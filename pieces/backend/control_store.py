"""Durable control-plane store for the v2 connection service.

SQLite (stdlib) with explicit ``BEGIN IMMEDIATE`` transactions, so durable
Start, cancellation tombstones, idempotency replay and generation fencing are
tested against real transactional behaviour instead of a dict.

The store owns persistence only. Authority decisions stay in the service.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    principal_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    csrf TEXT NOT NULL,
    kind TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drafts (
    draft_id TEXT PRIMARY KEY,
    shop_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    state TEXT NOT NULL,
    continuation_hash TEXT NOT NULL,
    case_id TEXT
);
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    requester_id TEXT NOT NULL,
    shop_url TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    state_version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS members (
    case_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (case_id, principal_id)
);
CREATE TABLE IF NOT EXISTS nodes (
    case_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    label TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    environment TEXT NOT NULL,
    controller_state TEXT NOT NULL,
    read_scope_text TEXT NOT NULL,
    permitted_actions TEXT NOT NULL,
    PRIMARY KEY (case_id, node_id)
);
CREATE TABLE IF NOT EXISTS bindings (
    binding_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    environment TEXT NOT NULL,
    state TEXT NOT NULL,
    scope_text TEXT NOT NULL,
    epochs TEXT NOT NULL,
    evidence_refs TEXT NOT NULL,
    evidence_class TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS provider_intents (
    intent_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    resource_id TEXT,
    purpose TEXT NOT NULL,
    continuation_ref TEXT NOT NULL,
    continuation_hash TEXT NOT NULL,
    redirect_url TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invitations (
    invitation_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    resource_ids TEXT NOT NULL,
    requester_id TEXT NOT NULL,
    recipient_hint TEXT,
    copy_url TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL,
    controller_id TEXT
);
CREATE TABLE IF NOT EXISTS readiness (
    readiness_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    body TEXT NOT NULL,
    digest TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS action_intents (
    action_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    readiness_id TEXT NOT NULL,
    readiness_digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS acceptances (
    action_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    work_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    body TEXT NOT NULL,
    accepted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS work (
    work_id TEXT PRIMARY KEY,
    action_id TEXT NOT NULL UNIQUE,
    case_id TEXT NOT NULL,
    state TEXT NOT NULL,
    generation INTEGER,
    lease_until TEXT,
    cancel_ref TEXT,
    evidence_refs TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS outbox (
    work_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    dispatched_at TEXT
);
CREATE TABLE IF NOT EXISTS cancellations (
    cancel_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    state TEXT NOT NULL,
    work_id TEXT,
    generation INTEGER,
    evidence_refs TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS tombstones (
    action_id TEXT PRIMARY KEY,
    cancel_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ids (
    scope TEXT NOT NULL,
    idem_key TEXT NOT NULL,
    body_hash TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    body TEXT NOT NULL,
    PRIMARY KEY (scope, idem_key)
);
CREATE TABLE IF NOT EXISTS events (
    case_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (case_id, seq)
);
CREATE TABLE IF NOT EXISTS uploads (
    upload_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    contributor_id TEXT NOT NULL,
    body TEXT NOT NULL,
    state TEXT NOT NULL,
    received TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS worker_ops (
    operation_id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    result TEXT NOT NULL,
    body TEXT NOT NULL
);
"""


class _Tx:
    """Thin helpers over a cursor inside one transaction."""

    def __init__(self, cursor: sqlite3.Cursor):
        self.cursor = cursor

    def run(self, sql: str, params: tuple = ()) -> None:
        self.cursor.execute(sql, params)

    def one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

    def all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def value(self, sql: str, params: tuple = ()) -> Any:
        row = self.one(sql, params)
        return None if row is None else row[0]


class ControlStore:
    """One SQLite database, serialized writes, durable reads."""

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        if self.path == ":memory:":
            self._conn = sqlite3.connect(
                ":memory:",
                check_same_thread=False,
                isolation_level=None,
            )
        else:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        cursor = self._conn.cursor()
        try:
            cursor.executescript(SCHEMA)
        finally:
            cursor.close()

    @contextmanager
    def transaction(self):
        with self._lock:
            cursor = self._conn.cursor()
            try:
                cursor.execute("BEGIN IMMEDIATE")
                yield _Tx(cursor)
                cursor.execute("COMMIT")
            except BaseException:
                try:
                    cursor.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                cursor.close()

    def read(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            cursor = self._conn.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.fetchall()
            finally:
                cursor.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()
