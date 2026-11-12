"""Effect intents and unknown-effect reconciliation (GU04); the caller runs the effect itself.

A failed effect is not a rolled-back effect. Compensation needs its own
authority and its own record, and an unknown effect keeps retrying the *same*
identity rather than spending a second slot.

Slot identity is derived from the case, operation, target and idempotency key,
so a duplicate request returns the original slot instead of creating cardinality
beyond one. Intents and outcomes are stored transactionally (pass a private
database path to keep them across a restart); a recorded terminal outcome is
never overwritten, and resolving an unknown outcome needs a reconciliation note.
"""

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import Lock


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


# Outcomes that later records may not change (FAILED may be retried on the same slot).
TERMINAL = {EffectStatus.EXECUTED, EffectStatus.COMPENSATED, EffectStatus.ROLLED_BACK}


class EffectManager:
    """One durable slot per effect identity, with explicit unknown handling across restart."""

    def __init__(self, *, database: Path | None = None):
        self._lock = Lock()
        self._views: dict[str, EffectSlot] = {}
        self._db = sqlite3.connect(
            database if database is not None else ":memory:", check_same_thread=False
        )
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS effects (
                slot_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, action_type TEXT NOT NULL,
                target_resource TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                executed_at TEXT, reconciliation_note TEXT,
                attempts INTEGER NOT NULL DEFAULT 0, compensation_ref TEXT
            )
        """)

    def _read_slot(self, slot_id: str) -> EffectSlot:
        row = self._db.execute("SELECT * FROM effects WHERE slot_id = ?", (slot_id,)).fetchone()
        if row is None:
            raise KeyError(f"Effect slot {slot_id} not found")
        values = dict(row)
        values["status"] = EffectStatus(values["status"])
        return EffectSlot(**values)

    def _view(self, slot: EffectSlot) -> EffectSlot:
        """Keep one object per slot so callers holding it see later outcomes."""
        view = self._views.setdefault(slot.slot_id, slot)
        changing = ("status", "executed_at", "reconciliation_note", "attempts", "compensation_ref")
        for name in changing:
            setattr(view, name, getattr(slot, name))
        return view

    def allocate_slot(
        self, case_id: str, action_type: str, target_resource: str, idempotency_key: str
    ) -> EffectSlot:
        raw = repr((case_id, action_type, target_resource, idempotency_key)).encode()
        slot_id = f"effect-{hashlib.sha256(raw).hexdigest()[:24]}"
        with self._lock:
            with self._db:
                self._db.execute(
                    "INSERT OR IGNORE INTO effects "
                    "(slot_id, case_id, action_type, target_resource, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        slot_id,
                        case_id,
                        action_type,
                        target_resource,
                        EffectStatus.PENDING,
                        datetime.now(UTC).isoformat(),
                    ),
                )
            return self._view(self._read_slot(slot_id))

    def record_execution(self, slot_id: str, success: bool, note: str = "") -> EffectSlot:
        status = EffectStatus.EXECUTED if success else EffectStatus.FAILED
        return self._record(slot_id, status, note, attempt=True)

    def allocate_plan_slot(self, plan, slot_id: str) -> EffectSlot:
        """A caller retry key cannot buy a second effect for an immutable plan slot.

        Current independent authorities/approvals/reservations must be verified
        by the accepting service before dispatch; allocation alone is no grant.
        """
        from goldgraft_contracts.lifecycle import ActionPlan, canonical_target_id
        from goldgraft_contracts.plan5_common import content_digest

        plan = ActionPlan.model_validate(plan.model_dump(mode="json"))
        if (
            content_digest(plan.model_dump(mode="json", exclude={"plan_digest"}))
            != plan.plan_digest
        ):
            raise ValueError("Action plan digest mismatch")
        slot = next((s for s in plan.slots if s.slot_id == slot_id), None)
        if slot is None:
            raise ValueError("Unknown action plan slot")
        return self.allocate_slot(
            plan.case_id,
            slot.operation,
            canonical_target_id(slot.target_key),
            content_digest([plan.plan_digest, slot_id]),
        )

    def mark_unknown(self, slot_id: str, reason: str) -> EffectSlot:
        return self._record(slot_id, EffectStatus.UNKNOWN, reason)

    def reconcile(self, slot_id: str, *, observed: bool, note: str) -> EffectSlot:
        """Resolve an unknown effect without creating a new slot."""
        status = EffectStatus.EXECUTED if observed else EffectStatus.FAILED
        return self._record(slot_id, status, note, only_from={EffectStatus.UNKNOWN})

    def record_compensation(
        self, slot_id: str, *, authority_ref: str, note: str = ""
    ) -> EffectSlot:
        """Compensation is a separate financial action with its own authority."""
        if not authority_ref:
            raise ValueError("compensation requires separate financial authority")
        return self._record(
            slot_id,
            EffectStatus.COMPENSATED,
            note,
            only_from={EffectStatus.EXECUTED},
            compensation_ref=authority_ref,
        )

    def _record(
        self,
        slot_id: str,
        status: EffectStatus,
        note: str,
        *,
        attempt: bool = False,
        only_from: set[EffectStatus] | None = None,
        compensation_ref: str | None = None,
    ) -> EffectSlot:
        with self._lock:
            with self._db:
                self._db.execute("BEGIN IMMEDIATE")
                previous = self._read_slot(slot_id)
                if previous.status == status:
                    return self._view(previous)  # idempotent replay of the same outcome
                if only_from is not None and previous.status not in only_from:
                    allowed = ", ".join(sorted(only_from))
                    raise ValueError(f"only a {allowed} effect can move to {status}")
                if previous.status in TERMINAL and status != EffectStatus.COMPENSATED:
                    raise ValueError("A recorded terminal effect outcome cannot be overwritten")
                if previous.status == EffectStatus.UNKNOWN and not note.strip():
                    raise ValueError("Resolving an unknown effect requires a reconciliation note")
                executed_at = (
                    previous.executed_at
                    if status in {EffectStatus.UNKNOWN, EffectStatus.COMPENSATED}
                    else datetime.now(UTC).isoformat()
                )
                self._db.execute(
                    "UPDATE effects SET status = ?, executed_at = ?, reconciliation_note = ?, "
                    "attempts = attempts + ?, compensation_ref = COALESCE(?, compensation_ref) "
                    "WHERE slot_id = ?",
                    (status, executed_at, note, int(attempt), compensation_ref, slot_id),
                )
            return self._view(self._read_slot(slot_id))

    def close(self) -> None:
        with self._lock:
            self._db.close()
