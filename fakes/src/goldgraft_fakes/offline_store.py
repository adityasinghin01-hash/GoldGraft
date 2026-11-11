"""Persistent synthetic boundary store. Never a production authority or custody service."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.plan5_common import canonical_bytes, content_digest

LABEL = "SCRIPTED OFFLINE COUNTERPART — not a live service"


def fail(code):
    raise ValueError(code)


def encoded(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", by_alias=True)
    return canonical_bytes(value).decode()


class OfflineStore:
    def __init__(self, path: Path, *, clock=None):
        self.path = Path(path)
        if str(path) == ":memory:":
            fail("INVALID persistent path required")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock or (lambda: datetime.now(UTC))
        with self.transaction() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs(
                    ref TEXT PRIMARY KEY, body TEXT NOT NULL, authority INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS tasks(
                    id TEXT PRIMARY KEY, run_ref TEXT NOT NULL, body TEXT NOT NULL,
                    claim_version INTEGER);
                CREATE TABLE IF NOT EXISTS keys(namespace TEXT, id TEXT, digest TEXT,
                    result TEXT, PRIMARY KEY(namespace,id));
                CREATE TABLE IF NOT EXISTS blobs(
                    ref TEXT PRIMARY KEY, body BLOB NOT NULL, scope TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS artifacts(
                    ref TEXT PRIMARY KEY, descriptor TEXT NOT NULL, payload BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS contexts(ref TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS checkpoints(ref TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS results(task_id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS wakes(task_id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS invocations(
                    id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY, run_ref TEXT NOT NULL,
                    sequence INTEGER NOT NULL, body TEXT NOT NULL,
                    ack INTEGER NOT NULL DEFAULT 0, UNIQUE(run_ref,sequence));
                CREATE TABLE IF NOT EXISTS model_turns(id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL, task_id TEXT NOT NULL, request TEXT NOT NULL,
                    result TEXT, status TEXT NOT NULL, dispatch_count INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS tools(id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL, task_id TEXT NOT NULL,
                    body TEXT NOT NULL, dispatch_count INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS scripts(namespace TEXT, id TEXT,
                    body TEXT, PRIMARY KEY(namespace,id));
                CREATE TABLE IF NOT EXISTS deliveries(run_ref TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS effects(id TEXT PRIMARY KEY, logical_key TEXT UNIQUE,
                    fingerprint TEXT, body TEXT, dispatch_count INTEGER NOT NULL);
            """)
        self.path.chmod(0o600)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("BEGIN IMMEDIATE")
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    def key(self, db, namespace, key, body, result=None):
        digest = content_digest(body)
        row = db.execute(
            "SELECT * FROM keys WHERE namespace=? AND id=?", (namespace, key)
        ).fetchone()
        if row:
            if row["digest"] != digest:
                fail("CONFLICT")
            return json.loads(row["result"])
        if result is not None:
            db.execute(
                "INSERT INTO keys VALUES(?,?,?,?)", (namespace, key, digest, encoded(result))
            )
        return None

    def blob(self, db, scope, value):
        data = canonical_bytes(value)
        ref = "fake:blob:" + content_digest({"scope": scope, "body": value})
        db.execute("INSERT OR IGNORE INTO blobs VALUES(?,?,?)", (ref, data, scope))
        return ref

    def raw(self, ref, *, scope):
        with self.transaction() as db:
            row = db.execute("SELECT * FROM blobs WHERE ref=?", (ref,)).fetchone()
            if row is None or row["scope"] != scope:
                fail("DENIED")
            return bytes(row["body"])
