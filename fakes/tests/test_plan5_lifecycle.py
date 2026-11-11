"""Lifecycle counterpart stores observations/identities; it never decides delivery."""

from datetime import UTC, datetime

import pytest
from goldgraft_contracts.registry import validate
from goldgraft_fakes._fixtures import example

NOW = datetime(2026, 11, 10, 12, tzinfo=UTC)


def lifecycle(tmp_path):
    from goldgraft_fakes.lifecycle_control import OfflineLifecycleControl

    c = OfflineLifecycleControl(tmp_path / "lifecycle.sqlite", clock=lambda: NOW)
    c.fixture_snapshot(
        "fake:delivery", validate("DeliverySnapshot/1", example("DeliverySnapshot/1"))
    )
    return c


def test_lifecycle_same_request_and_slot_once_after_restart(tmp_path):
    from goldgraft_fakes.lifecycle_control import OfflineLifecycleControl

    c = lifecycle(tmp_path)
    decision = validate("DeliveryDecision/1", example("DeliveryDecision/1"))
    receipt = c.submit(decision, "request-1")
    assert c.submit(decision, "request-1") == receipt
    fresh = OfflineLifecycleControl(tmp_path / "lifecycle.sqlite", clock=lambda: NOW)
    assert fresh.submit(decision, "request-1") == receipt
    assert fresh.dispatch_count("request-1") == 1
    assert fresh.status("request-1").state == "unknown"
    with pytest.raises(ValueError, match="CONFLICT"):
        fresh.submit(decision, "request-2")
    with pytest.raises(ValueError, match="CONFLICT"):
        fresh.submit(decision.model_copy(update={"reason_code": "changed"}), "request-1")
    assert fresh.snapshot("fake:delivery") == c.snapshot("fake:delivery")


def test_lifecycle_missing_approval_cancel_and_stale_version_hold(tmp_path):
    c = lifecycle(tmp_path)
    value = example("DeliveryDecision/1")
    value.update(operation="deploy_exact", slot_id="slot-1")
    d = validate("DeliveryDecision/1", value)
    with pytest.raises(ValueError, match="MISSING_EVIDENCE"):
        c.submit(d, "deploy-1")
    c.fixture_slot("fake:delivery", d, authority_current=True, approvals_current=True)
    receipt = c.submit(d, "deploy-1")
    assert receipt.request_id == "deploy-1" and c.dispatch_count("deploy-1") == 1
    snapshot = c.snapshot("fake:delivery").model_copy(update={"cancellation_ref": "fake:stop"})
    c.fixture_snapshot("fake:delivery", snapshot)
    with pytest.raises(ValueError, match="CANCELLED"):
        c.submit(d.model_copy(update={"slot_id": "slot-2"}), "deploy-2")
    assert c.status("deploy-1").state == "unknown"
    assert c.dispatch_count("deploy-2") == 0


def test_lifecycle_observations_and_fake_authenticity_remain_scoped(tmp_path):
    c = lifecycle(tmp_path)
    ref = c.fixture_record("fake:delivery", "ExitManifest/1", example("ExitManifest/1"))
    descriptor, payload = c.resolve_fixture(ref, run_ref="fake:delivery")
    assert descriptor.evidence_class == "scripted"
    assert descriptor.producer_identity_ref.startswith("fake:")
    with pytest.raises(ValueError):
        c.resolve_fixture(ref, run_ref="wrong-case")
    forged = example("ArtifactBuild/1")
    forged["authenticity_ref"] = "real:signature"
    with pytest.raises(ValueError):
        c.fixture_record("fake:delivery", "ArtifactBuild/1", forged)
