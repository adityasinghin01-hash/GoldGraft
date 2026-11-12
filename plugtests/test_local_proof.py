"""Offline binding/replay and HTTP checks, using explicitly synthetic test captures."""

import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from integration.agents_app import create_app
from integration.local_proof import LocalProof
from integration.local_shop import ROOT, SCENARIOS

REFERENCE = ROOT / "fixtures/proof/legacy-php-shop"


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / "runs" / "sample-1"
    stored = directory / "local-proof"
    stored.mkdir(parents=True)
    (directory / "RESULT.json").write_text(
        json.dumps(
            {
                "shop": "legacy-php-shop",
                "status": "completed",
                "tasks": [],
            }
        )
    )
    (directory / "CHANGES.json").write_text('{"files": []}')
    plan = json.loads((REFERENCE / "target_plan.json").read_bytes())
    (directory / "OUTPUTS.json").write_text(
        json.dumps(
            {
                "architect": [{"schema": "TargetPlan/1", "payload": plan}],
            }
        )
    )

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    report = {
        "run_id": "sample-1",
        "evidence_class": "local_php_execution_simulated_paypal",
        "real_payment_qualified": False,
        "isolated_execution_qualified": False,
        "merchant_delivery_qualified": False,
        "changes_sha256": sha(directory / "CHANGES.json"),
        "outputs_sha256": sha(directory / "OUTPUTS.json"),
        "normative_contract_sha256": sha(REFERENCE / "contract.json"),
        "capture_sha256": {},
    }
    for scenario in SCENARIOS:
        for variant in ("OLD", "OLD_TWIN", "NEW"):
            name = f"{scenario}.{variant}.json"
            capture = json.loads((REFERENCE / "raw" / name).read_bytes())
            capture.update(graft_id="sample-1", run_id="sample-1-local-php")
            (stored / name).write_text(json.dumps(capture))
            report["capture_sha256"][name] = sha(stored / name)
    (stored / "REPORT.json").write_text(json.dumps(report))
    return directory


def test_local_proof_replays_captures_instead_of_trusting_reported_grades(evidence):
    path = evidence / "local-proof/REPORT.json"
    report = json.loads(path.read_text())
    report["scenarios"] = [{"scenario": "PENDING", "actual_model_plan": {"grade": "PASS"}}]
    path.write_text(json.dumps(report))
    replay = LocalProof(evidence)
    rows = {row.scenario.id: row.verdict for row in replay.scenarios().scenarios}
    assert rows["HAPPY"].grade == "PASS"
    assert rows["PENDING"].grade == "PROBLEM"
    events = replay.cmel("HAPPY")
    assert events.graft_id == "sample-1"
    assert {event.variant for event in events.new} == {"NEW"}


@pytest.mark.parametrize("name", ["CHANGES.json", "OUTPUTS.json", "local-proof/HAPPY.NEW.json"])
def test_local_proof_refuses_drifted_candidate_plan_or_capture(evidence, name):
    with (evidence / name).open("a") as stream:
        stream.write(" ")
    with pytest.raises(ValueError, match="drift"):
        LocalProof(evidence)


def test_http_exposes_local_verdicts_and_events_without_a_certificate_or_strength(evidence):
    with TestClient(create_app(runs_dir=evidence.parent)) as client:
        scenarios = client.get("/grafts/sample-1/scenarios")
        assert scenarios.status_code == 200
        assert scenarios.headers["X-GoldGraft-Evidence-Class"] == "local-php-simulated-paypal"
        rows = {row["scenario"]["id"]: row["verdict"] for row in scenarios.json()["scenarios"]}
        assert rows["PENDING"]["grade"] == "PROBLEM"
        assert len(rows) == 9
        mapped = client.get("/grafts/sample-1/cmel?scenario=HAPPY")
        assert mapped.status_code == 200
        assert mapped.json()["new"][0]["graft_id"] == "sample-1"
        card = client.get("/grafts/sample-1").json()["card"]
        assert card["scenarios_total"] == 9
        assert 0 < card["scenarios_pass"] < 9
        assert card["problems"] > 0
        assert "simulated PayPal" in card["notes"]["scenarios_pass"]
        assert client.get("/grafts/sample-1/proof").status_code == 404
        with (evidence / "CHANGES.json").open("a") as stream:
            stream.write(" ")
        assert client.get("/grafts/sample-1/scenarios").status_code == 503
