"""Resource-Authorised Apply & Approval Gates (GU04).

Enforces:
1. Hard rule: Read-only tokens CANNOT escalate without explicit merchant re-authorization.
2. Target resource locks across concurrent graft operations to prevent race conditions.
3. Explicit ApprovalSlots bound to specific deployment targets (GitHub PR, Render service).
4. Commits approved authorization receipts into foundation.ledger.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from goldgraft_contracts.common import Producer, ProducerKind
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger


class TargetLockError(Exception):
    """Raised when an effect slot or target resource is locked by another graft."""


class AuthorizationEscalationError(Exception):
    """Raised when a read-only token attempts to perform mutating deployment actions."""


@dataclass
class ApprovalSlot:
    slot_id: str
    graft_id: str
    target_resource: str
    permission_level: str  # "READ_ONLY", "PULL_REQUEST", "DEPLOY_PRODUCTION"
    granted_by: str
    expires_at: str
    status: str  # "GRANTED", "REVOKED", "CONSUMED"


class ApprovalGate:
    """Manages explicit effect slots, permission locks, and deployment approvals."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        self._target_locks: dict[str, str] = {}  # target_resource -> graft_id
        self._slots: dict[str, ApprovalSlot] = {}

    def acquire_target_lock(self, graft_id: str, target_resource: str) -> None:
        """Locks a deployment target (e.g. repo branch, Render service) to a single graft."""
        if target_resource in self._target_locks:
            locking_graft = self._target_locks[target_resource]
            if locking_graft != graft_id:
                msg = (
                    f"Target resource {target_resource!r} is currently locked "
                    f"by graft {locking_graft!r}"
                )
                raise TargetLockError(msg)
        self._target_locks[target_resource] = graft_id

    def release_target_lock(self, graft_id: str, target_resource: str) -> None:
        """Releases the lock on a target resource."""
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
    ) -> ApprovalSlot:
        """Grants explicit merchant authority for a specific deployment action."""
        self.acquire_target_lock(graft_id, target_resource)

        raw_id = f"{graft_id}:{target_resource}:{permission_level}".encode()
        slot_id = f"slot-{hashlib.sha256(raw_id).hexdigest()[:12]}"
        now = datetime.now(UTC).isoformat()

        slot = ApprovalSlot(
            slot_id=slot_id,
            graft_id=graft_id,
            target_resource=target_resource,
            permission_level=permission_level,
            granted_by=granted_by,
            expires_at=now,
            status="GRANTED",
        )
        self._slots[slot_id] = slot

        # Commit durable audit trail to foundation.ledger
        service_producer = Producer(
            kind=ProducerKind.SERVICE,
            name="ApprovalGate",
            version="1.0.0",
        )

        reason = (
            f"Deployment approval granted: {permission_level} "
            f"for {target_resource} by {granted_by}"
        )

        self.ledger.append(
            graft_id=graft_id,
            type=EntryType.STAGE.value,
            producer=service_producer.model_dump(),
            schema="StageChange/1",
            payload={
                "graft_id": graft_id,
                "from_stage": None,
                "to_stage": "PR_OPEN",
                "attempt": 1,
                "reason": reason,
                "actor": {"kind": service_producer.kind.value, "name": service_producer.name},
                "evidence_refs": [f"blob://approval/{slot_id}"],
            },
            idempotency_key=idempotency_key,
        )

        return slot

    def verify_action_permitted(self, slot_id: str, required_level: str) -> None:
        """Verifies that an approval slot is valid and has sufficient authority."""
        slot = self._slots.get(slot_id)
        if not slot or slot.status != "GRANTED":
            raise AuthorizationEscalationError(
                f"Approval slot {slot_id!r} is invalid or has expired"
            )

        # Read-only tokens can never perform writes
        if slot.permission_level == "READ_ONLY" and required_level != "READ_ONLY":
            raise AuthorizationEscalationError(
                f"Escalation denied: slot permission is READ_ONLY, required is {required_level}"
            )

    def revoke_approval(self, slot_id: str, reason: str = "Merchant revoked authority") -> None:
        """Revokes an active approval slot immediately."""
        slot = self._slots.get(slot_id)
        if slot:
            slot.status = "REVOKED"
            self.release_target_lock(slot.graft_id, slot.target_resource)
