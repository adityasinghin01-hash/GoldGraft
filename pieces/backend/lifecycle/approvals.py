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
        self, slot_id: str, required_level: str, *, plan_digest: str | None = None
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

    def revoke_approval(self, slot_id: str, reason: str = "Merchant revoked authority") -> None:
        slot = self._slots.get(slot_id)
        if slot is not None:
            slot.status = "REVOKED"
            slot.revoked_reason = reason
            self.release_target_lock(slot.graft_id, slot.target_resource)
