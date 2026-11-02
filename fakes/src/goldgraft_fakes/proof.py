"""C4 answer-key lookups, not an implementation of the proof algorithms.

Content must match a known vector. Caller-specific graft/run metadata is preserved;
unknown economics, contracts, plans, mutants, events or certificates raise LookupError.
"""

import json
from collections.abc import Mapping, Sequence

from goldgraft_contracts.api import CertificateVerifyResult
from goldgraft_contracts.money import MoneyEvent
from goldgraft_contracts.proof import (
    Certificate,
    Grade,
    MoneyContract,
    Mutant,
    ProofStrength,
    Verdict,
)
from goldgraft_contracts.runner import GuardEvent, HealDecision, RawCapture
from goldgraft_contracts.survey import TargetPlan

from ._fixtures import PROOF, boundary, events, read

MutantRuns = Mapping[str, Mapping[str, Grade]]


def content(model, *, omit=()):
    data = model.model_dump(mode="json")
    return {k: v for k, v in data.items() if k not in omit}


def stream(items):
    return [content(item, omit=("graft_id", "run_id")) for item in items]


def unordered(items):
    return sorted(json.dumps(content(item, omit=("graft_id",)), sort_keys=True) for item in items)


class FakeProof:
    def to_cmel(self, capture: RawCapture) -> list[MoneyEvent]:
        path = PROOF / "raw" / f"{capture.scenario_id}.{capture.variant}.json"
        # Membership in the known filenames also prevents path traversal via scenario_id.
        if path not in (PROOF / "raw").glob("*.json") or content(
            capture, omit=("graft_id", "run_id")) != content(
                boundary("RawCapture/1", path), omit=("graft_id", "run_id")):
            raise LookupError(f"No CMEL key for capture {capture.scenario_id}.{capture.variant}")
        result = events(PROOF / "cmel" / path.name, "CMEL/1")
        for event in result:
            event.graft_id, event.run_id = capture.graft_id, capture.run_id
        return result

    def judge(self, old: Sequence[MoneyEvent], old_twin: Sequence[MoneyEvent],
              new: Sequence[MoneyEvent], contract: MoneyContract,
              target_plan: TargetPlan) -> Verdict:
        if (contract != boundary("Contract/1", PROOF / "contract.json") or
                target_plan != boundary("TargetPlan/1", PROOF / "target_plan.json")):
            raise LookupError("No judge key for this contract/target plan")
        scenario = old[0].scenario_id if old else "<empty>"
        path = PROOF / "expected" / f"{scenario}.verdict.json"
        if path in (PROOF / "expected").glob("*.verdict.json"):
            for items, variant in zip(
                    (old, old_twin, new), ("OLD", "OLD_TWIN", "NEW"), strict=True):
                expected = events(PROOF / "cmel" / f"{scenario}.{variant}.json", "CMEL/1")
                if stream(items) != stream(expected):
                    break
            else:
                return boundary("Verdict/1", path)
        raise LookupError(f"No judge key for scenario/content {scenario!r}")

    def proof_strength(self, mutants: Sequence[Mutant], runs: MutantRuns) -> ProofStrength:
        known = events_from_mutants()
        expected_runs = {row["mutant"]: row["grades"]
                         for row in read(PROOF / "mutants/runs.json")["runs"]}
        if unordered(mutants) != unordered(known) or dict(runs) != expected_runs:
            raise LookupError("No proof-strength key for these mutants/runs")
        return boundary("ProofStrength/1", PROOF / "expected/proof_strength.json")

    def heal_decide(self, graft_id: str, stage_pct: int, events: Sequence[GuardEvent],
                    hard_stops: Sequence[str] = ()) -> HealDecision:
        for path in sorted((PROOF / "heal").glob("*.events.json")):
            evidence = read(path.with_name(path.name.replace(".events.", ".evidence.")))
            stops = [evidence["hard_stop"]] if evidence["hard_stop"] else []
            if (stage_pct == evidence["stage_pct"] and sorted(hard_stops) == sorted(stops)
                    and unordered(events) == unordered(load_guard_events(path))):
                result = boundary("HealDecision/1", path.with_name(
                    path.name.replace(".events.", ".expected.")))
                result.graft_id = graft_id
                return result
        raise LookupError("No heal key for this stage/events/hard-stop evidence")

    def recipe_confidence(self, passes: int, fails: int) -> float:
        if type(passes) is not int or type(fails) is not int or min(passes, fails) < 0:
            raise ValueError("passes and fails must be nonnegative integers")
        return (passes + 1) / (passes + fails + 2)

    def verify_certificate(self, certificate: Certificate) -> CertificateVerifyResult:
        for name in ("valid", "tampered"):
            if certificate == boundary("Certificate/1", PROOF / f"certificate/{name}.json"):
                key = read(PROOF / "certificate/expected_verify.json")[name]
                ok = key["payload_hash_matches"]
                detail = ("Synthetic schema/hash-binding vector only; signature unverified; "
                          "not eligible for certification" if ok else key["failed_check"])
                return CertificateVerifyResult.model_validate({
                    "cert_id": certificate.cert_id, "ok": ok,
                    "checks": [{"name": "SIGNATURE", "ok": ok, "detail": detail}]})
        raise LookupError(f"No certificate key for content of {certificate.cert_id!r}")


def events_from_mutants():
    return [boundary("Mutant/1", path) for path in sorted((PROOF / "mutants").glob("M*.json"))]


def load_guard_events(path):
    return events(path, "GuardEvent/1")
