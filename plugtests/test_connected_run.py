"""The connected local run binds Gupta's control, the executed recordings, Singhal's
judge and the SI01 records. Synthetic captures stand in for PHP execution here;
the composition, seals and holds are the real code."""

import hashlib
import json

import pytest

from integration.connected_run import LocalHost, connect_run
from integration.local_shop import ROOT, SCENARIOS

REFERENCE = ROOT / "fixtures/proof/legacy-php-shop"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def agent_run(tmp_path):
    directory = tmp_path / "agents"
    directory.mkdir()
    (directory / "RESULT.json").write_text(
        json.dumps({"shop": "legacy-php-shop", "status": "completed", "tasks": []})
    )
    (directory / "CHANGES.json").write_text('{"files": []}')
    plan = json.loads((REFERENCE / "target_plan.json").read_bytes())
    (directory / "OUTPUTS.json").write_text(
        json.dumps({"architect": [{"schema": "TargetPlan/1", "payload": plan}]})
    )
    return directory


def fixture_execute(tamper=None):
    """Writes reference recordings under the run directory's own id, like the
    real executor does, then reports their digests."""

    def execute(run_dir, output, *, php="php"):
        output.mkdir(parents=True)
        report = {
            "run_id": run_dir.name,
            "evidence_class": "local_php_execution_simulated_paypal",
            "real_payment_qualified": False,
            "isolated_execution_qualified": False,
            "merchant_delivery_qualified": False,
            "changes_sha256": sha(run_dir / "CHANGES.json"),
            "outputs_sha256": sha(run_dir / "OUTPUTS.json"),
            "normative_contract_sha256": sha(REFERENCE / "contract.json"),
            "capture_sha256": {},
            "candidate_mutations": [],
            "unguarded_critical_rule_ids": ["R02", "R17"],
        }
        for scenario in SCENARIOS:
            for variant in ("OLD", "OLD_TWIN", "NEW"):
                name = f"{scenario}.{variant}.json"
                capture = json.loads((REFERENCE / "raw" / name).read_bytes())
                capture.update(graft_id=run_dir.name, run_id=run_dir.name + "-local-php")
                (output / name).write_text(json.dumps(capture))
                report["capture_sha256"][name] = sha(output / name)
        (output / "REPORT.json").write_text(json.dumps(report))
        if tamper:
            tamper(output)
        return report

    return execute


def test_connected_run_binds_control_recordings_judge_and_records(agent_run, tmp_path):
    summary = connect_run(agent_run, tmp_path / "state", execute=fixture_execute())
    control = summary["gupta_control"]
    assert control["status"] == "operation_started" and control["generation"] == 1
    # The evidence run id is derived from the work id Gupta's control issued.
    assert summary["evidence_run"] == control["work_id"]
    states = {c: s for s, ids in summary["proof_result"]["by_state"].items() for c in ids}
    for scenario in SCENARIOS:
        assert states[f"baseline:{scenario}"] == "verified"
        assert states[f"candidate:{scenario}"] == "verified"
    assert states["scenario:HAPPY"] == "verified"
    assert states["scenario:PENDING"] != "verified"  # Reference NEW still has R01/R07.
    for gate in (
        "domain_rule:R02",
        "domain_rule:R17",
        "payment:shop-checkout-paypal",
        "isolation:runner",
    ):
        assert states[gate] == "missing"
    assert summary["proof_result"]["outcome"] == "hold"
    assert summary["promotion"]["action"] == "HOLD"
    assert summary["certificate"] == {"issued": False, "held_at": "EVIDENCE_HOLD"}
    assert summary["lifecycle_review"]["disposition"] == "HOLD"
    for name in ("ProofPlan", "ProofResult", "PromotionDecision", "PublicProofView"):
        assert (tmp_path / "state" / f"{name}.json").exists()


def test_recording_changed_after_execution_stops_the_run(agent_run, tmp_path):
    def tamper(output):
        path = output / "HAPPY.NEW.json"
        capture = json.loads(path.read_bytes())
        capture["exchanges"] = capture["exchanges"][:-1]
        path.write_text(json.dumps(capture))

    with pytest.raises(ValueError):
        connect_run(agent_run, tmp_path / "state", execute=fixture_execute(tamper))


def test_reused_state_folder_is_refused(agent_run, tmp_path):
    connect_run(agent_run, tmp_path / "state", execute=fixture_execute())
    with pytest.raises(ValueError, match="new folder"):
        connect_run(agent_run, tmp_path / "state", execute=fixture_execute())


def test_host_seal_rejects_changed_descriptor_or_wrong_role():
    from datetime import UTC, datetime

    from goldgraft_contracts.agent_runtime import SubjectManifest

    from integration.proof_evidence import StoredArtifact

    host = LocalHost("tenant", datetime(2026, 11, 12, tzinfo=UTC))
    subject = SubjectManifest(
        source_snapshot_refs=["local:x"],
        source_tree_digest="a" * 64,
        oci_manifest_digest=None,
        config_digest=None,
        runtime_profile_digest="a" * 64,
        scope_digest="a" * 64,
    )
    binding = dict(case_id="c", run_id="r", generation=1, work_package_digest="b" * 64)
    host.put(
        "local:s",
        "SubjectManifest/1",
        subject,
        role="collector",
        trust="collector_observed",
        evidence_class="component_offline",
        binding=binding,
        subject="c" * 64,
    )

    class Ctx:
        tenant_id = "tenant"

    record = host.resolve("local:s")
    assert host.authenticate(record, Ctx, "collector") is True
    assert host.authenticate(record, Ctx, "judge") is False
    forged = StoredArtifact(
        record.descriptor.model_copy(update={"run_id": "other"}), record.payload
    )
    assert host.authenticate(forged, Ctx, "collector") is False
    Ctx.tenant_id = "other-tenant"
    assert host.authenticate(record, Ctx, "collector") is False


def test_app_serves_connected_run_and_fails_closed_on_edits(agent_run, tmp_path):
    from fastapi.testclient import TestClient

    from integration.agents_app import create_app

    runs = tmp_path / "runs"
    run = runs / "sample-1"
    run.mkdir(parents=True)
    (run / "RESULT.json").write_bytes((agent_run / "RESULT.json").read_bytes())
    connect_run(agent_run, run / "connected-run", execute=fixture_execute())
    client = TestClient(create_app(runs_dir=runs))
    body = client.get("/grafts/sample-1/connected").json()
    assert body["proof_result"]["outcome"] == "hold"
    checks = {c["check_id"]: c for c in body["checks"]}
    assert checks["candidate:HAPPY"]["state"] == "verified"
    assert checks["isolation:runner"] == {
        "check_id": "isolation:runner",
        "kind": "isolation",
        "critical": True,
        "evidence_class": "isolation_qualified",
        "state": "missing",
        "reason": "MISSING",
    }
    assert client.get("/grafts/other/connected").status_code == 404
    result = run / "connected-run/ProofResult.json"
    edited = json.loads(result.read_bytes())
    edited["outcome"] = "ready"
    result.write_text(json.dumps(edited))
    assert client.get("/grafts/sample-1/connected").status_code == 503
