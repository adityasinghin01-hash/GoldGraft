"""Exercise isolated patch application and checkout behavior without network calls."""

import json
import os
import shutil
import subprocess

import pytest
from goldgraft_contracts.proof import Grade
from goldgraft_contracts.registry import validate

from pieces.proof.mutation import apply_mutant, run_mutants
from pieces.proof.proof import Proof

from .conftest import ROOT

FIXTURE = ROOT / "fixtures/proof/legacy-php-shop"


def test_all_mutants_apply_to_independent_source_and_run_linked_scenarios():
    mutants = [
        validate("Mutant/1", json.loads(path.read_text()))
        for path in sorted((FIXTURE / "mutants").glob("M*.json"))
    ]
    sources = {
        mutant.location.file: (FIXTURE / mutant.location.file).read_text() for mutant in mutants
    }
    calls = []

    def run(mutant, patched, scenario):
        original = sources[mutant.location.file]
        line = mutant.location.line - 1
        assert patched.splitlines()[line] != original.splitlines()[line]
        calls.append((mutant.id, scenario))
        return Grade.PASS

    results = run_mutants(mutants, sources, {mutant.rule: ["linked"] for mutant in mutants}, run)
    assert len(calls) == 12
    assert results == {mutant.id: {"linked": Grade.PASS} for mutant in mutants}
    with pytest.raises(ValueError, match="context mismatch"):
        apply_mutant("\n" * 100, mutants[0])


def test_php_checkout_mutation_outcomes(tmp_path):
    php = os.environ.get("GOLDGRAFT_PHP") or shutil.which("php")
    if not php:
        pytest.skip("PHP CLI is required for executable checkout mutations")

    cases = (
        ("WRONG_CURRENCY", Grade.PROBLEM),
        ("PENDING", Grade.PROBLEM),
        ("UNAPPROVED", Grade.PASS),
        ("LOCKED_CAPTURE", Grade.PROBLEM),
        ("LOST_RESPONSE", Grade.PROBLEM),
        ("EXACT_AMOUNT", Grade.PROBLEM),
        ("BROWSER_QUOTE", Grade.PROBLEM),
        ("FORGED_WEBHOOK", Grade.PROBLEM),
        ("VALID_WEBHOOK", Grade.UNVERIFIED),
        ("MIXED_CASE_WEBHOOK", Grade.PROBLEM),
        ("DURABLE_APPROVAL", Grade.PROBLEM),
        ("REFUND_TWICE", Grade.PROBLEM),
    )
    sample = FIXTURE / "new_sample/payments.php"
    harness = ROOT / "plugtests/proof_support/mutation_harness.php"

    def execute(source, scenario):
        result = subprocess.run(
            [php, "-n", "-d", "display_errors=stderr", str(harness), str(source), scenario],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert result.returncode == 0, f"{scenario}: {result.stderr}"
        return Grade(result.stdout.strip())

    for scenario, _ in cases:
        assert execute(sample, scenario) == Grade.PASS, scenario

    mutants = [
        validate("Mutant/1", json.loads((FIXTURE / f"mutants/M{index:02}.json").read_text()))
        for index in range(1, len(cases) + 1)
    ]

    def run(mutant, patched, scenario):
        source = tmp_path / f"{mutant.id}.php"
        source.write_text(patched)
        return execute(source, scenario)

    linked = {}
    for mutant, (scenario, _) in zip(mutants, cases, strict=True):
        linked.setdefault(mutant.rule, []).append(scenario)
    results = run_mutants(mutants, {mutants[0].location.file: sample.read_text()}, linked, run)
    for mutant, (scenario, expected) in zip(mutants, cases, strict=True):
        assert results[mutant.id][scenario] == expected, mutant.id
    strength = Proof().proof_strength(mutants, results)
    assert (strength.killed, strength.total) == (10, 12)


def test_proof_strength_requires_outcomes_and_verified_equivalence():
    mutant = validate("Mutant/1", json.loads((FIXTURE / "mutants/M03.json").read_text()))
    proof = Proof()

    with pytest.raises(ValueError, match="at least one scenario"):
        proof.proof_strength([mutant], {mutant.id: {}})
    with pytest.raises(ValueError, match="must agree"):
        proof.proof_strength([mutant], {mutant.id: {"example": Grade.PASS}, "extra": {}})

    inconclusive = {mutant.id: {"example": Grade.UNVERIFIED}}
    assert proof.proof_strength([mutant], inconclusive).score == 0
    with pytest.raises(ValueError, match="verified passing outcomes"):
        proof.proof_strength([mutant], inconclusive, reviewed_equivalent={mutant.id})
