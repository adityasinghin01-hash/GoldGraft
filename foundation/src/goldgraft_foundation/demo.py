"""One fake cycle: repair once, cut back once, re-prove and finish; no network."""

import argparse
from pathlib import Path

from .ledger import Ledger
from .tracker import ARROWS, PERCENTAGES, StageResult, StepTracker


def run_demo(ledger, graft_id, *, output=Path("fixtures/events/demo_graft_events.jsonl")):
    tracker = StepTracker(ledger, backoff_base=0)
    tracker.start(graft_id, reason="Fake sandbox graft created")

    def worker(ctx):
        if ctx.stage == "PROVING":
            target = "REPAIRING" if ctx.attempt == 1 else "CERTIFIED"
        elif ctx.stage == "HEAL_10" and ctx.attempt == 1:
            target = "CUTBACK"
        else:
            target = {
                "SURVEYED": "BUILT", "BUILT": "RECORDED", "HEAL_10": "HEAL_50",
            }.get(ctx.stage)
            if target is None:
                target = next(iter(ARROWS[ctx.stage] - {"FAILED", "CUTBACK"}))
        artifacts = []
        if ctx.stage in PERCENTAGES and target in PERCENTAGES:
            artifacts.append(("HealDecision/1", dict(
                graft_id=ctx.graft_id, from_stage_pct=PERCENTAGES[ctx.stage],
                to_stage_pct=PERCENTAGES[target], action="STEP_UP",
                reason="FAKE demo evidence: 30 simulated successful samples",
                stats=dict(n_new=30, n_old=30, success_new=30, success_old=30,
                           prob_new_not_worse=0.99, threshold=0.95))))
        return StageResult(target, "FAKE demo worker complete", artifacts)

    for stage in ARROWS:
        tracker.register(stage, worker)
    for _ in range(100):
        stage = tracker.current_stage(graft_id)
        if stage == "DONE":
            break
        if stage == "PR_OPEN":
            tracker.record_consent(graft_id, "demo://fake-merchant-consent",
                                   reason="FAKE demo consent; no real merge or rollout")
        if tracker.run_once(graft_id) is None:
            raise RuntimeError(f"demo blocked at {stage}")
    if tracker.current_stage(graft_id) != "DONE":
        raise RuntimeError("demo did not finish")
    entries = ledger.read(graft_id)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(entry.model_dump_json() + "\n" for entry in entries))
    for entry in entries:
        print(entry.model_dump_json())
    check = ledger.verify_chain(graft_id)
    root = ledger.root_hash(graft_id)
    print(f"Chain verified: ok={check.ok}, entries={len(entries)}, root={root}")
    if not check.ok:
        raise RuntimeError(f"chain failed at {check.first_bad_seq}")
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graft", default="demo-1")
    args = parser.parse_args()
    ledger = Ledger()
    try:
        run_demo(ledger, args.graft)
    finally:
        ledger.close()


if __name__ == "__main__":
    main()
