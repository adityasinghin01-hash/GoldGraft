"""Tests for Advanced Lifecycle Mechanisms: GU04 Approvals & GU05 Recovery/Exit."""

import pytest
from goldgraft_foundation.ledger import Ledger

from pieces.backend.lifecycle import (
    ApprovalGate,
    AuthorizationEscalationError,
    ExitController,
    RecoveryManager,
    TargetLockError,
)


def test_target_lock_and_concurrency():
    ledger = Ledger()
    gate = ApprovalGate(ledger=ledger)

    gate.acquire_target_lock("graft-1", "github.com/merchant/repo:production")

    # Re-acquiring by same graft is allowed
    gate.acquire_target_lock("graft-1", "github.com/merchant/repo:production")

    # Different graft attempting to lock same target must be rejected
    with pytest.raises(TargetLockError, match="currently locked by graft"):
        gate.acquire_target_lock("graft-2", "github.com/merchant/repo:production")

    # Release lock allows second graft
    gate.release_target_lock("graft-1", "github.com/merchant/repo:production")
    gate.acquire_target_lock("graft-2", "github.com/merchant/repo:production")


def test_approval_gate_escalation_denial():
    ledger = Ledger()
    gate = ApprovalGate(ledger=ledger)

    slot = gate.grant_approval(
        graft_id="graft-read",
        target_resource="render.com/srv-123",
        permission_level="READ_ONLY",
        granted_by="MerchantOps",
        idempotency_key="idem-appr-1",
    )

    # Read-only verification passes
    gate.verify_action_permitted(slot.slot_id, "READ_ONLY")

    # Read-only token cannot escalate to mutating write or deploy action
    with pytest.raises(AuthorizationEscalationError, match="Escalation denied"):
        gate.verify_action_permitted(slot.slot_id, "DEPLOY_PRODUCTION")

    # Revoke approval
    gate.revoke_approval(slot.slot_id)
    with pytest.raises(AuthorizationEscalationError, match="invalid or has expired"):
        gate.verify_action_permitted(slot.slot_id, "READ_ONLY")


def test_safe_recovery_and_rollback():
    ledger = Ledger()
    recovery = RecoveryManager(ledger=ledger)

    receipt = recovery.execute_safe_rollback(
        graft_id="graft-live-1",
        current_stage="LIVE_100",
        reason="Heartbeat ping failure on host gateway",
        idempotency_key="idem-rb-1",
        processed_orders=["ORDER-101", "ORDER-102", "ORDER-103"],
    )

    assert receipt.graft_id == "graft-live-1"
    assert receipt.prior_stage == "LIVE_100"
    assert receipt.reverted_to == "CUTBACK"
    assert receipt.retained_orders_count == 3
    assert receipt.reason == "Heartbeat ping failure on host gateway"

    # Verify ledger entry
    entries = ledger.read("graft-live-1")
    assert len(entries) >= 1
    assert entries[-1].payload["to_stage"] == "CUTBACK"


def test_exit_controller_teardown_and_verification():
    ledger = Ledger()

    class FakeCustodyBroker:
        def __init__(self):
            self.revoked = []

        def revoke_token(self, token_key: str):
            self.revoked.append(token_key)

        def active_sessions_count(self, graft_id: str) -> int:
            return 0

    class FakeContainerRunner:
        def __init__(self):
            self.cleaned = []

        def cleanup_container(self, cid: str):
            self.cleaned.append(cid)

    broker = FakeCustodyBroker()
    runner = FakeContainerRunner()

    exit_ctrl = ExitController(
        ledger=ledger,
        custody_broker=broker,
        container_runner=runner,
    )

    receipt = exit_ctrl.execute_merchant_exit(
        graft_id="graft-exit-99",
        actor_name="MerchantCTO",
        idempotency_key="idem-exit-1",
        token_keys=["tok_doppler_sandbox_abc"],
        container_ids=["container_runner_456"],
    )

    assert receipt.graft_id == "graft-exit-99"
    assert receipt.status == "EXIT_COMPLETE"
    assert receipt.verified_clean is True
    assert receipt.revoked_tokens_count == 1
    assert receipt.cleaned_containers_count == 1
    assert "tok_doppler_sandbox_abc" in broker.revoked
    assert "container_runner_456" in runner.cleaned

    # Verify ledger entry
    entries = ledger.read("graft-exit-99")
    assert len(entries) >= 1
    assert entries[-1].payload["to_stage"] == "DONE"
