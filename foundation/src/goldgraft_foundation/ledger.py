"""Append-only per-graft ledger, SQLAlchemy Core (SQLite or Postgres).

canonical JSON: sorted keys, no whitespace, UTF-8; finite floats are allowed and
written with Python's shortest round-trip repr (NaN/Infinity rejected). Money is
still integer-only: the formats reject float money before anything is stored.
Floats are needed for probabilities, confidences and USD usage costs.
payload_hash = sha256(canonical(payload)), or sha256(referenced blob bytes).
entry_hash = sha256(prev_hash + "|" + payload_hash + "|" + type + "|" +
                    canonical(producer) + "|" + str(seq)).

The formula does not cover all envelope fields, nor guarantee global uniqueness
across grafts. A separate stored checksum detects edits to the full envelope.
Neither hash is a signature against a database administrator rewriting history.
"""

import asyncio
import hashlib
import json
import math
import os
from collections.abc import AsyncIterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.common import Producer
from goldgraft_contracts.ledger import INLINE_LIMIT_BYTES, EntryType, LedgerEntry
from goldgraft_contracts.registry import validate
from sqlalchemy import (
    Column,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    select,
    text,
)
from sqlalchemy.engine import make_url

from .blobs import BlobStore, LocalBlobStore

GENESIS = "0" * 64
metadata = MetaData()
entries = Table(
    "graft_ledger", metadata,
    Column("graft_id", String, primary_key=True),
    Column("seq", Integer, primary_key=True),
    Column("entry_hash", String(64), nullable=False),
    Column("idempotency_key", String),
    Column("body", Text, nullable=False),
    Column("envelope_hash", String(64), nullable=False),
    UniqueConstraint("graft_id", "idempotency_key"),
    Index("ix_graft_ledger_hash", "entry_hash"),
)
# Coordination only: stage truth always comes from the ledger.
step_runs = Table(
    "graft_step_runs", metadata,
    Column("graft_id", String, primary_key=True),
    Column("stage", String, primary_key=True),
    Column("attempt", Integer, primary_key=True),
    Column("failures", Integer, nullable=False, default=0),
    Column("retry_at", Float, nullable=False, default=0),
    Column("lease_owner", String),
    Column("lease_until", Float, nullable=False, default=0),
)


class SchemaRejected(ValueError):
    """Payload/envelope rejected; transaction stores nothing."""


class AmbiguousHash(LookupError):
    """Required hash formula can produce the same hash in different grafts."""


@dataclass(frozen=True)
class ChainCheck:
    ok: bool
    first_bad_seq: int | None = None
    reason: str | None = None


def canonical(value) -> bytes:
    def check(node):
        if node is None or type(node) in (str, int, bool):
            return
        if type(node) is float:
            if math.isfinite(node):
                return
            raise ValueError("canonical JSON rejects NaN and Infinity")
        if isinstance(node, list):
            for child in node:
                check(child)
            return
        if isinstance(node, dict) and all(isinstance(key, str) for key in node):
            for child in node.values():
                check(child)
            return
        raise ValueError("canonical JSON permits only JSON values")
    check(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entry_digest(prev_hash, payload_hash, type, producer, seq):
    who = canonical(producer).decode()
    return digest(f"{prev_hash}|{payload_hash}|{type}|{who}|{seq}".encode())


class LedgerTransaction:
    """A graft-locked transaction; rollback includes every append in the batch."""

    def __init__(self, ledger, conn, graft_id):
        self.ledger, self.conn, self.graft_id = ledger, conn, graft_id

    def rows(self):
        return self.conn.execute(select(entries).where(
            entries.c.graft_id == self.graft_id).order_by(entries.c.seq)).mappings().all()

    def read(self):
        return [self.ledger._decode(row) for row in self.rows()]

    def append(self, type, producer, schema, payload=None, payload_ref=None,
               inputs=None, idempotency_key=None):
        if idempotency_key is not None:
            existing = self.conn.execute(select(entries).where(
                entries.c.graft_id == self.graft_id,
                entries.c.idempotency_key == idempotency_key)).mappings().first()
            if existing:
                return self.ledger._decode(existing)
        try:
            if payload_ref is not None and payload is not None:
                raise ValueError("exactly one of payload or payload_ref is required")
            raw = self.ledger.blob_store.get(payload_ref) if payload_ref is not None else None
            resolved = json.loads(raw) if raw is not None else payload
            body_bytes = canonical(resolved)
            if raw is None and len(body_bytes) > INLINE_LIMIT_BYTES:
                raise ValueError("inline payload exceeds 16 KB; use BlobStore and payload_ref")
            # Context is local evidence only; no network/storage I/O in contracts.
            context = {"ledger_entries": {row["entry_hash"]: json.loads(row["body"])
                                           for row in self.rows()}}
            validate(schema, resolved, context=context)
            producer = Producer.model_validate(producer).model_dump(mode="json")
            last = self.conn.execute(select(entries).where(
                entries.c.graft_id == self.graft_id).order_by(entries.c.seq.desc())
                .limit(1)).mappings().first()
            seq = last["seq"] + 1 if last else 1
            prev = last["entry_hash"] if last else GENESIS
            phash = digest(raw if raw is not None else body_bytes)
            body = dict(seq=seq, graft_id=self.graft_id, ts=datetime.now(UTC).isoformat(),
                        type=type, producer=producer, inputs=list(inputs or []), schema=schema,
                        payload_hash=phash, prev_hash=prev,
                        entry_hash=entry_digest(prev, phash, type, producer, seq))
            body["payload_ref" if raw is not None else "payload"] = (
                payload_ref if raw is not None else resolved)
            result = LedgerEntry.model_validate(body, context=context)
            body = result.model_dump(mode="json")
            wire = canonical(body)
        except (ValueError, TypeError, OSError) as exc:
            raise SchemaRejected(str(exc)) from exc
        self.conn.execute(entries.insert().values(
            graft_id=self.graft_id, seq=seq, entry_hash=result.entry_hash,
            idempotency_key=idempotency_key, body=wire.decode(), envelope_hash=digest(wire)))
        return result


class Ledger:
    entries = entries

    def __init__(self, database_url=None, *, blob_store: BlobStore | None = None,
                 poll_interval: float = 0.1):
        url = make_url(database_url or os.environ.get("DATABASE_URL") or
                       "sqlite:///.goldgraft/ledger.sqlite")
        if url.drivername in ("postgres", "postgresql"):
            url = url.set(drivername="postgresql+psycopg")
        if url.get_backend_name() == "sqlite" and url.database not in (None, "", ":memory:"):
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        args = {"connect_args": {"timeout": 60, "check_same_thread": False}} if (
            url.get_backend_name() == "sqlite") else {}
        self.engine = create_engine(url, **args)
        metadata.create_all(self.engine)
        self.blob_store = blob_store if blob_store is not None else LocalBlobStore()
        self.poll_interval = poll_interval

    @contextmanager
    def transaction(self, graft_id):
        with self.engine.connect() as conn:
            try:
                if self.engine.dialect.name == "sqlite":
                    conn.exec_driver_sql("BEGIN IMMEDIATE")
                else:
                    # Stable signed 64-bit transaction lock, including empty chains.
                    key = int.from_bytes(hashlib.sha256(graft_id.encode()).digest()[:8],
                                         "big", signed=True)
                    conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
                yield LedgerTransaction(self, conn, graft_id)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def append(self, graft_id, type, producer, schema, payload=None, payload_ref=None,
               inputs=None, idempotency_key=None) -> LedgerEntry:
        with self.transaction(graft_id) as tx:
            return tx.append(type, producer, schema, payload, payload_ref, inputs, idempotency_key)

    def _decode(self, row):
        # model_construct bypasses validation on read: provenance-bearing payloads
        # were validated on write, and verify_chain performs the integrity audit.
        body = json.loads(row["body"])
        body["producer"] = Producer.model_validate(body["producer"])
        body["type"] = EntryType(body["type"])
        body["ts"] = datetime.fromisoformat(body["ts"].replace("Z", "+00:00"))
        body["schema_"] = body.pop("schema")
        return LedgerEntry.model_construct(**body)

    def read(self, graft_id, after_seq=0) -> list[LedgerEntry]:
        with self.engine.connect() as conn:
            rows = conn.execute(select(entries).where(
                entries.c.graft_id == graft_id, entries.c.seq > after_seq)
                .order_by(entries.c.seq)).mappings().all()
        return [self._decode(row) for row in rows]

    def get(self, entry_hash, *, graft_id=None):
        query = select(entries).where(entries.c.entry_hash == entry_hash)
        if graft_id is not None:
            query = query.where(entries.c.graft_id == graft_id)
        with self.engine.connect() as conn:
            rows = conn.execute(query.limit(2)).mappings().all()
        if len(rows) > 1:
            raise AmbiguousHash("hash occurs in multiple grafts; pass graft_id")
        return self._decode(rows[0]) if rows else None

    def root_hash(self, graft_id):
        with self.engine.connect() as conn:
            return conn.execute(select(entries.c.entry_hash).where(
                entries.c.graft_id == graft_id).order_by(entries.c.seq.desc())
                .limit(1)).scalar_one_or_none() or GENESIS

    def payload(self, entry):
        if entry.payload_ref:
            return json.loads(self.blob_store.get(entry.payload_ref))
        return entry.payload

    def verify_chain(self, graft_id) -> ChainCheck:
        return self._verify_chain(graft_id)

    def verified_payloads(self, graft_id, through_hash, schema):
        """Return validated payloads from the nonempty prefix ending at a signed root."""
        payloads = []
        check = self._verify_chain(graft_id, through_hash, schema, payloads)
        return check, payloads if check.ok else []

    def _verify_chain(self, graft_id, through_hash=None, schema=None, payloads=None):
        with self.engine.connect() as conn:
            rows = conn.execute(select(entries).where(entries.c.graft_id == graft_id)
                                .order_by(entries.c.seq)).mappings().all()
        prev, context = GENESIS, {"ledger_entries": {}}
        for expected_seq, row in enumerate(rows, 1):
            try:
                body = json.loads(row["body"])
                if row["seq"] != expected_seq or body["seq"] != expected_seq:
                    raise ValueError("sequence gap or changed sequence")
                if body["graft_id"] != graft_id or body["entry_hash"] != row["entry_hash"]:
                    raise ValueError("envelope/index mismatch")
                if digest(canonical(body)) != row["envelope_hash"]:
                    raise ValueError("envelope checksum mismatch")
                if body["prev_hash"] != prev:
                    raise ValueError("previous hash mismatch")
                raw = self.blob_store.get(body["payload_ref"]) if "payload_ref" in body else None
                payload = json.loads(raw) if raw is not None else body["payload"]
                canonical_payload = canonical(payload)
                if digest(raw if raw is not None else canonical_payload) != body["payload_hash"]:
                    raise ValueError("payload hash mismatch")
                if entry_digest(prev, body["payload_hash"], body["type"], body["producer"],
                                expected_seq) != body["entry_hash"]:
                    raise ValueError("entry hash mismatch")
                validated = validate(body["schema"], payload, context=context)
                LedgerEntry.model_validate(body, context=context)
                if payloads is not None and body["schema"] == schema:
                    payloads.append(validated)
                prev = body["entry_hash"]
                context["ledger_entries"][prev] = body
                if through_hash is not None and prev == through_hash:
                    return ChainCheck(True)
            except (ValueError, TypeError, OSError, KeyError) as exc:
                reason = type(exc).__name__ + ": integrity check failed"
                return ChainCheck(False, expected_seq, reason)
        if through_hash is not None:
            return ChainCheck(False, reason="signed root not found in this graft")
        return ChainCheck(True)

    async def subscribe(self, graft_id, after_seq=0) -> AsyncIterator[LedgerEntry]:
        while True:
            batch = await asyncio.to_thread(self.read, graft_id, after_seq)
            for entry in batch:
                after_seq = entry.seq
                yield entry
            await asyncio.sleep(self.poll_interval)

    def close(self):
        self.engine.dispose()
