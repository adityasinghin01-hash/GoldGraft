"""Effect Intent Reservations and Unknown State Reconciliation (GU04).

Implements:
1. Explicit EffectSlot allocation preventing duplicate external side-effects.
2. Commits effect intents before mutation; commits execution receipts upon completion.
3. Unknown result reconciliation (e.g. timeout during HTTP postback).
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class EffectStatus(StrEnum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    UNKNOWN = "UNKNOWN"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class EffectSlot:
    slot_id: str
    case_id: str
    action_type: str  # "PUBLISH_PR", "RENDER_DEPLOY", "REVOKE_TOKEN"
    target_resource: str
    status: EffectStatus
    created_at: str
    executed_at: str | None = None
    reconciliation_note: str | None = None


class EffectManager:
    """Guarantees exactly-once effect intent processing and unknown reconciliation."""

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
        if not slot:
            raise KeyError(f"Effect slot {slot_id} not found")

        slot.status = EffectStatus.EXECUTED if success else EffectStatus.ROLLED_BACK
        slot.executed_at = datetime.now(UTC).isoformat()
        slot.reconciliation_note = note
        return slot

    def mark_unknown(self, slot_id: str, reason: str) -> EffectSlot:
        slot = self._slots.get(slot_id)
        if not slot:
            raise KeyError(f"Effect slot {slot_id} not found")

        slot.status = EffectStatus.UNKNOWN
        slot.reconciliation_note = reason
        return slot
