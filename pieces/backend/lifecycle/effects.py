"""Effect intents and unknown-effect reconciliation (GU04).

A failed effect is not a rolled-back effect. Compensation needs its own
authority and its own record, and an unknown effect keeps retrying the *same*
identity rather than spending a second slot.

Slot identity is derived from the case, operation, target and idempotency key,
so a duplicate request returns the original slot instead of creating cardinality
beyond one.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class EffectStatus(StrEnum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    COMPENSATED = "COMPENSATED"
    ROLLED_BACK = "ROLLED_BACK"  # legacy value; compensation uses COMPENSATED


@dataclass
class EffectSlot:
    slot_id: str
    case_id: str
    action_type: str
    target_resource: str
    status: EffectStatus
    created_at: str
    executed_at: str | None = None
    reconciliation_note: str | None = None
    attempts: int = 0
    compensation_ref: str | None = None

    def __post_init__(self):
        if self.status == EffectStatus.COMPENSATED and not self.compensation_ref:
            raise ValueError("compensation requires its own authority reference")


class EffectManager:
    """Guarantees one slot per effect identity and explicit unknown handling."""

    def __init__(self):
        self._slots: dict[str, EffectSlot] = {}

    def allocate_slot(
        self,
        case_id: str,
        action_type: str,
        target_resource: str,
        idempotency_key: str,
    ) -> EffectSlot:
        raw = f"{case_id}:{action_type}:{target_resource}:{idempotency_key}".encode()
        slot_id = f"effect-{hashlib.sha256(raw).hexdigest()[:12]}"
        if slot_id in self._slots:
            return self._slots[slot_id]
        slot = EffectSlot(
            slot_id=slot_id,
            case_id=case_id,
            action_type=action_type,
            target_resource=target_resource,
            status=EffectStatus.PENDING,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._slots[slot_id] = slot
        return slot

    def record_execution(self, slot_id: str, success: bool, note: str = "") -> EffectSlot:
        slot = self._slots.get(slot_id)
        if slot is None:
            raise KeyError(f"Effect slot {slot_id} not found")
        if slot.status in {EffectStatus.COMPENSATED, EffectStatus.ROLLED_BACK}:
            raise ValueError("a compensated effect cannot be re-executed")
        slot.attempts += 1
        slot.status = EffectStatus.EXECUTED if success else EffectStatus.FAILED
        slot.executed_at = datetime.now(UTC).isoformat()
        slot.reconciliation_note = note
        return slot

    def mark_unknown(self, slot_id: str, reason: str) -> EffectSlot:
        slot = self._slots.get(slot_id)
        if slot is None:
            raise KeyError(f"Effect slot {slot_id} not found")
        slot.status = EffectStatus.UNKNOWN
        slot.reconciliation_note = reason
        return slot

    def reconcile(self, slot_id: str, *, observed: bool, note: str) -> EffectSlot:
        """Resolve an unknown effect without creating a new slot."""
        slot = self._slots.get(slot_id)
        if slot is None:
            raise KeyError(f"Effect slot {slot_id} not found")
        if slot.status != EffectStatus.UNKNOWN:
            raise ValueError("only an unknown effect can be reconciled")
        slot.status = EffectStatus.EXECUTED if observed else EffectStatus.FAILED
        slot.executed_at = datetime.now(UTC).isoformat()
        slot.reconciliation_note = note
        return slot

    def record_compensation(
        self, slot_id: str, *, authority_ref: str, note: str = ""
    ) -> EffectSlot:
        """Compensation is a separate financial action with its own authority."""
        if not authority_ref:
            raise ValueError("compensation requires separate financial authority")
        slot = self._slots.get(slot_id)
        if slot is None:
            raise KeyError(f"Effect slot {slot_id} not found")
        if slot.status != EffectStatus.EXECUTED:
            raise ValueError("only an observed effect can be compensated")
        slot.status = EffectStatus.COMPENSATED
        slot.compensation_ref = authority_ref
        slot.reconciliation_note = note
        return slot
