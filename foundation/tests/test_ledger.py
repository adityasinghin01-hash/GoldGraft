import asyncio
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from goldgraft_foundation.blobs import LocalBlobStore
from goldgraft_foundation.ledger import GENESIS, Ledger, SchemaRejected, canonical
from sqlalchemy import select, update

PRODUCER = {"kind": "service", "name": "test", "version": "1"}


@pytest.fixture
def ledger(tmp_path):
    return Ledger(f"sqlite:///{tmp_path / 'ledger.sqlite'}",
                  blob_store=LocalBlobStore(tmp_path / "blobs"))


def append(ledger, **kwargs):
    return ledger.append("g1", "ARTIFACT", PRODUCER, "Money/1",
                         payload={"minor": 123, "currency": "USD"}, **kwargs)


def test_append_read_hash_and_idempotency(ledger):
    first = append(ledger, idempotency_key="first")
    assert first.prev_hash == GENESIS
    assert first.seq == 1
    digest = hashlib.sha256(canonical({"minor": 123, "currency": "USD"})).hexdigest()
    expected = hashlib.sha256(
        f'{GENESIS}|{digest}|ARTIFACT|{canonical(PRODUCER).decode()}|1'.encode()
    ).hexdigest()
    assert first.entry_hash == expected
    assert append(ledger, idempotency_key="first") == first
    second = append(ledger)
    assert second.prev_hash == first.entry_hash
    assert ledger.read("g1", after_seq=1) == [second]
    assert ledger.get(first.entry_hash) == first
    assert ledger.get("f" * 64) is None
    assert ledger.root_hash("g1") == second.entry_hash
    assert ledger.root_hash("empty") == GENESIS
    assert ledger.verify_chain("g1").ok


@pytest.mark.parametrize("field,value", [
    ("payload", {"minor": 124, "currency": "USD"}), ("type", "MESSAGE"),
    ("producer", {**PRODUCER, "name": "evil"}), ("graft_id", "g2"),
    ("ts", "2025-01-01T00:00:00Z"), ("schema", "Other/1"),
    ("inputs", ["e" * 64]), ("seq", 99), ("prev_hash", "e" * 64),
    ("payload_hash", "e" * 64), ("entry_hash", "e" * 64), ("payload_ref", "blob://evil"),
])
def test_tamper_exact_sequence(ledger, field, value):
    for _ in range(3):
        append(ledger)
    table = ledger.entries
    with ledger.engine.begin() as conn:
        raw = conn.execute(select(table.c.body).where(table.c.seq == 2)).scalar_one()
        body = json.loads(raw)
        body[field] = value
        conn.execute(update(table).where(table.c.seq == 2).values(body=json.dumps(body)))
    check = ledger.verify_chain("g1")
    assert not check.ok
    assert check.first_bad_seq == 2
    assert check.reason


def test_schema_rejection_size_and_float(ledger):
    for schema, payload in [("Money/1", {"minor": 1.2, "currency": "USD"}),
                            ("Missing/1", {}),
                            ("Money/1", {"minor": 1, "currency": "ZZZ"})]:
        with pytest.raises(SchemaRejected):
            ledger.append("g1", "ARTIFACT", PRODUCER, schema, payload=payload)
    payload = json.loads((Path(__file__).parents[2] /
                         "contracts/examples/RootMap.1.json").read_text())
    payload["stack"]["framework"] = "€" * 6000
    for touchpoint in payload["touchpoints"]:
        touchpoint["confidence"] = 1
    with pytest.raises(SchemaRejected, match="16"):
        ledger.append("g1", "ARTIFACT", PRODUCER, "RootMap/1", payload=payload)
    assert ledger.read("g1") == []
    ref = ledger.blob_store.put(canonical(payload))
    entry = ledger.append("g1", "ARTIFACT", PRODUCER, "RootMap/1", payload_ref=ref)
    assert entry.payload_ref == ref
    assert entry.payload_hash == hashlib.sha256(canonical(payload)).hexdigest()
    assert ledger.verify_chain("g1").ok
    ledger.blob_store.path_for(ref).write_bytes(b"broken")
    assert ledger.verify_chain("g1").first_bad_seq == 1


def test_fractional_fields_are_stored_but_float_money_is_not(ledger):
    decision = dict(graft_id="g1", from_stage_pct=1, to_stage_pct=10, action="STEP_UP",
                    reason="posterior above threshold",
                    stats=dict(n_new=40, n_old=400, success_new=39, success_old=388,
                               prob_new_not_worse=0.9731, threshold=0.95))
    entry = ledger.append("g1", "SWITCH", PRODUCER, "HealDecision/1", payload=decision)
    assert entry.payload["stats"]["prob_new_not_worse"] == 0.9731
    budget = json.loads((Path(__file__).parents[2] /
                         "contracts/examples/BudgetRecord.1.json").read_text())
    budget["usd"] = 0.0375
    ledger.append("g1", "COST", PRODUCER, "BudgetRecord/1", payload=budget)
    assert ledger.verify_chain("g1").ok
    with pytest.raises(SchemaRejected):
        ledger.append("g1", "ARTIFACT", PRODUCER, "Money/1",
                      payload={"minor": 10.5, "currency": "USD"})
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError):
            canonical({"x": bad})


def test_ten_threads_fifty_appends(ledger):
    # Independent Ledger objects/connections: no reliance on a process-local mutex.
    def writer(_):
        other = Ledger(ledger.engine.url, blob_store=ledger.blob_store)
        try:
            for _ in range(50):
                append(other)
        finally:
            other.close()
    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(writer, range(10)))
    assert [e.seq for e in ledger.read("g1")] == list(range(1, 501))
    assert ledger.verify_chain("g1").ok


def test_subscribe_catches_up_and_cancels(ledger):
    async def exercise():
        first = append(ledger)
        stream = ledger.subscribe("g1", after_seq=0)
        assert await anext(stream) == first
        task = asyncio.create_task(anext(stream))
        await asyncio.sleep(0.01)
        second = append(ledger)
        assert await asyncio.wait_for(task, 2) == second
        await stream.aclose()
    asyncio.run(exercise())
