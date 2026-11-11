"""Effect intent and outcome records; external execution belongs to the caller."""

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
    UNKNOWN = "UNKNOWN"
    ROLLED_BACK = "ROLLED_BACK"


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


class EffectManager:
    """Store idempotent intents and preserve unknown outcomes across restart."""

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
                executed_at TEXT, reconciliation_note TEXT
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
        view = self._views.setdefault(slot.slot_id, slot)
        view.status = slot.status
        view.executed_at = slot.executed_at
        view.reconciliation_note = slot.reconciliation_note
        return view

    def allocate_slot(
        self, case_id: str, action_type: str, target_resource: str, idempotency_key: str
    ) -> EffectSlot:
        raw = repr((case_id, action_type, target_resource, idempotency_key)).encode()
        slot_id = f"effect-{hashlib.sha256(raw).hexdigest()[:24]}"
        with self._lock:
            with self._db:
                self._db.execute(
                    "INSERT OR IGNORE INTO effects VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)",
                    (slot_id, case_id, action_type, target_resource, EffectStatus.PENDING,
                     datetime.now(UTC).isoformat()),
                )
            return self._view(self._read_slot(slot_id))

    def record_execution(self, slot_id: str, success: bool, note: str = "") -> EffectSlot:
        status = EffectStatus.EXECUTED if success else EffectStatus.ROLLED_BACK
        return self._record(slot_id, status, note)

    def mark_unknown(self, slot_id: str, reason: str) -> EffectSlot:
        return self._record(slot_id, EffectStatus.UNKNOWN, reason)

    def _record(self, slot_id: str, status: EffectStatus, note: str) -> EffectSlot:
        with self._lock:
            with self._db:
                self._db.execute("BEGIN IMMEDIATE")
                previous = self._read_slot(slot_id)
                if previous.status != status:
                    if previous.status in {EffectStatus.EXECUTED, EffectStatus.ROLLED_BACK}:
                        raise ValueError(
                            "A recorded terminal effect outcome cannot be overwritten"
                        )
                    if previous.status == EffectStatus.UNKNOWN and not note.strip():
                        raise ValueError(
                            "Resolving an unknown effect requires a reconciliation note"
                        )
                    executed_at = (
                        None if status == EffectStatus.UNKNOWN else datetime.now(UTC).isoformat()
                    )
                    self._db.execute(
                        "UPDATE effects SET status = ?, executed_at = ?, reconciliation_note = ? "
                        "WHERE slot_id = ?", (status, executed_at, note, slot_id)
                    )
            return self._view(self._read_slot(slot_id))

    def close(self) -> None:
        with self._lock:
            self._db.close()
