"""Exact Beta-posterior integration; synthetic demo policy, no dependencies.

For integer a,b, f(x)=x**(a-1)*(1-x)**(b-1)/B(a,b) is a
polynomial. Integrate f_old(x)*F_new(x-margin) from margin to 1.
That is P(new < old-margin); its complement is the promotion probability.
Every coefficient and antiderivative is a Fraction: no quadrature or randomness.
"""

from fractions import Fraction
from math import comb, factorial


def probabilities(n_old, success_old, n_new, success_new, margin=Fraction(1, 50)):
    """Return exact (not_worse, worse) posterior probabilities, Beta(1,1) priors."""
    if not (0 <= success_old <= n_old and 0 <= success_new <= n_new):
        raise ValueError("success counts must lie within sample counts")
    if not 0 <= margin <= 1:
        raise ValueError("margin must be in [0,1]")
    ao, bo = success_old + 1, n_old - success_old + 1
    an, bn = success_new + 1, n_new - success_new + 1
    norm_old = factorial(ao + bo - 1) // (factorial(ao - 1) * factorial(bo - 1))
    norm_new = factorial(an + bn - 1) // (factorial(an - 1) * factorial(bn - 1))
    # F_new(x-margin), using the integrated binomial expansion of its density.
    cdf = [Fraction(0) for _ in range(an + bn)]
    for k in range(bn):
        degree = an + k
        coefficient = Fraction(norm_new * (-1) ** k * comb(bn - 1, k), degree)
        for j in range(degree + 1):
            cdf[j] += coefficient * comb(degree, j) * (-margin) ** (degree - j)
    product = [Fraction(0) for _ in range(len(cdf) + ao + bo - 2)]
    for k in range(bo):
        degree = ao - 1 + k
        coefficient = norm_old * (-1) ** k * comb(bo - 1, k)
        for j, value in enumerate(cdf):
            product[degree + j] += coefficient * value
    worse = sum(
        (
            coefficient * (1 - margin ** (degree + 1)) / (degree + 1)
            for degree, coefficient in enumerate(product)
        ),
        Fraction(0),
    )
    assert 0 <= worse <= 1
    return 1 - worse, worse


def counts_from_events(events):
    """Unique APPROVED orders are trials; CAPTURED among those are successes."""
    counts = {}
    for path in ("OLD", "NEW"):
        approved = {
            e["order_ref"] for e in events if e["path"] == path and e["event"] == "APPROVED"
        }
        captured = {
            e["order_ref"] for e in events if e["path"] == path and e["event"] == "CAPTURED"
        }
        counts[path] = len(approved), len(approved & captured)
    return counts["OLD"][0], counts["OLD"][1], counts["NEW"][0], counts["NEW"][1]


def decision(events, *, stage=10, hard_stop=None):
    n_old, success_old, n_new, success_new = counts_from_events(events)
    safe, worse = probabilities(n_old, success_old, n_new, success_new)
    if hard_stop:
        action, target, reason = "CUTBACK", 0, hard_stop
    elif worse >= Fraction(95, 100):
        action, target, reason = "CUTBACK", 0, "Posterior probability of worse exceeds 0.95"
    elif n_new >= 30 and safe >= Fraction(95, 100):
        stages = [0, 1, 10, 50, 100]
        action, target, reason = (
            "STEP_UP",
            stages[stages.index(stage) + 1],
            "Enough safe NEW trials",
        )
    else:
        action, target, reason = (
            "HOLD",
            stage,
            "Thin data" if n_new < 30 else "Posterior inconclusive",
        )
    return {
        "graft_id": "synthetic-c4",
        "from_stage_pct": stage,
        "action": action,
        "to_stage_pct": target,
        "reason": reason,
        "stats": {
            "n_old": n_old,
            "n_new": n_new,
            "success_old": success_old,
            "success_new": success_new,
            "prob_new_not_worse": float(safe),
            "threshold": 0.95,
        },
        "hard_stop": hard_stop,
    }
