"""Proof acceptance vectors, all C4 keys; no algorithms imported from the stand-in.

GOLDGRAFT_PROOF=pieces.proof.proof:Proof uv run pytest plugtests/test_proof.py
"""

import json

import pytest
from goldgraft_contracts.api import CertificateVerifyResult
from goldgraft_contracts.registry import validate

from .conftest import ROOT, load

PROOF = ROOT / "fixtures/proof/legacy-php-shop"
RAW = sorted((PROOF / "raw").glob("*.json"))
VERDICTS = sorted((PROOF / "expected").glob("*.verdict.json"))
HEAL = sorted((PROOF / "heal").glob("*.events.json"))
# INDEX: metadata, timing and ID vocabulary may change; money/kind/source/status/counts may not.
NOISE = {"graft_id", "run_id", "variant", "raw_ref", "t_ms",
         "pp.legacy_token", "pp.txn_id", "pp.order_id", "pp.capture_id", "pp.refund_id",
         "pp.debug_id"}


def read(path):
    return json.loads(path.read_text())


def models(schema, path):
    return [validate(schema, item) for item in read(path)]


def normalise(event):
    event = validate("CMEL/1", event).model_dump(mode="json", exclude_none=True)
    assert set(event.pop("noise")) <= NOISE, "economic fields must never be marked as noise"
    for field in NOISE:
        parent, dot, child = field.partition(".")
        if dot:
            event.get(parent, {}).pop(child, None)
        else:
            event.pop(parent, None)
    return event


@pytest.fixture(scope="module")
def proof():
    cls, _ = load("GOLDGRAFT_PROOF", "goldgraft_fakes.proof:FakeProof")
    return cls()


@pytest.mark.parametrize("path", RAW, ids=lambda p: p.stem)
def test_raw_to_cmel(proof, path):
    capture = validate("RawCapture/1", read(path))
    actual = proof.to_cmel(capture)
    expected = models("CMEL/1", PROOF / "cmel" / path.name)
    assert [normalise(e) for e in actual] == [normalise(e) for e in expected]
    # Never merge a PayPal ledger witness into the API witness or sum them together.
    assert sum(e.source == "PAYPAL_LEDGER" for e in actual) == sum(
        e.source == "PAYPAL_LEDGER" for e in expected)


@pytest.mark.parametrize("path", VERDICTS, ids=lambda p: p.stem)
def test_judge(proof, path):
    expected = validate("Verdict/1", read(path))
    streams = [models("CMEL/1", PROOF / f"cmel/{expected.scenario_id}.{v}.json")
               for v in ("OLD", "OLD_TWIN", "NEW")]
    evidence = {}
    if proof.__class__.__module__ == "pieces.proof.proof":
        for side in ("OLD", "NEW"):
            raw = read(PROOF / f"raw/{expected.scenario_id}.{side}.json")
            evidence[f"{side.lower()}_capture"] = validate("RawCapture/1", raw)
    result = validate("Verdict/1", proof.judge(
        *streams, validate("Contract/1", read(PROOF / "contract.json")),
        validate("TargetPlan/1", read(PROOF / "target_plan.json")), **evidence))
    assert result.scenario_id == expected.scenario_id
    assert result.grade == expected.grade
    assert {(hit.rule, hit.side) for hit in result.rule_hits} == {
        (hit.rule, hit.side) for hit in expected.rule_hits}
    assert bool(result.parity_diff) == bool(expected.parity_diff)


def test_proof_strength(proof):
    mutants = [validate("Mutant/1", read(p)) for p in sorted((PROOF / "mutants").glob("M*.json"))]
    rows = read(PROOF / "mutants/runs.json")["runs"]
    runs = {row["mutant"]: row["grades"] for row in rows}
    evidence = {}
    if proof.__class__.__module__ == "pieces.proof.proof":
        evidence["reviewed_equivalent"] = {
            row["mutant"] for row in rows if row["equivalence"] == "DROPPED"
        }
    actual = validate("ProofStrength/1", proof.proof_strength(mutants, runs, **evidence))
    expected = validate("ProofStrength/1", read(PROOF / "expected/proof_strength.json"))
    assert (actual.total, actual.equivalent_dropped, actual.killed) == (
        expected.total, expected.equivalent_dropped, expected.killed)
    assert actual.score == pytest.approx(expected.score, abs=1e-9, rel=0)


@pytest.mark.parametrize("path", HEAL, ids=lambda p: p.stem)
def test_heal_decisions(proof, path):
    expected = validate("HealDecision/1", read(path.with_name(
        path.name.replace(".events.", ".expected."))))
    evidence = read(path.with_name(path.name.replace(".events.", ".evidence.")))
    stops = [evidence["hard_stop"]] if evidence["hard_stop"] else []
    result = validate("HealDecision/1", proof.heal_decide(
        expected.graft_id, evidence["stage_pct"], models("GuardEvent/1", path), stops))
    assert (result.graft_id, result.from_stage_pct, result.action, result.to_stage_pct,
            result.hard_stop) == (expected.graft_id, expected.from_stage_pct, expected.action,
                                 expected.to_stage_pct, expected.hard_stop)
    for field in ("n_old", "n_new", "success_old", "success_new"):
        assert getattr(result.stats, field) == getattr(expected.stats, field)
    assert result.stats.prob_new_not_worse == pytest.approx(
        evidence["prob_new_not_worse"], abs=1e-6, rel=0)
    assert result.stats.threshold == expected.stats.threshold


@pytest.mark.parametrize("case", read(PROOF / "recipes/confidence_cases.json")["cases"],
                         ids=lambda c: f"{c['passes']}-passes-{c['fails']}-fails")
def test_recipe_confidence(proof, case):
    assert proof.recipe_confidence(case["passes"], case["fails"]) == pytest.approx(
        case["expected_mean"], abs=1e-9, rel=0)


@pytest.mark.parametrize("name", ["valid", "tampered"])
def test_certificate_hash_binding_vectors(proof, name):
    wire = read(PROOF / f"certificate/{name}.json")
    certificate = validate("Certificate/1", wire)
    expected = read(PROOF / "certificate/expected_verify.json")
    key = expected[name]
    result = CertificateVerifyResult.model_validate(proof.verify_certificate(certificate))
    assert result.cert_id == certificate.cert_id
    if proof.__class__.__module__ == "pieces.proof.proof":
        from pieces.proof.certificate import matches_payload_hash

        assert matches_payload_hash(wire, expected["trusted_payload_sha256"]) == (
            key["payload_hash_matches"]
        )
        assert not result.ok
        assert result.checks and all(not check.ok for check in result.checks)
        return
    assert result.ok == key["payload_hash_matches"]
    assert result.checks
    if not result.ok:
        # Check names are a closed enum in C3; the C4 failure code belongs in detail.
        assert any(not check.ok and key["failed_check"] in check.detail for check in result.checks)
