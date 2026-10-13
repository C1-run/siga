"""Statistics for the audit engine.

Pure stdlib. The two-tailed p-value for the t-statistic is computed exactly
via the regularized incomplete beta function (continued-fraction form),
not a normal approximation — small samples deserve honest tails.
"""

from __future__ import annotations

import math

_MAX_ITER = 200
_EPS = 3e-14
_FPMIN = 1e-300


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _FPMIN:
        d = _FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, _MAX_ITER + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = 1.0 + aa / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = 1.0 + aa / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPS:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_two_tailed_p(t: float, df: int) -> float:
    """Exact two-tailed p-value for a t-statistic with `df` degrees of freedom."""
    if df < 1:
        return 1.0
    if math.isinf(t):
        return 0.0
    x = df / (df + t * t)
    return _betai(df / 2.0, 0.5, x)


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs: list[float]) -> float:
    """Sample standard deviation (n-1)."""
    n = len(xs)
    if n < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def t_stat(xs: list[float]) -> tuple[float, float]:
    """One-sample t-statistic against zero and its exact two-tailed p-value."""
    n = len(xs)
    if n < 2:
        return 0.0, 1.0
    m = mean(xs)
    sd = stdev(xs)
    if sd == 0.0:
        if m == 0.0:
            return 0.0, 1.0
        return math.copysign(math.inf, m), 0.0
    t = m / (sd / math.sqrt(n))
    return t, t_two_tailed_p(t, n - 1)
