"""Offline synthetic decision-consumer rehearsal; never proof or actual promotion."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    # Verify the actual pinned model sources before importing any team contract.
    import hashlib

    import check_shop_pack

    folder = ROOT / ".context/team-contracts"
    for name, expected in check_shop_pack.PINNED.items():
        path = folder / "goldgraft_contracts" / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("linked_contract_source")
        data = path.read_bytes()
        if hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() != expected:
            raise ValueError("pinned_model_changed")
    sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location(
        "rollout_consumer", ROOT / "pieces/switch-libs/python/rollout.py"
    )
    rollout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rollout)
    stats = {
        "n_old": 10,
        "n_new": 10,
        "success_old": 10,
        "success_new": 10,
        "prob_new_not_worse": 0.99,
        "threshold": 0.95,
    }

    def payload(old, new, action="STEP_UP"):
        return {
            "graft_id": "SYNTHETIC-REHEARSAL",
            "from_stage_pct": old,
            "to_stage_pct": new,
            "action": action,
            "reason": "synthetic test, not a real proof decision",
            "stats": copy.deepcopy(stats),
        }

    count = 0
    stage = 0
    for target in (1, 10, 50, 100):
        stage = rollout.proposed_stage(
            payload(stage, target), graft_id="SYNTHETIC-REHEARSAL", current_stage=stage
        )
        assert stage == target
        count += 1
    assert (
        rollout.proposed_stage(
            payload(100, 100, "HOLD"), graft_id="SYNTHETIC-REHEARSAL", current_stage=100
        )
        == 100
    )
    count += 1
    cutback = payload(100, 0, "CUTBACK")
    cutback["hard_stop"] = "synthetic controlled fault"
    assert rollout.proposed_stage(cutback, graft_id="SYNTHETIC-REHEARSAL", current_stage=100) == 0
    count += 1
    negatives = [
        (payload(0, 1), "wrong-graft", 0),
        (payload(0, 1), "SYNTHETIC-REHEARSAL", 1),
        (payload(0, 50), "SYNTHETIC-REHEARSAL", 0),
        ({**payload(0, 1), "hard_stop": "fault"}, "SYNTHETIC-REHEARSAL", 0),
        (payload(0, 1), "SYNTHETIC-REHEARSAL", True),
        ({**payload(0, 1), "stats": {**stats, "success_new": 11}}, "SYNTHETIC-REHEARSAL", 0),
    ]
    for value, graft, current in negatives:
        try:
            rollout.proposed_stage(value, graft_id=graft, current_stage=current)
        except ValueError:
            count += 1
        else:
            raise AssertionError("invalid_decision_accepted")
    result = {
        "status": "PASS",
        "cases": count,
        "evidence": "SYNTHETIC_CURRENT_HEALDECISION_CONSUMER",
        "decisions_applied": 0,
        "proof_math_implemented": False,
        "provider_calls": 0,
        "rollout_qualified": False,
    }
    output = ROOT / ".context/rollout-rehearsal"
    output.mkdir(parents=True, exist_ok=True)
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
