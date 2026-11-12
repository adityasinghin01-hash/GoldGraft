"""Offline HTTP checks of integrated evidence and bounded live-run admission."""

import json
import re
from threading import Event
from time import monotonic

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.api import Graft
from goldgraft_contracts.registry import validate
from goldgraft_fakes import data

from integration.agents_app import create_app

LABEL = "real-models-scripted-runner"


@pytest.fixture
def runs(tmp_path, monkeypatch):
    # Keep the base backend's default ledgers out of the working repository too.
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "runs"
    directory = root / "sample-1"
    directory.mkdir(parents=True)
    tasks = [
        {"task": task, "role": role, "passed": True, "model": "haiku", "cost_micro_usd": 10}
        for task, role in [
            ("gardener:propose_plan", "Gardener"),
            ("survey", "Surveyor"),
            ("sentinel-audit", "Sentinel"),
        ]
    ]
    result = {
        "shop": "legacy-php-shop",
        "status": "completed",
        "tasks": tasks,
        "spent_micro_usd": 30,
        "cap_micro_usd": 600000,
        "finished_at": "2026-11-12T10:00:00Z",
    }
    (directory / "RESULT.json").write_text(json.dumps(result))
    outputs = {
        "survey": [{"schema": "RootMap/1", "payload": data.example("RootMap")}],
        "sentinel-audit": [{"schema": "Alert/1", "payload": data.example("Alert")}],
        "adversary-guards": [{"schema": "ScenarioSet/1", "payload": data.example("ScenarioSet")}],
        "librarian-recipe": [{"schema": "Recipe/1", "payload": data.example("Recipe")}],
        "orchard-aggregate": [
            {"schema": "DashboardSpec/1", "payload": data.example("DashboardSpec")}
        ],
    }
    for values in outputs.values():
        for item in values:
            validate(item["schema"], item["payload"])
    (directory / "OUTPUTS.json").write_text(json.dumps(outputs))
    return root


def assert_problem(response, status, integrated=True):
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == status
    if integrated:
        assert response.headers["X-GoldGraft-Evidence-Class"] == LABEL


def shop(client, repo="https://example.test/legacy-php-shop", key="shop"):
    response = client.post(
        "/shops", json={"name": "Test", "repo": repo}, headers={"Idempotency-Key": key}
    )
    assert response.status_code == 200
    return response.json()["shop_id"]


def start(client, shop_id, key="start", body=None):
    return client.post(f"/shops/{shop_id}/graft", json=body or {}, headers={"Idempotency-Key": key})


def test_graft_rootmap_and_sse_reconnect(runs):
    with TestClient(create_app(runs_dir=runs)) as client:
        response = client.get("/grafts/sample-1", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert response.headers["X-GoldGraft-Evidence-Class"] == LABEL
        assert response.headers["access-control-allow-origin"] == "*"
        graft = Graft.model_validate(response.json())
        assert graft.stage == "SURVEYED"
        assert graft.card.cost_usd == 0.00003
        assert graft.card.scenarios_total == 0
        rootmap = client.get("/grafts/sample-1/rootmap")
        assert rootmap.headers["X-GoldGraft-Evidence-Class"] == LABEL
        validate("RootMap/1", rootmap.json())
        feed = client.get("/grafts/sample-1/events")
        assert feed.headers["content-type"].startswith("text/event-stream")
        assert feed.headers["X-GoldGraft-Evidence-Class"] == LABEL
        entries = []
        for block in feed.text.strip().split("\n\n"):
            identity, event, payload = block.splitlines()
            entry = json.loads(payload.removeprefix("data: "))
            assert identity == f"id: {entry['seq']}"
            assert event == "event: ledger"
            validate("LedgerEntry/1", entry)
            validate(entry["schema"], entry["payload"])
            entries.append(entry)
        assert {entry["schema"] for entry in entries} == {
            "StageChange/1",
            "BudgetRecord/1",
            "Alert/1",
        }
        assert entries[-1]["entry_hash"] == graft.ledger_root
        browser = client.get("/grafts/sample-1/events", headers={"Accept": "text/event-stream"})
        assert browser.text.endswith("event: end\ndata: {}\n\n")  # finished run: stop reconnecting
        assert "event: end" not in feed.text  # plain GET keeps ledger frames only
        replay = client.get("/grafts/sample-1/events", headers={"Last-Event-ID": "2"})
        assert [
            json.loads(line[6:])["seq"]
            for line in replay.text.splitlines()
            if line.startswith("data: ")
        ] == [e["seq"] for e in entries if e["seq"] > 2]
        assert (
            client.get(
                "/grafts/sample-1/events", headers={"Last-Event-ID": str(entries[-1]["seq"])}
            ).text
            == ""
        )
        assert_problem(client.get("/grafts/sample-1/events", headers={"Last-Event-ID": "-1"}), 400)
    # Reading evidence must not add view databases or blobs alongside it.
    assert {p.name for p in (runs / "sample-1").iterdir()} == {"RESULT.json", "OUTPUTS.json"}


def test_real_agent_outputs_reach_their_screens(runs):
    scenarios = data.example("ScenarioSet")["scenarios"]
    with TestClient(create_app(runs_dir=runs)) as client:
        # Payment tests: the Adversary's real scenarios, never an invented verdict.
        listed = client.get("/grafts/sample-1/scenarios").json()
        assert [row["scenario"]["id"] for row in listed["scenarios"]] == [
            s["id"] for s in scenarios
        ]
        assert all(row["verdict"] is None for row in listed["scenarios"])
        # Agents tab: every step with its model, cost and an honest input label.
        agents = client.get("/grafts/sample-1/agents").json()
        assert [a["role"] for a in agents["agents"]] == ["Gardener", "Surveyor", "Sentinel"]
        by_role = {a["role"]: a for a in agents["agents"]}
        assert by_role["Surveyor"]["input"] == "real"
        assert by_role["Sentinel"]["input"] == "mixed"
        assert by_role["Surveyor"]["outputs"][0]["summary"].startswith("Found ")
        assert by_role["Surveyor"]["model"] == "claude-haiku-5-5"
        # Go-live never shows the sample's data for a real run.
        assert_problem(client.get("/heal/sample-1"), 404)
        feed = client.get("/heal/sample-1", headers={"Accept": "text/event-stream"})
        assert feed.text == "event: end\ndata: {}\n\n"
        assert client.get("/heal/demo-1").status_code == 200
        # Security: Sentinel's real alerts for a real run; the stand-in says it is a sample.
        gauntlet = client.get("/security/gauntlet/sample-1").json()
        assert gauntlet["attempts"] == [] and gauntlet["alerts"] == [data.example("Alert")]
        stand_in = client.get("/security/gauntlet/run-1")
        assert "SYNTHETIC" in stand_in.json()["label"]
        assert int(stand_in.headers["content-length"]) == len(stand_in.content)
        # Recipes and PayPal team come from the Librarian's and Orchard Analyst's real outputs.
        assert client.get("/recipes").json()["recipes"] == [data.example("Recipe")]
        orchard = client.get("/orchard").json()
        assert [s["shop_id"] for s in orchard["shops"]] == ["legacy-php-shop"]
        assert orchard["dashboards"] == [data.example("DashboardSpec")]
        assert orchard["label"].startswith("Real Orchard Analyst output")
        asked = client.post("/orchard/ask", json={"question": "Which shops?"})
        assert_problem(asked, 501)


@pytest.mark.parametrize("suffix", ["cmel", "proof"])
def test_independent_proof_is_not_claimed(runs, suffix):
    with TestClient(create_app(runs_dir=runs)) as client:
        response = client.get(f"/grafts/sample-1/{suffix}")
        assert_problem(response, 404)
        assert "independent proof has not run" in response.json()["detail"]


def test_changes_and_unknown_backend_fallthrough(runs):
    with TestClient(create_app(runs_dir=runs)) as client:
        response = client.get("/grafts/unknown")
        assert_problem(response, 404, integrated=False)
        assert response.headers["X-GoldGraft-Evidence-Class"] == "scripted"
        assert_problem(client.get("/grafts/sample-1/changes"), 404)
        changes = {
            "files": [{"path": "checkout.php", "before": "old", "after": "new", "author": "model"}],
            "extra": "preserved",
        }
        raw = json.dumps(changes, indent=2)
        (runs / "sample-1" / "CHANGES.json").write_text(raw)
        response = client.get("/grafts/sample-1/changes")
        assert response.status_code == 200
        assert response.json() == changes  # no plan to check against: no planted-bug result
        assert response.headers["X-GoldGraft-Evidence-Class"] == LABEL


def test_runs_newest_first_and_distinct_role_counts(runs):
    second = runs / "sample-2"
    second.mkdir()
    result = json.loads((runs / "sample-1" / "RESULT.json").read_text())
    result["finished_at"] = "2026-11-12T11:00:00Z"
    result["tasks"].append(dict(result["tasks"][0], task="gardener:another"))
    (second / "RESULT.json").write_text(json.dumps(result))
    with TestClient(create_app(runs_dir=runs)) as client:
        response = client.get("/runs")
        assert response.headers["X-GoldGraft-Evidence-Class"] == LABEL
        assert [row["run_id"] for row in response.json()] == ["sample-2", "sample-1"]
        assert response.json()[0] == {
            "run_id": "sample-2",
            "shop": "legacy-php-shop",
            "status": "completed",
            "roles_passed": 3,
            "roles_participated": 3,
            "spent_usd": 0.00003,
            "finished_at": "2026-11-12T11:00:00Z",
        }


@pytest.mark.parametrize(
    "enabled,repo",
    [
        (False, "https://example.test/legacy-php-shop"),
        (True, "https://example.test/unqualified"),
    ],
)
def test_disabled_or_unqualified_start_passes_through(runs, enabled, repo):
    def forbidden(*args):
        pytest.fail("Runner must not be invoked")

    with TestClient(create_app(runs_dir=runs, live_enabled=enabled, runner=forbidden)) as client:
        response = start(client, shop(client, repo))
        assert response.status_code == 200
        assert Graft.model_validate(response.json()).graft_id.startswith("graft-")
        assert response.headers["X-GoldGraft-Evidence-Class"] == "scripted"


def test_unnamed_shop_is_named_after_its_repo(runs):
    with TestClient(create_app(runs_dir=runs)) as client:
        made = client.post(
            "/shops",
            json={"repo": "https://github.com/goldgraft/eval-nvp.git/"},
            headers={"Idempotency-Key": "unnamed"},
        )
        assert made.status_code == 200
        assert made.json()["name"] == "eval-nvp"
        assert int(made.headers["content-length"]) == len(made.content)
        named = client.post(
            "/shops",
            json={"name": "Corner Shop", "repo": "https://github.com/goldgraft/eval-nvp"},
            headers={"Idempotency-Key": "named"},
        )
        assert named.json()["name"] == "Corner Shop"


@pytest.mark.parametrize("admitted", ["legacy-php-shop", "eval-nvp"])
def test_live_start_busy_replay_and_starting_views(runs, admitted):
    entered, release, exited = Event(), Event(), Event()
    calls = []

    def runner(shop_name, run_id):
        calls.append((shop_name, run_id))
        entered.set()
        try:
            assert release.wait(10), "test did not release runner"
        finally:
            exited.set()

    try:
        with TestClient(create_app(runs_dir=runs, live_enabled=True, runner=runner)) as client:
            sid = shop(client, f"https://example.test/{admitted}")
            response = start(client, sid)
            assert response.status_code == 200
            graft = Graft.model_validate(response.json())
            assert re.fullmatch(rf"web-{admitted}-\d{{8}}-\d{{6}}", graft.graft_id)
            assert len(graft.graft_id) <= 40
            assert graft.stage == "CREATED" and graft.shop_id == sid
            assert graft.card.cost_usd == graft.card.scenarios_total == 0
            assert "real" in graft.card.notes["_label"].lower()
            assert response.headers["X-GoldGraft-Evidence-Class"] == LABEL
            assert entered.wait(2)
            assert calls == [(admitted, graft.graft_id)]
            assert start(client, sid).json() == response.json()
            assert_problem(start(client, sid, "second"), 409)
            assert_problem(start(client, sid, body={"note": "changed"}), 409)
            current = client.get(f"/grafts/{graft.graft_id}")
            assert current.json()["stage"] == "CREATED"
            assert current.json()["shop_id"] == sid
            assert client.get(f"/grafts/{graft.graft_id}/events").status_code == 200
            assert_problem(client.get(f"/grafts/{graft.graft_id}/rootmap"), 404)
            listed = {row["run_id"]: row for row in client.get("/runs").json()}
            assert listed[graft.graft_id]["status"] == "starting"
    finally:
        release.set()
        assert exited.wait(2)


def test_live_process_cap_and_request_validation(runs):
    with TestClient(create_app(runs_dir=runs, live_enabled=True, max_live_runs=0)) as client:
        sid = shop(client)
        path = f"/shops/{sid}/graft"
        assert_problem(client.post(path, json={}), 400)
        assert_problem(
            client.post(path, json={"invalid": True}, headers={"Idempotency-Key": "invalid"}), 422
        )
        assert_problem(start(client, sid), 429)


def test_failed_runner_releases_busy_slot_and_retains_process_limit(runs, caplog):
    calls = []

    def runner(shop_name, run_id):
        calls.append((shop_name, run_id))
        raise RuntimeError("private-provider-detail")

    with TestClient(
        create_app(runs_dir=runs, live_enabled=True, runner=runner, max_live_runs=1)
    ) as client:
        sid = shop(client)
        first = start(client, sid)
        run_id = first.json()["graft_id"]
        deadline = monotonic() + 2
        while True:
            row = next(r for r in client.get("/runs").json() if r["run_id"] == run_id)
            if row["status"] == "failed":
                break
            assert monotonic() < deadline, "Runner did not finish"
        assert row["finished_at"] is not None
        assert_problem(start(client, sid, "after-failure"), 429)
        assert calls == [("legacy-php-shop", run_id)]
        response = client.get(f"/grafts/{run_id}")
        assert "failed" in response.json()["card"]["notes"]["runner"]
        assert "private-provider-detail" not in response.text + caplog.text


def test_default_runner_command_logs_and_custom_directory(runs, monkeypatch):
    from integration import agents_app

    driver_runs = runs.parent / "driver-runs"
    monkeypatch.setattr(agents_app, "DEFAULT_RUNS_DIR", driver_runs)
    calls = []

    def fake_process(command, **kwargs):
        calls.append(command)
        assert command == [
            str(agents_app.GATEWAY_PYTHON),
            "-m",
            "scripts.live_integrated_run",
            "--live",
            "--run-id",
            "web-test",
            "--shop",
            "eval-nvp",
            "--max-usd",
            "0.60",
        ]
        assert kwargs["cwd"] == agents_app.ROOT
        assert kwargs["env"]["PATH"].startswith("/Library/Developer/CommandLineTools/usr/bin:")
        assert kwargs["stderr"] == agents_app.subprocess.STDOUT
        assert kwargs["check"] is True
        kwargs["stdout"].write(b"fake process output\n")
        output = driver_runs / "web-test"
        output.mkdir(parents=True)
        (output / "RESULT.json").write_text('{"status":"completed"}')

    monkeypatch.setattr(agents_app.subprocess, "run", fake_process)
    agents_app._default_runner(runs)("eval-nvp", "web-test")
    assert len(calls) == 1
    assert (runs.parent / "web-runs/web-test.log").read_text() == "fake process output\n"
    assert (runs / "web-test/RESULT.json").read_text() == '{"status":"completed"}'
