"""Compare integer integration against the independent Fraction reference."""

import importlib.util
from fractions import Fraction
from itertools import product

from pieces.proof.posterior import probabilities

from .conftest import ROOT


def test_exact_posterior_matches_reference_across_small_samples():
    spec = importlib.util.spec_from_file_location(
        "heal_reference", ROOT / "fixtures/tools/heal_reference.py"
    )
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)

    counts = [(n, success) for n in range(5) for success in range(n + 1)]
    for (n_old, old), (n_new, new), margin in product(
        counts, counts, (Fraction(0), Fraction(1, 50), Fraction(2, 7), Fraction(1))
    ):
        args = n_old, old, n_new, new, margin
        assert probabilities(*args) == reference.probabilities(*args)
