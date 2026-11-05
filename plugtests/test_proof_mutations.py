"""Exercise patch application without running PHP or making network calls."""

import json

import pytest
from goldgraft_contracts.proof import Grade
from goldgraft_contracts.registry import validate

from pieces.proof.mutation import apply_mutant, run_mutants

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
