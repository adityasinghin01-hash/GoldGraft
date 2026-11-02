import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from goldgraft_foundation.ledger import Ledger
from goldgraft_foundation.tracker import (
    ARROWS,
    STAGES,
    IllegalTransition,
    StageResult,
    StepTracker,
)
from sqlalchemy import select

PRODUCER = {"kind": "service", "name": "test", "version": "1"}
ACTOR = {"kind": "service", "name": "tracker"}


@pytest.fixture
def ledger(tmp_path):
    return Ledger(f"sqlite:///{tmp_path / 'ledger.sqlite'}")


def seed(ledger, stage, graft="g1", attempt=1):
    # A synthetic source stage isolates arrow tests from path setup.
    return ledger.append(graft, "STAGE", PRODUCER, "StageChange/1", payload=dict(
        graft_id=graft, from_stage=None, to_stage=stage, attempt=attempt,
        reason="Test source", actor=ACTOR, evidence_refs=[]))


def decision(ledger, source, target, graft="g1"):
    return ledger.append(graft, "SWITCH", PRODUCER, "HealDecision/1", payload=dict(
        graft_id=graft, from_stage_pct=source, to_stage_pct=target, action="STEP_UP",
        reason="Fake deterministic promotion", stats=dict(n_new=30, n_old=30,
            success_new=30, success_old=30, prob_new_not_worse=1, threshold=1)))


@pytest.mark.parametrize("source,target", sorted((a, b) for a, bs in ARROWS.items() for b in bs))
def test_every_allowed_arrow(ledger, source, target):
    seed(ledger, source)
    tracker = StepTracker(ledger)
    if target == "MERGED":
        tracker.record_consent("g1", "merchant-action-1")
    percentages = {"SHADOW": 0, "HEAL_1": 1, "HEAL_10": 10, "HEAL_50": 50, "LIVE_100": 100}
    if source in percentages and target in percentages:
        decision(ledger, percentages[source], percentages[target])
    tracker.transition("g1", target, reason="Test transition")
    assert tracker.current_stage("g1") == target
    assert ledger.verify_chain("g1").ok


@pytest.mark.parametrize("source,target", sorted(
    (a, b) for a in STAGES for b in STAGES if b not in ARROWS[a] and b != "FAILED"))
def test_illegal_arrows(ledger, source, target):
    seed(ledger, source)
    tracker = StepTracker(ledger)
    with pytest.raises(IllegalTransition):
        tracker.transition("g1", target, reason="Invalid")
    assert len(ledger.read("g1")) == 1


@pytest.mark.parametrize("stage", sorted(STAGES))
def test_any_stage_can_dead_letter(ledger, stage):
    seed(ledger, stage)
    tracker = StepTracker(ledger)
    tracker.transition("g1", "FAILED", reason="Dead-letter reason")
    assert tracker.current_stage("g1") == "FAILED"


def test_repair_rounds_are_bounded(ledger):
    seed(ledger, "PROVING")
    tracker = StepTracker(ledger)
    for _ in range(2):
        tracker.transition("g1", "REPAIRING", reason="Repair")
        tracker.transition("g1", "PROVING", reason="Repaired")
    with pytest.raises(IllegalTransition, match="repair"):
        tracker.transition("g1", "REPAIRING", reason="Too many repairs")
    StepTracker(ledger, max_repair_rounds=3).transition("g1", "REPAIRING", reason="Configured")


def test_heal_and_consent_guards_need_fresh_matching_evidence(ledger):
    decision(ledger, 1, 10)
    seed(ledger, "HEAL_1")
    tracker = StepTracker(ledger)
    with pytest.raises(IllegalTransition, match="STEP_UP"):
        tracker.transition("g1", "HEAL_10", reason="Stale evidence")
    decision(ledger, 10, 50)
    with pytest.raises(IllegalTransition):
        tracker.transition("g1", "HEAL_10", reason="Wrong step")
    fresh = decision(ledger, 1, 10)
    step = tracker.transition("g1", "HEAL_10", reason="Safe")
    assert fresh.entry_hash in step.payload["evidence_refs"]
    seed(ledger, "PR_OPEN", graft="consent")
    with pytest.raises(IllegalTransition, match="consent"):
        tracker.transition("consent", "MERGED", reason="No consent")
    tracker.record_consent("consent", "merchant-click-123")
    tracker.transition("consent", "MERGED", reason="Consent captured")


def test_worker_crash_resume_is_atomic(ledger):
    tracker = StepTracker(ledger, backoff_base=0)
    tracker.start("g1")
    calls = []
    def crash(ctx):
        calls.append(ctx.idempotency_key)
        raise RuntimeError("Crash mid-stage")
    tracker.register("CREATED", crash)
    assert tracker.run_once("g1") is None
    assert len(ledger.read("g1")) == 1
    resumed = StepTracker(ledger, backoff_base=0)
    def success(ctx):
        calls.append(ctx.idempotency_key)
        return StageResult("GATED", "Recovered", [("Money/1", {"minor": 1, "currency": "USD"})])
    resumed.register("CREATED", success)
    resumed.run_once("g1")
    assert calls[0] == calls[1]
    assert resumed.current_stage("g1") == "GATED"
    assert len(ledger.read("g1")) == 3
    assert resumed.run_once("g1") is None
    assert ledger.verify_chain("g1").ok


def test_reentry_attempts_and_cutback(ledger):
    seed(ledger, "HEAL_50")
    tracker = StepTracker(ledger)
    tracker.transition("g1", "CUTBACK", reason="Fault")
    tracker.transition("g1", "GRAFTED", reason="Fixed")
    tracker.transition("g1", "PROVING", reason="Reprove")
    tracker.transition("g1", "REPAIRING", reason="Repair")
    entry = tracker.transition("g1", "PROVING", reason="Retry")
    assert entry.payload["attempt"] == 2


def test_timeout_durable_backoff_and_retry_limit(ledger):
    import threading
    now = [100.0]
    release = threading.Event()
    tracker = StepTracker(ledger, timeout=0.01, max_retries=1, backoff_base=2,
                          clock=lambda: now[0], jitter=lambda: 0.5)
    tracker.start("g1")
    tracker.register("CREATED", lambda ctx: release.wait(1))
    try:
        assert tracker.run_once("g1") is None
        with ledger.engine.connect() as conn:
            row = conn.execute(select(tracker.runs)).mappings().one()
        assert row["failures"] == 1
        assert row["retry_at"] == 102
        resumed = StepTracker(ledger, timeout=0.01, max_retries=1, backoff_base=2,
                              clock=lambda: now[0], jitter=lambda: 0.5)
        resumed.register("CREATED", lambda ctx: release.wait(1))
        assert resumed.run_once("g1") is None
        assert resumed.current_stage("g1") == "CREATED"
        now[0] = 103
        resumed.run_once("g1")
        assert resumed.current_stage("g1") == "FAILED"
        assert "TimeoutError" in ledger.read("g1")[-1].payload["reason"]
    finally:
        release.set()


def test_concurrent_workers_do_not_duplicate(ledger):
    import threading
    ready, release = threading.Event(), threading.Event()
    tracker = StepTracker(ledger)
    tracker.start("g1")
    def worker(ctx):
        ready.set()
        assert release.wait(3)
        return StageResult("GATED", "Done", [("Money/1", {"minor": 1, "currency": "USD"})])
    tracker.register("CREATED", worker)
    other = StepTracker(ledger)
    other.register("CREATED", worker)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(tracker.run_once, "g1")
        assert ready.wait(3)
        assert other.run_once("g1") is None
        release.set()
        future.result()
    assert len(ledger.read("g1")) == 3


def test_demo_runs_end_to_end(tmp_path):
    from goldgraft_foundation.demo import run_demo
    ledger = Ledger(f"sqlite:///{tmp_path / 'demo.sqlite'}")
    output = tmp_path / "demo.jsonl"
    run_demo(ledger, "demo-1", output=output)
    payloads = [json.loads(line) for line in output.read_text().splitlines()]
    stages = [e["payload"]["to_stage"] for e in payloads if e["type"] == "STAGE"]
    assert stages[0] == "CREATED" and stages[-1] == "DONE"
    assert stages.count("REPAIRING") == 1
    assert stages.count("CUTBACK") == 1
    assert stages.count("GRAFTED") == 2
    assert ledger.verify_chain("demo-1").ok
    first = output.read_bytes()
    run_demo(ledger, "demo-1", output=output)
    assert output.read_bytes() == first
