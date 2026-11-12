"""Resource-authorised apply and approval gates (GU04).

An approval slot is bound to one target resource, one permission level and one
plan digest, and it expires. Verification checks all three: an expired or
plan-mismatched slot denies the effect, and a read-only slot can never escalate.

Approval is issued by a controller for exact resources; possession of a grant id
is not authority for a different target.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from goldgraft_contracts.common import Producer, ProducerKind
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger

LEVELS = ("READ_ONLY", "PULL_REQUEST", "DEPLOY_PRODUCTION")


class TargetLockError(Exception):
    """Raised when an effect slot or target resource is locked by another graft."""


class AuthorizationEscalationError(Exception):
    """Raised when authority does not cover the requested action."""


@dataclass
class ApprovalSlot:
    slot_id: str
    graft_id: str
    target_resource: str
    permission_level: str
    granted_by: str
    expires_at: str
    status: str
    plan_digest: str | None = None
    revoked_reason: str | None = None


class ApprovalGate:
    """Manages explicit effect slots, permission locks and deployment approvals."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        self._target_locks: dict[str, str] = {}
        self._slots: dict[str, ApprovalSlot] = {}

    def acquire_target_lock(self, graft_id: str, target_resource: str) -> None:
        locking_graft = self._target_locks.get(target_resource)
        if locking_graft is not None and locking_graft != graft_id:
            raise TargetLockError(
                f"Target resource {target_resource!r} is currently locked by graft "
                f"{locking_graft!r}"
            )
        self._target_locks[target_resource] = graft_id

    def release_target_lock(self, graft_id: str, target_resource: str) -> None:
        if self._target_locks.get(target_resource) == graft_id:
            del self._target_locks[target_resource]

    def grant_approval(
        self,
        graft_id: str,
        target_resource: str,
        *,
        permission_level: str,
        granted_by: str,
        idempotency_key: str,
        plan_digest: str | None = None,
        ttl_seconds: int = 300,
    ) -> ApprovalSlot:
        if permission_level not in LEVELS:
            raise AuthorizationEscalationError(f"Unknown permission level: {permission_level!r}")
        if ttl_seconds <= 0:
            raise AuthorizationEscalationError("Approval must have a positive lifetime")
        self.acquire_target_lock(graft_id, target_resource)

        raw_id = f"{graft_id}:{target_resource}:{permission_level}:{plan_digest}".encode()
        slot_id = f"slot-{hashlib.sha256(raw_id).hexdigest()[:12]}"
        now = datetime.now(UTC)
        slot = ApprovalSlot(
            slot_id=slot_id,
            graft_id=graft_id,
            target_resource=target_resource,
            permission_level=permission_level,
            granted_by=granted_by,
            expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
            status="GRANTED",
            plan_digest=plan_digest,
        )
        self._slots[slot_id] = slot

        # Commit durable audit trail to foundation.ledger
        producer = Producer(kind=ProducerKind.SERVICE, name="ApprovalGate", version="2.0.0")
        self.ledger.append(
            graft_id=graft_id,
            type=EntryType.STAGE.value,
            producer=producer.model_dump(),
            schema="StageChange/1",
            payload={
                "graft_id": graft_id,
                "from_stage": None,
                "to_stage": "PR_OPEN",
                "attempt": 1,
                "reason": (
                    f"Deployment approval granted: {permission_level} for {target_resource} "
                    f"by {granted_by}"
                ),
                "actor": {"kind": producer.kind.value, "name": producer.name},
                "evidence_refs": [f"blob://approval/{slot_id}"],
            },
            idempotency_key=idempotency_key,
        )
        return slot

    def verify_action_permitted(
        self,
        slot_id: str,
        required_level: str,
        *,
        plan_digest: str | None = None,
        target_resource: str | None = None,
    ) -> None:
        """Deny unless the slot is current, unexpired and covers the exact plan."""
        slot = self._slots.get(slot_id)
        if slot is None or slot.status != "GRANTED":
            raise AuthorizationEscalationError(
                f"Approval slot {slot_id!r} is invalid or has expired / revoked"
            )
        if datetime.fromisoformat(slot.expires_at) <= datetime.now(UTC):
            raise AuthorizationEscalationError(f"Approval slot {slot_id!r} has expired")
        if plan_digest is not None and slot.plan_digest != plan_digest:
            raise AuthorizationEscalationError(
                f"Approval slot {slot_id!r} does not cover this action plan"
            )
        if self._target_locks.get(slot.target_resource) != slot.graft_id:
            raise AuthorizationEscalationError("Target lock no longer belongs to this approval")
        if required_level not in LEVELS:
            raise AuthorizationEscalationError(f"Unknown permission level: {required_level!r}")
        if slot.permission_level == "READ_ONLY" and required_level != "READ_ONLY":
            raise AuthorizationEscalationError(
                f"Escalation denied: slot permission is READ_ONLY, required is {required_level}"
            )
        if LEVELS.index(slot.permission_level) < LEVELS.index(required_level):
            raise AuthorizationEscalationError(
                f"Escalation denied: slot permission {slot.permission_level} does not cover "
                f"{required_level}"
            )

        if required_level != "READ_ONLY" and (
            not plan_digest or target_resource != slot.target_resource
        ):
            raise AuthorizationEscalationError("Exact action plan and target binding required")

    def revoke_approval(self, slot_id: str, reason: str = "Merchant revoked authority") -> None:
        slot = self._slots.get(slot_id)
        if slot is not None:
            slot.status = "REVOKED"
            slot.revoked_reason = reason
            self.release_target_lock(slot.graft_id, slot.target_resource)


def verify_plan_approvals(
    plan,
    approval_set,
    *,
    authorities,
    approvals,
    reservation,
    current_authority_epochs,
    current_resource_epochs,
    required_controllers_by_target,
    current_version_refs,
    reservation_plan_digest,
    now=None,
):
    """Check resolved, host-authenticated records, never caller-selected role claims.

    This is the offline-checkable IR05 boundary. The host must authenticate
    current controllers/provider versions and reserve effect slots atomically
    with dispatch. Passing this function does not execute or qualify a provider.
    """
    from goldgraft_contracts.lifecycle import canonical_target_id
    from goldgraft_contracts.plan5_common import content_digest

    now = now or datetime.now(UTC)
    fail = AuthorizationEscalationError
    if (
        content_digest(plan.model_dump(mode="json", exclude={"plan_digest"})) != plan.plan_digest
        or plan.expires_at <= now
        or approval_set.state != "complete"
        or (
            approval_set.case_id,
            approval_set.run_id,
            approval_set.generation,
            approval_set.plan_digest,
        )
        != (plan.case_id, plan.run_id, plan.generation, plan.plan_digest)
        or approval_set.checked_at > now
    ):
        raise fail("Stale, incomplete or mismatched action approval set")
    if (
        reservation.case_id != plan.case_id
        or reservation.run_id != plan.run_id
        or reservation.state != "held"
        or reservation.lease_until <= now
        or reservation.unresolved_effect_refs
        or reservation_plan_digest != plan.plan_digest
        or reservation.resource_epochs != current_resource_epochs
    ):
        raise fail("Current resolved target reservation required")
    if approval_set.authority_epochs != current_authority_epochs:
        raise fail("Authority epochs changed")
    required_controllers = {c for s in plan.slots for c in s.required_controller_ids}
    if set(approval_set.required_controller_ids) != required_controllers:
        raise fail("Missing independent controller approval")
    for slot in plan.slots:
        target = canonical_target_id(slot.target_key)
        if set(slot.required_controller_ids) != set(required_controllers_by_target.get(target, [])):
            raise fail("Required controllers differ from current resource control inventory")
        if target not in reservation.resource_epochs:
            raise fail("Slot target is not reserved")
        if slot.expected_version_ref not in reservation.expected_version_refs:
            raise fail("Expected provider version is not reserved")
        if slot.expected_version_ref != current_version_refs.get(target):
            raise fail("Provider resource version changed")
        for controller in slot.required_controller_ids:
            covered = False
            for ref in slot.required_authority_refs:
                authority = authorities.get(ref)
                if (
                    authority is None
                    or authority.controller_id != controller
                    or authority.target_key != slot.target_key
                    or slot.operation not in authority.actions
                    or authority.revoked_at
                    or not authority.issued_at <= now < authority.expires_at
                    or authority.grant_epoch != current_authority_epochs.get(authority.authority_id)
                    or not authority.role_evidence_refs
                ):
                    continue
                for approval_ref in approval_set.approval_refs:
                    approval = approvals.get(approval_ref)
                    if (
                        approval is not None
                        and ref in approval.authority_refs
                        and approval.controller_id == controller
                        and approval.case_id == plan.case_id
                        and approval.generation == plan.generation
                        and approval.action_plan_digest == plan.plan_digest
                        and approval.reviewed_bundle_digest == plan.review_bundle_digest
                        and approval.graph_digest == plan.graph_digest
                        and approval.scope_digest == plan.scope_digest
                        and approval.policy_digest == plan.policy_digest
                        and target in approval.target_resources
                        and slot.operation in approval.allowed_actions
                        and approval.authority_binding_epochs == current_authority_epochs
                        and approval.trigger_chain_digest == slot.trigger_digest
                        and (
                            slot.artifact_digest is None
                            or approval.artifact_digest == slot.artifact_digest
                        )
                        and (
                            slot.config_digest is None
                            or approval.config_digest == slot.config_digest
                        )
                        and (
                            slot.state_plan_digest is None
                            or approval.state_plan_digest == slot.state_plan_digest
                        )
                        and not approval.revoked_at
                        and approval.issued_at <= now < approval.expires_at
                    ):
                        covered = True
            if not covered:
                raise fail("Independent controller does not cover exact resource/action/plan")
    return True
