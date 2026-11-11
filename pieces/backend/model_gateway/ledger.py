"""One durable local project allowance; integer micro-USD, never a per-agent reset."""

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


def money(value):
    if type(value) is not int or not 0 <= value <= 20000000:
        raise ValueError("INVALID money")
    return value


class Ledger:
    def __init__(self, path):
        self.path = Path(path)
        if str(path) == ":memory:" or self.path.is_symlink():
            raise ValueError("INVALID durable private ledger path")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS budget(
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    active_cap INTEGER NOT NULL, hard_cap INTEGER NOT NULL,
                    frozen INTEGER NOT NULL DEFAULT 0);
                INSERT OR IGNORE INTO budget VALUES(1,50000,20000000,0);
                CREATE TABLE IF NOT EXISTS batches(
                    id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                    ceiling INTEGER NOT NULL, actual INTEGER NOT NULL DEFAULT 0,
                    state TEXT NOT NULL DEFAULT 'reserved', stopped INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS turns(
                    batch TEXT NOT NULL, id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    reserved INTEGER NOT NULL, actual INTEGER NOT NULL DEFAULT 0,
                    state TEXT NOT NULL, result TEXT, usage TEXT,
                    PRIMARY KEY(batch,id));
                CREATE TABLE IF NOT EXISTS provider_observations(
                    batch TEXT NOT NULL, turn TEXT NOT NULL, record TEXT NOT NULL,
                    PRIMARY KEY(batch,turn));
                CREATE TABLE IF NOT EXISTS cap_changes(
                    authority_ref TEXT PRIMARY KEY, old_cap INTEGER NOT NULL,
                    new_cap INTEGER NOT NULL, recorded_at_utc TEXT NOT NULL);
            """)
        self.path.chmod(0o600)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _batch(self, db, batch):
        row = db.execute("SELECT * FROM batches WHERE id=?", (batch,)).fetchone()
        if row is None:
            raise ValueError("NOT_FOUND batch")
        return row

    def _uncertain(self, db, batch=None):
        return (
            db.execute(
                "SELECT 1 FROM turns WHERE state IN ('intended','submitted','unknown') LIMIT 1"
            ).fetchone()
            is not None
        )

    def _writable(self, db, batch=None):
        if db.execute("SELECT frozen FROM budget WHERE singleton=1").fetchone()[0]:
            raise ValueError("FROZEN accounting profile")
        if batch:
            row = self._batch(db, batch)
            if row["stopped"]:
                raise ValueError("STOPPED")
            if row["state"] != "reserved":
                raise ValueError("CLOSED")

    def snapshot(self):
        with self.transaction() as db:
            budget = db.execute("SELECT * FROM budget WHERE singleton=1").fetchone()
            spent = db.execute("SELECT COALESCE(SUM(actual),0) FROM batches").fetchone()[0]
            reserved = db.execute(
                "SELECT COALESCE(SUM(MAX(0,ceiling-actual)),0) FROM batches WHERE state='reserved'"
            ).fetchone()[0]
            unknown = db.execute(
                "SELECT COALESCE(SUM(reserved),0) FROM turns WHERE state IN ('submitted','unknown')"
            ).fetchone()[0]
            return {
                "spent_micro_usd": spent,
                "reserved_micro_usd": reserved,
                "unknown_micro_usd": unknown,
                "outstanding_micro_usd": max(0, reserved - unknown),
                "active_cap_micro_usd": budget["active_cap"],
                "hard_cap_micro_usd": budget["hard_cap"],
                "frozen": bool(budget["frozen"]),
                "available_micro_usd": max(0, budget["active_cap"] - spent - reserved),
            }

    def raise_active_cap(self, new_cap, authority_ref, *, limit):
        """Raise-only cumulative cap change bound to one recorded authority digest.

        Spend, reservations, unknown turns and their identities are never touched.
        """
        money(new_cap)
        money(limit)
        if type(authority_ref) is not str or not re.fullmatch(r"[0-9a-f]{64}", authority_ref):
            raise ValueError("INVALID cap authority")
        with self.transaction() as db:
            self._writable(db)
            previous = db.execute(
                "SELECT * FROM cap_changes WHERE authority_ref=?", (authority_ref,)
            ).fetchone()
            old, hard = db.execute(
                "SELECT active_cap, hard_cap FROM budget WHERE singleton=1"
            ).fetchone()
            if previous:
                if previous["new_cap"] != new_cap or old != new_cap:
                    raise ValueError("CONFLICT cap authority")
                return dict(previous)
            if new_cap <= old or new_cap > min(limit, hard):
                raise ValueError("INVALID raise-only cap change")
            row = (authority_ref, old, new_cap, datetime.now(UTC).isoformat())
            db.execute("INSERT INTO cap_changes VALUES(?,?,?,?)", row)
            db.execute("UPDATE budget SET active_cap=? WHERE singleton=1", (new_cap,))
            fields = ["authority_ref", "old_cap", "new_cap", "recorded_at_utc"]
            return dict(zip(fields, row, strict=True))

    def reserve(self, batch, fingerprint, ceiling):
        money(ceiling)
        if not batch or not fingerprint or ceiling == 0:
            raise ValueError("INVALID batch")
        with self.transaction() as db:
            self._writable(db)
            previous = db.execute("SELECT * FROM batches WHERE id=?", (batch,)).fetchone()
            if previous:
                if (previous["fingerprint"], previous["ceiling"]) != (fingerprint, ceiling):
                    raise ValueError("CONFLICT batch")
                return
            if self._uncertain(db, batch):
                raise ValueError("UNKNOWN original turn must reconcile")
            total = db.execute(
                "SELECT COALESCE(SUM(CASE WHEN state='reserved' THEN MAX(ceiling,actual) "
                "ELSE actual END),0) FROM batches"
            ).fetchone()[0]
            cap = db.execute("SELECT MIN(active_cap,hard_cap) FROM budget").fetchone()[0]
            if total + ceiling > cap:
                raise ValueError("BUDGET_EXHAUSTED")
            db.execute(
                "INSERT INTO batches(id,fingerprint,ceiling) VALUES(?,?,?)",
                (batch, fingerprint, ceiling),
            )

    def begin(self, batch, turn, fingerprint, ceiling, *, max_turns=12):
        money(ceiling)
        if type(max_turns) is not int or not 1 <= max_turns <= 12:
            raise ValueError("INVALID turn limit")
        with self.transaction() as db:
            self._writable(db, batch)
            old = db.execute("SELECT * FROM turns WHERE batch=? AND id=?", (batch, turn)).fetchone()
            if old:
                if (old["fingerprint"], old["reserved"]) != (fingerprint, ceiling):
                    raise ValueError("CONFLICT turn")
                return
            if self._uncertain(db, batch):
                raise ValueError("UNKNOWN prior turn")
            count = db.execute("SELECT COUNT(*) FROM turns WHERE batch=?", (batch,)).fetchone()[0]
            if count >= max_turns:
                raise ValueError("TURN_LIMIT")
            row = self._batch(db, batch)
            if row["actual"] + ceiling > row["ceiling"]:
                raise ValueError("BUDGET_EXHAUSTED batch")
            db.execute(
                "INSERT INTO turns(batch,id,fingerprint,reserved,state) VALUES(?,?,?,?,'intended')",
                (batch, turn, fingerprint, ceiling),
            )

    def submit(self, batch, turn):
        with self.transaction() as db:
            self._writable(db, batch)
            changed = db.execute(
                "UPDATE turns SET state='submitted' WHERE batch=? AND id=? AND state='intended'",
                (batch, turn),
            ).rowcount
            if changed != 1:
                raise ValueError("UNKNOWN cannot redispatch")

    def observe(self, batch, turn, actual, result, usage):
        money(actual)
        overrun = False
        with self.transaction() as db:
            row = db.execute("SELECT * FROM turns WHERE batch=? AND id=?", (batch, turn)).fetchone()
            if row is None or row["state"] not in {"submitted", "unknown"}:
                raise ValueError("CONFLICT observation")
            overrun = actual > row["reserved"]
            db.execute(
                "UPDATE turns SET state='observed',actual=?,result=?,usage=? "
                "WHERE batch=? AND id=?",
                (actual, json.dumps(result), json.dumps(usage), batch, turn),
            )
            db.execute("UPDATE batches SET actual=actual+? WHERE id=?", (actual, batch))
            if overrun:
                db.execute("UPDATE budget SET frozen=1 WHERE singleton=1")
        if overrun:
            raise ValueError("USAGE_OVER_BOUND accounting frozen")

    def mark_unknown(self, batch, turn):
        with self.transaction() as db:
            db.execute(
                "UPDATE turns SET state='unknown' WHERE batch=? AND id=? AND state='submitted'",
                (batch, turn),
            )

    def record_provider(self, batch, turn, record):
        """Append an immutable signed receipt/closed failure before normalizing output."""
        encoded = json.dumps(record, sort_keys=True)
        if len(encoded.encode()) > 4096:
            raise ValueError("INVALID diagnostic size")
        with self.transaction() as db:
            row = db.execute(
                "SELECT state FROM turns WHERE batch=? AND id=?", (batch, turn)
            ).fetchone()
            if row is None or row["state"] not in {"intended", "submitted"}:
                raise ValueError("CONFLICT diagnostic identity")
            db.execute("INSERT INTO provider_observations VALUES(?,?,?)", (batch, turn, encoded))

    def abort_intended(self, batch, turn):
        with self.transaction() as db:
            changed = db.execute(
                "UPDATE turns SET state='failed' WHERE batch=? AND id=? AND state='intended'",
                (batch, turn),
            ).rowcount
            if changed != 1:
                raise ValueError("UNKNOWN submitted intent cannot be erased")

    def turn(self, batch, turn):
        with self.transaction() as db:
            row = db.execute("SELECT * FROM turns WHERE batch=? AND id=?", (batch, turn)).fetchone()
            if row is None:
                raise ValueError("NOT_FOUND turn")
            result = dict(row)
            for key in ["result", "usage"]:
                result[key] = json.loads(result[key]) if result[key] else None
            observation = db.execute(
                "SELECT record FROM provider_observations WHERE batch=? AND turn=?", (batch, turn)
            ).fetchone()
            result["provider_observation"] = json.loads(observation[0]) if observation else None
            return result

    def stop(self, batch):
        with self.transaction() as db:
            self._batch(db, batch)
            db.execute("UPDATE batches SET stopped=1 WHERE id=?", (batch,))

    def freeze(self):
        with self.transaction() as db:
            db.execute("UPDATE budget SET frozen=1 WHERE singleton=1")

    def check(self, batch):
        with self.transaction() as db:
            self._writable(db, batch)

    def close(self, batch):
        with self.transaction() as db:
            self._batch(db, batch)
            pending = db.execute(
                "SELECT 1 FROM turns WHERE batch=? AND state IN ('intended','submitted','unknown')",
                (batch,),
            ).fetchone()
            if pending:
                raise ValueError("UNKNOWN reservation retained")
            db.execute("UPDATE batches SET state='closed' WHERE id=?", (batch,))
