"""Durable cross-case/run target locks and fencing, with atomic group acquisition.

Use canonical TargetKey records for provider resources. Legacy string keys stay
exact; a caller must not invent aliases for the same physical resource.
"""

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from uuid import uuid4

from goldgraft_contracts.lifecycle import TargetKey, canonical_target_id


class ReservationConflictError(Exception):
    """A target cannot be transferred until its previous effects are known."""


@dataclass
class TargetReservation:
    reservation_id: str
    target_resource: str
    case_id: str
    granted_at: str
    expires_at: str
    owner_run_id: str | None = None
    fence_epoch: int = 1
    unresolved_effect_refs: list[str] = field(default_factory=list)
    released: bool = False

    def active(self, now: datetime) -> bool:
        return not self.released and datetime.fromisoformat(self.expires_at) > now


class TargetReservationManager:
    def __init__(self, default_lease_seconds: int = 300, *, database: Path | None = None):
        self._ttl(default_lease_seconds)
        self.default_lease_seconds = default_lease_seconds
        self._lock = Lock()
        self._views: dict[str, TargetReservation] = {}
        self._db = sqlite3.connect(
            database if database is not None else ":memory:", check_same_thread=False
        )
        self._db.row_factory = sqlite3.Row
        self._db.execute("""CREATE TABLE IF NOT EXISTS target_reservations (
            reservation_id TEXT PRIMARY KEY, target_resource TEXT NOT NULL,
            case_id TEXT NOT NULL, granted_at TEXT NOT NULL, expires_at TEXT NOT NULL,
            owner_run_id TEXT, fence_epoch INTEGER NOT NULL,
            unresolved_effect_refs TEXT NOT NULL, released INTEGER NOT NULL
        )""")

    @staticmethod
    def _ttl(value):
        if type(value) is not int or value <= 0:
            raise ValueError("Lease must be a positive integer")
        return value

    @staticmethod
    def _key(value):
        if isinstance(value, TargetKey):
            return canonical_target_id(value)
        if not isinstance(value, str) or not value.strip() or "*" in value:
            raise ValueError("Canonical target required")
        return value

    @contextmanager
    def _write(self):
        with self._lock, self._db:
            self._db.execute("BEGIN IMMEDIATE")
            yield

    def _read(self, reservation_id):
        row = self._db.execute(
            "SELECT * FROM target_reservations WHERE reservation_id = ?", (reservation_id,)
        ).fetchone()
        if row is None:
            raise ReservationConflictError("Reservation not found")
        body = dict(row)
        body["unresolved_effect_refs"] = json.loads(body["unresolved_effect_refs"])
        body["released"] = bool(body["released"])
        return TargetReservation(**body)

    def _view(self, value):
        view = self._views.setdefault(value.reservation_id, value)
        view.__dict__.update(value.__dict__)
        return view

    def reserve(self, target_resource, case_id, *, lease_seconds=None, run_id=None):
        return self.reserve_many(
            [target_resource], case_id, lease_seconds=lease_seconds, run_id=run_id
        )[0]

    def reserve_many(self, targets, case_id, *, lease_seconds=None, run_id=None):
        keys = sorted({self._key(t) for t in targets})
        if not keys:
            raise ValueError("At least one target required")
        ttl = self._ttl(self.default_lease_seconds if lease_seconds is None else lease_seconds)
        now = datetime.now(UTC)
        with self._write():
            values = [self._reserve(key, case_id, run_id, ttl, now) for key in keys]
        # Do not update caller views for a partially rolled back group.
        return [self._view(v) for v in values]

    def _reserve(self, key, case_id, run_id, ttl, now):
        rows = self._db.execute(
            "SELECT reservation_id FROM target_reservations WHERE target_resource = ? "
            "ORDER BY fence_epoch DESC",
            (key,),
        ).fetchall()
        previous = self._read(rows[0][0]) if rows else None
        if previous and not previous.released:
            if previous.active(now):
                if previous.case_id != case_id or previous.owner_run_id != run_id:
                    raise ReservationConflictError(f"Target {key} reserved by case/run")
                previous.expires_at = (now + timedelta(seconds=ttl)).isoformat()
                self._db.execute(
                    "UPDATE target_reservations SET expires_at = ? WHERE reservation_id = ?",
                    (previous.expires_at, previous.reservation_id),
                )
                return previous
            if previous.unresolved_effect_refs:
                raise ReservationConflictError("Target has unresolved effects; reconcile first")
            self._db.execute(
                "UPDATE target_reservations SET released = 1 WHERE reservation_id = ?",
                (previous.reservation_id,),
            )
        value = TargetReservation(
            "res-" + uuid4().hex,
            key,
            case_id,
            now.isoformat(),
            (now + timedelta(seconds=ttl)).isoformat(),
            run_id,
            previous.fence_epoch + 1 if previous else 1,
        )
        self._db.execute(
            "INSERT INTO target_reservations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                value.reservation_id,
                key,
                case_id,
                value.granted_at,
                value.expires_at,
                run_id,
                value.fence_epoch,
                "[]",
                0,
            ),
        )
        return value

    def current_epoch(self, reservation_id):
        with self._lock:
            value = self._read(reservation_id)
            if not value.active(datetime.now(UTC)):
                raise ReservationConflictError("Reservation is not active")
            return value.fence_epoch

    def require_current(self, reservation_id, *, case_id, epoch, run_id=None):
        with self._lock:
            value = self._read(reservation_id)
            if (
                value.case_id != case_id
                or value.fence_epoch != epoch
                or value.owner_run_id != run_id
                or not value.active(datetime.now(UTC))
            ):
                raise ReservationConflictError("Stale reservation owner, fencing epoch or lease")

    def add_unresolved(self, reservation_id, effect_ref):
        with self._write():
            value = self._read(reservation_id)
            if not value.active(datetime.now(UTC)):
                raise ReservationConflictError("Cannot dispatch under inactive reservation")
            if effect_ref not in value.unresolved_effect_refs:
                value.unresolved_effect_refs.append(effect_ref)
            self._save_refs(value)
        self._view(value)

    def resolve_unresolved(self, reservation_id, effect_ref):
        with self._write():
            value = self._read(reservation_id)
            if effect_ref in value.unresolved_effect_refs:
                value.unresolved_effect_refs.remove(effect_ref)
            self._save_refs(value)
        self._view(value)

    def _save_refs(self, value):
        self._db.execute(
            "UPDATE target_reservations SET unresolved_effect_refs = ? WHERE reservation_id = ?",
            (json.dumps(value.unresolved_effect_refs), value.reservation_id),
        )

    def release(self, reservation_id):
        with self._write():
            value = self._read(reservation_id)
            if value.unresolved_effect_refs:
                raise ReservationConflictError("Cannot release target with unresolved effects")
            self._db.execute(
                "UPDATE target_reservations SET released = 1 WHERE reservation_id = ?",
                (reservation_id,),
            )
            value.released = True
        self._view(value)

    def close(self):
        with self._lock:
            self._db.close()
