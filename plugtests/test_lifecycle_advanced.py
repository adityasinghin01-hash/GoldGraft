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

    # Missing state preservation manifests: must hold rather than blind restore
    held_receipt = recovery.execute_safe_rollback(
        graft_id="graft-live-1",
        current_stage="LIVE_100",
        reason="Heartbeat ping failure on host gateway",
        idempotency_key="idem-rb-1",
        processed_orders=["ORDER-101", "ORDER-102", "ORDER-103"],
    )
    assert held_receipt.outcome == "held"
    assert held_receipt.reverted_to is None
    assert "no consistent state export; a cutback would lose state" in held_receipt.holds

    # With verified export and disposable restore manifests
    prepared_receipt = recovery.execute_safe_rollback(
        graft_id="graft-live-1",
        current_stage="LIVE_100",
        reason="Heartbeat ping failure on host gateway",
        idempotency_key="idem-rb-2",
        processed_orders=["ORDER-101", "ORDER-102", "ORDER-103"],
        export_manifest_ref="blob://export/manifest-1",
        restore_verified_ref="blob://restore/verified-1",
    )
    assert prepared_receipt.graft_id == "graft-live-1"
    assert prepared_receipt.prior_stage == "LIVE_100"
    assert prepared_receipt.reverted_to == "CUTBACK"
    assert prepared_receipt.retained_orders_count == 3
    assert prepared_receipt.reason == "Heartbeat ping failure on host gateway"

    # Verify ledger entry
    entries = ledger.read("graft-live-1")
    assert len(entries) >= 1
    assert entries[-1].payload["to_stage"] == "CUTBACK"


def test_exit_controller_teardown_and_verification():
    from pieces.backend.lifecycle.exit import (
        ORDINARY_CAPABILITIES,
        ExitCheckResult,
        RevocationAck,
    )

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

    # Missing independent executor: must hold
    held_receipt = exit_ctrl.execute_merchant_exit(
        graft_id="graft-exit-99",
        actor_name="MerchantCTO",
        idempotency_key="idem-exit-1",
        token_keys=["tok_doppler_sandbox_abc"],
        container_ids=["container_runner_456"],
    )
    assert held_receipt.graft_id == "graft-exit-99"
    assert held_receipt.outcome == "held"
    assert held_receipt.status == "HELD"
    assert "no qualified independent exit-check executor; exit held" in held_receipt.holds

    # With merchant-owned executor and capability revocations
    class MerchantExecutor:
        identity_ref = "merchant-executor-1"

        def run_exit_check(self):
            return ExitCheckResult(
                executor_identity_ref="merchant-executor-1",
                restart_performed=True,
                recovery_outcome="recovered",
                observed_evidence_refs=["blob://obs-1"],
                signed=True,
            )

    revocations = [
        RevocationAck(capability=c, acknowledged=True, evidence_ref=f"blob://revoked/{c}")
        for c in ORDINARY_CAPABILITIES
    ]
    exit_ack = RevocationAck(
        capability="exit_evidence", acknowledged=True, evidence_ref="blob://revoked/exit_evidence"
    )

    complete_receipt = exit_ctrl.execute_merchant_exit(
        graft_id="graft-exit-99",
        actor_name="MerchantCTO",
        idempotency_key="idem-exit-2",
        executor=MerchantExecutor(),
        revocations=revocations,
        exit_evidence_ack=exit_ack,
        token_keys=["tok_doppler_sandbox_abc"],
        container_ids=["container_runner_456"],
    )
    assert complete_receipt.graft_id == "graft-exit-99"
    assert complete_receipt.outcome == "complete"
    assert complete_receipt.status == "EXIT_COMPLETE"
    assert complete_receipt.verified_clean is True
    assert complete_receipt.revoked_tokens_count == 1
    assert complete_receipt.cleaned_containers_count == 1
    assert "tok_doppler_sandbox_abc" in broker.revoked
    assert "container_runner_456" in runner.cleaned

    # Verify ledger entry
    entries = ledger.read("graft-exit-99")
    assert len(entries) >= 1
    assert entries[-1].payload["to_stage"] == "DONE"
