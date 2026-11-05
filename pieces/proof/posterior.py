"""Exact Beta(1,1)-prior posterior comparisons using integer polynomials."""

from fractions import Fraction
from math import comb, lcm


def probabilities(n_old, success_old, n_new, success_new, margin=Fraction(1, 50)):
    """Return exact probabilities of new >= old - margin and its complement."""
    if not (0 <= success_old <= n_old and 0 <= success_new <= n_new):
        raise ValueError("success counts must lie within sample counts")
    margin = Fraction(margin)
    if not 0 <= margin <= 1:
        raise ValueError("margin must be in [0,1]")
    if margin == 1:
        return Fraction(1), Fraction(0)

    # For margin p/q, substitute y=q*old. Integrate the old density times
    # F_new((y-p)/q) over [p,q], postponing division until the final result.
    p, q = margin.numerator, margin.denominator
    new_degree = n_new + 1
    old_failures = n_old - success_old
    new_failures = n_new - success_new
    q_powers = [1]
    p_powers = [1]
    max_degree = n_old + new_degree + 1
    for _ in range(max_degree):
        q_powers.append(q_powers[-1] * q)
        p_powers.append(p_powers[-1] * p)

    cdf = [0] * (new_degree + 1)
    for k in range(new_failures + 1):
        degree = success_new + 1 + k
        coefficient = comb(new_degree, degree) * comb(degree - 1, success_new)
        coefficient *= q_powers[new_degree - degree] * (-1) ** k
        for j in range(degree + 1):
            power = degree - j
            cdf[j] += coefficient * comb(degree, j) * p_powers[power] * (-1) ** power

    product = [0] * max_degree
    for k in range(old_failures + 1):
        shift = success_old + k
        coefficient = comb(old_failures, k) * q_powers[old_failures - k] * (-1) ** k
        for j, value in enumerate(cdf):
            product[shift + j] += coefficient * value

    common = lcm(*(degree for degree, value in enumerate(product, 1) if value))
    numerator = sum(
        value * (q_powers[degree] - p_powers[degree]) * (common // degree)
        for degree, value in enumerate(product, 1)
        if value
    )
    norm_old = (n_old + 1) * comb(n_old, success_old)
    worse = Fraction(numerator * norm_old, common * q_powers[max_degree])
    return 1 - worse, worse
