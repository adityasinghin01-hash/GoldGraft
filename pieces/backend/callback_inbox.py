"""Bounded private callback receipt/retry state; never public/model evidence.

Persistent mode requires host-owned encryption callbacks; this module does not
create, store or manage encryption keys. Memory mode is offline/volatile only.
Receipt acceptance and business-handler execution are intentionally separate.
"""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import RLock


class CallbackInbox:
    def __init__(
        self,
        *,
        database: Path | None = None,
        seal=None,
        unseal=None,
        max_body_bytes=256 * 1024,
        max_receipts=10000,
    ):
        if database is not None and (seal is None or unseal is None):
            raise ValueError("Persistent raw ingress requires host-owned encryption")
        if any(type(n) is not int or n <= 0 for n in (max_body_bytes, max_receipts)):
            raise ValueError("Positive ingress limits required")
        self.seal = seal or (lambda value: value)
        self.unseal = unseal or (lambda value: value)
        self.max_body_bytes, self.max_receipts = max_body_bytes, max_receipts
        self.durable = database is not None
        self._lock = RLock()
        self._db = sqlite3.connect(
            database if database is not None else ":memory:", check_same_thread=False
        )
        self._db.row_factory = sqlite3.Row
        self._db.execute("""CREATE TABLE IF NOT EXISTS callback_inbox (
            graft_id TEXT NOT NULL, kind TEXT NOT NULL, delivery_id TEXT NOT NULL,
            digest TEXT NOT NULL, sealed BLOB NOT NULL, receipt TEXT,
            PRIMARY KEY (graft_id, kind, delivery_id)
        )""")

    @contextmanager
    def processing(self):
        # Serializes local processing. Provider verification may retry; business
        # effect execution belongs in the merchant's transactional origin ledger.
        with self._lock:
            yield

    def accept(self, graft_id, kind, delivery_id, raw: bytes):
        if not delivery_id or len(delivery_id) > 256 or len(raw) > self.max_body_bytes:
            raise ValueError("INGRESS_LIMIT")
        digest = hashlib.sha256(raw).hexdigest()
        with self._lock, self._db:
            self._db.execute("BEGIN IMMEDIATE")
            prior = self._db.execute(
                "SELECT digest FROM callback_inbox WHERE graft_id=? AND kind=? AND delivery_id=?",
                (graft_id, kind, delivery_id),
            ).fetchone()
            if prior:
                if prior[0] != digest:
                    raise ValueError("CALLBACK_IDENTITY_CONFLICT")
                return False
            if self._db.execute("SELECT count(*) FROM callback_inbox").fetchone()[0] >= (
                self.max_receipts
            ):
                raise ValueError("INGRESS_QUOTA")
            self._db.execute(
                "INSERT INTO callback_inbox VALUES (?, ?, ?, ?, ?, NULL)",
                (graft_id, kind, delivery_id, digest, self.seal(raw)),
            )
        return True

    def raw(self, graft_id, kind, delivery_id):
        with self._lock:
            row = self._db.execute(
                "SELECT digest, sealed FROM callback_inbox WHERE graft_id=? AND kind=? "
                "AND delivery_id=?",
                (graft_id, kind, delivery_id),
            ).fetchone()
            if row is None:
                raise LookupError("CALLBACK_UNAVAILABLE")
            raw = self.unseal(row[1])
            if hashlib.sha256(raw).hexdigest() != row[0]:
                raise ValueError("CALLBACK_INTEGRITY_FAILURE")
            return raw

    def receipt(self, graft_id, kind, delivery_id):
        with self._lock:
            row = self._db.execute(
                "SELECT receipt FROM callback_inbox WHERE graft_id=? AND kind=? AND delivery_id=?",
                (graft_id, kind, delivery_id),
            ).fetchone()
            return json.loads(row[0]) if row and row[0] else None

    def record(self, graft_id, kind, delivery_id, receipt):
        with self._lock, self._db:
            self._db.execute(
                "UPDATE callback_inbox SET receipt=? WHERE graft_id=? AND kind=? AND delivery_id=?",
                (json.dumps(receipt), graft_id, kind, delivery_id),
            )

    def close(self):
        with self._lock:
            self._db.close()
