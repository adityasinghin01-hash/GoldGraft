"""All frontend modes use validated wire payloads and explicit synthetic provenance."""

import hashlib
import json
from pathlib import Path

import pytest
from goldgraft_contracts.registry import validate

ROOT = Path(__file__).resolve().parents[2]
MODES = [
    "ready",
    "controller_wait",
    "missing_source",
    "start_response_lost",
    "claimed_no_operation",
    "cancel_before_accept",
    "cancel_pending",
    "event_gap",
    "proof_missing",
    "apply_split_controllers",
    "deploy_unknown_no_id",
    "persistent_config_mismatch",
    "exit_executor_missing",
    "cleanup_pending",
    "synthetic_complete",
]


@pytest.mark.parametrize("mode", MODES)
def test_frontend_mode_payloads_conform_and_stay_scripted(tmp_path, mode):
    from goldgraft_fakes.case_views import OfflineCaseViews

    views = OfflineCaseViews(tmp_path / "views.sqlite")
    records = views.load_mode(mode, actor="synthetic-reviewer")
    assert "CaseView/1" in records
    for schema, value in records.items():
        validate(schema, value.model_dump(mode="json"))
    assert records["CaseView/1"].evidence_class == "scripted"
    assert views.label.startswith("Mock mode:")
    assert views.load_mode(mode, actor="synthetic-reviewer") == records
    with pytest.raises(ValueError):
        views.load_mode(mode, actor="unbound-actor")


def test_truthful_progress_cancel_unknown_exit_and_public_projection(tmp_path):
    from goldgraft_fakes.case_views import OfflineCaseViews

    views = OfflineCaseViews(tmp_path / "views.sqlite")
    def get(mode):
        return views.load_mode(mode, actor="synthetic-reviewer")
    assert get("claimed_no_operation")["CaseView/1"].action.status.state == "provisioning"
    cancelled = get("cancel_before_accept")["CaseView/1"].action
    assert cancelled.acceptance_ref is None and cancelled.status.work_id is None
    assert get("cancel_pending")["WorkCancellation/1"].state == "termination_pending"
    unknown = get("deploy_unknown_no_id")["DeploymentObservation/1"]
    assert unknown.provider_deploy_id is None and unknown.outcome == "unknown"
    assert get("cleanup_pending")["ExitManifest/1"].outcome == "pending"
    assert get("synthetic_complete")["ExitManifest/1"].outcome == "complete"
    assert get("synthetic_complete")["PublicProofView/1"].evidence_class == "scripted"
    for mode in ["real", "same_origin", "live_provider"]:
        with pytest.raises(ValueError):
            views.load_mode(mode, actor="synthetic-reviewer")


def test_frontend_catalog_has_every_named_mode_with_exact_file_hashes():
    index = json.loads((ROOT / "fixtures/plan5/index.json").read_text())
    assert {m["mode"] for m in index["frontend_modes"]} == set(MODES)
    for mode in index["frontend_modes"]:
        assert mode["evidence_class"] == "scripted"
        for row in mode["records"]:
            path = ROOT / row["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
