"""Run GoldGraft's offline proof examples and print the actual decisions."""

import json
from pathlib import Path

from goldgraft_contracts.registry import validate

from pieces.proof.certificate import matches_payload_hash
from pieces.proof.proof import Proof

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/proof/legacy-php-shop"


def read(path):
    return json.loads((FIXTURES / path).read_text())


def model(schema, path):
    return validate(schema, read(path))


def main():
    proof = Proof()
    contract = model("Contract/1", "contract.json")
    plan = model("TargetPlan/1", "target_plan.json")
    print("SYNTHETIC fixtures, real proof implementation")
    for path in sorted((FIXTURES / "expected").glob("*.verdict.json")):
        scenario = path.name.removesuffix(".verdict.json")
        old, twin, new = [
            model("RawCapture/1", f"raw/{scenario}.{variant}.json")
            for variant in ("OLD", "OLD_TWIN", "NEW")
        ]
        streams = [proof.to_cmel(capture) for capture in (old, twin, new)]
        result = proof.judge(*streams, contract, plan, old_capture=old, new_capture=new)
        hits = ",".join(f"{hit.side}/{hit.rule}" for hit in result.rule_hits) or "-"
        print(f"{scenario}: {result.grade} | hits={hits} | CMEL={list(map(len, streams))}")
        if scenario == "HAPPY":
            print(f"  masked={','.join(result.noise_masked)}")
            print(f"  allowed={','.join(result.deltas_applied)}")
            na = proof.judge(
                *streams,
                contract,
                plan,
                not_applicable_reason="Feature disabled for this shop",
            )
            print(f"  explicit applicability decision: {na.grade}")

    rows = read("mutants/runs.json")["runs"]
    mutants = [model("Mutant/1", f"mutants/{row['mutant']}.json") for row in rows]
    runs = {row["mutant"]: row["grades"] for row in rows}
    equivalents = {row["mutant"] for row in rows if row["equivalence"] == "DROPPED"}
    strength = proof.proof_strength(mutants, runs, reviewed_equivalent=equivalents)
    survivors = [
        mid
        for mid, grades in runs.items()
        if mid not in equivalents and "PROBLEM" not in grades.values()
    ]
    print(f"Fixture-only mutation outcomes: {strength.killed}/{strength.total - len(equivalents)}")
    print(f"  reviewed equivalent={','.join(sorted(equivalents))}, survivors={','.join(survivors)}")

    for path in sorted((FIXTURES / "heal").glob("*.events.json")):
        name = path.name.removesuffix(".events.json")
        events = [validate("GuardEvent/1", row) for row in read(f"heal/{path.name}")]
        evidence = read(f"heal/{name}.evidence.json")
        expected = read(f"heal/{name}.expected.json")
        args = expected["graft_id"], evidence["stage_pct"]
        stops = [evidence["hard_stop"]] if evidence["hard_stop"] else []
        decision = proof.heal_decide(*args, events, stops)
        print(
            f"{name}: {decision.action} -> {decision.to_stage_pct}% "
            f"(p={decision.stats.prob_new_not_worse:.6f})"
        )
        if name == "case_healthy":
            assert proof.heal_decide(*args, events + events) == decision
            full_stage = proof.heal_decide(args[0], 100, events)
            print(f"  duplicates unchanged, full stage={full_stage.action}")

    print(f"Recipe (3 pass, 2 fail): {proof.recipe_confidence(3, 2):.6f}")
    try:
        proof.recipe_confidence(-1, 2)
    except ValueError as error:
        print(f"Recipe rejected: {error}")

    trusted = read("certificate/expected_verify.json")["trusted_payload_sha256"]
    for name in ("valid", "tampered"):
        wire = read(f"certificate/{name}.json")
        checked = proof.verify_certificate(validate("Certificate/1", wire))
        print(
            f"Certificate {name}: hash={matches_payload_hash(wire, trusted)}, verified={checked.ok}"
        )


if __name__ == "__main__":
    main()
