"""Published backend → runner → actual proof → durable ledger → published read routes."""

import json

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.api_routes import route
from goldgraft_contracts.registry import validate

from integration.app import create_app
from integration.service import FixtureRun


def test_pushed_scope_runs_through_backend_and_reopens_without_execution(tmp_path):
    service = FixtureRun(tmp_path)
    client = TestClient(create_app(service=service))
    path = f"/shops/{service.shop_id}/graft"
    headers = {"Idempotency-Key": "pushed-scope-1"}
    response = client.post(path, json={}, headers=headers)
    assert response.status_code == 200, response.text
    graft = route("start_graft").response.model_validate(response.json())
    assert graft.graft_id == service.graft_id
    assert graft.stage == "PARTIAL"  # Published negatives retain their actual outcomes.
    assert (graft.card.scenarios_total, graft.card.scenarios_pass, graft.card.problems) == (9, 6, 2)
    assert graft.card.pieces_upgraded == 0
    assert "SYNTHETIC" in graft.card.notes["_label"]
    assert service.ledger.verify_chain(service.graft_id).ok

    scenarios = client.get(f"/grafts/{graft.graft_id}/scenarios")
    rows = route("get_scenarios").response.model_validate(scenarios.json()).scenarios
    assert {r.scenario.id: r.verdict.grade for r in rows} == {
        "HAPPY": "PASS",
        "DECLINE": "PASS",
        "DOUBLE": "PASS",
        "REFUND": "PASS",
        "REFUND_TWICE": "PASS_FIXED",
        "NOTIFY_FORGED": "PASS",
        "NOTIFY_DUP": "UNVERIFIED",
        "PENDING": "PROBLEM",
        "PARITY_EXTRA": "PROBLEM",
    }
    for row in rows:
        response = client.get(
            f"/grafts/{graft.graft_id}/cmel", params={"scenario": row.scenario.id}
        )
        cmel = route("get_cmel").response.model_validate(response.json())
        assert cmel.graft_id == graft.graft_id and cmel.old and cmel.old_twin and cmel.new
    proof = client.get(f"/grafts/{graft.graft_id}/proof")
    assert route("get_proof").response.model_validate(proof.json()).proof_strength.total == 12
    feed = client.get(f"/grafts/{graft.graft_id}/events")
    entries = [
        json.loads(s.removeprefix("data: "))
        for s in feed.text.splitlines()
        if s.startswith("data: ")
    ]
    assert entries and entries[-1]["entry_hash"] == graft.ledger_root
    assert any(e["schema"] == "CMEL/1" for e in entries)
    assert any(e["schema"] == "Verdict/1" for e in entries)
    for entry in entries:
        validate("LedgerEntry/1", entry)
    replay = client.get(
        f"/grafts/{graft.graft_id}/events", headers={"Last-Event-ID": str(entries[-1]["seq"])}
    )
    assert replay.text == ""

    before = service.ledger.root_hash(service.graft_id)
    reopened = FixtureRun(tmp_path)

    def must_not_run(_):
        raise AssertionError("completed fixture run dispatched after restart")

    reopened.runner.run_job = must_not_run
    restarted = TestClient(create_app(service=reopened))
    assert restarted.post(path, json={}, headers=headers).json() == graft.model_dump(mode="json")
    assert restarted.get(f"/grafts/{graft.graft_id}").json() == graft.model_dump(mode="json")
    assert reopened.ledger.root_hash(service.graft_id) == before
    assert restarted.post(path, json={"note": "different"}, headers=headers).status_code == 409
    assert reopened.ledger.root_hash(service.graft_id) == before


def test_failed_runner_leaves_no_success_or_partial_ledger(tmp_path):
    service = FixtureRun(tmp_path)

    def fail(_):
        raise ValueError("fixture failed")

    service.runner.run_job = fail
    with pytest.raises(ValueError):
        service.start("failure", {})
    assert service.events() == []


def test_missing_fixture_run_is_a_problem_response(tmp_path):
    service = FixtureRun(tmp_path)
    client = TestClient(create_app(service=service))
    for suffix in ("", "/scenarios", "/proof", "/cmel"):
        response = client.get(f"/grafts/{service.graft_id}{suffix}")
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/problem+json")


def test_concurrent_starts_commit_one_fixture_run(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    first = FixtureRun(tmp_path)
    second = FixtureRun(tmp_path)
    calls = []
    original = first.runner.run_job

    def counted(spec):
        calls.append(spec.job_id)
        return original(spec)

    first.runner.run_job = counted
    second.runner.run_job = counted
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda service: service.start("same", {}), (first, second)))
    assert len(calls) == 1
    assert results[0] == results[1]
    assert first.ledger.verify_chain(first.graft_id).ok


def test_reopened_views_use_archived_inputs_and_reject_corruption(tmp_path):
    from sqlalchemy import update

    service = FixtureRun(tmp_path)
    service.start("archived", {})
    expected = service.proof()
    reopened = FixtureRun(tmp_path)
    reopened._read = lambda _: (_ for _ in ()).throw(AssertionError("re-read fixture source"))
    assert reopened.proof() == expected
    rows = reopened.events()
    with reopened.ledger.engine.begin() as connection:
        connection.execute(
            update(reopened.ledger.entries)
            .where(
                reopened.ledger.entries.c.graft_id == reopened.graft_id,
                reopened.ledger.entries.c.seq == rows[-1].seq,
            )
            .values(body="{}")
        )
    with pytest.raises(ValueError, match="corrupted"):
        reopened.graft()


def test_mutation_input_blob_tampering_is_rejected(tmp_path):
    service = FixtureRun(tmp_path)
    service.start("blob-integrity", {})
    ref = service._payloads("StageChange/1")[0].evidence_refs[0]
    service.store.path_for(ref).write_bytes(b'{"runs": []}')
    with pytest.raises(ValueError, match="blob integrity"):
        service.proof()
