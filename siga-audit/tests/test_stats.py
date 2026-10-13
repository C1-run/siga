"""Tests for the exact statistics (no normal approximations allowed)."""

import math

from siga_audit.stats import mean, stdev, t_stat, t_two_tailed_p


def test_p_at_zero_t_is_one():
    assert t_two_tailed_p(0.0, 29) == 1.0


def test_known_critical_value_df29():
    # t_{0.975, 29} = 2.0452 — the exact 5% two-tailed boundary.
    p = t_two_tailed_p(2.0452, 29)
    assert abs(p - 0.05) < 0.001


def test_large_df_approaches_normal():
    # With huge df the t-distribution converges to normal: 1.96 -> ~0.05.
    p = t_two_tailed_p(1.95996, 100000)
    assert abs(p - 0.05) < 0.001


def test_huge_t_gives_tiny_p():
    assert t_two_tailed_p(10.0, 30) < 1e-10


def test_p_decreases_monotonically_in_t():
    ps = [t_two_tailed_p(t, 20) for t in (0.5, 1.0, 1.5, 2.0, 3.0)]
    assert all(a > b for a, b in zip(ps, ps[1:]))


def test_mean_and_stdev():
    xs = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    assert mean(xs) == 5.0
    assert abs(stdev(xs) - 2.138) < 0.001


def test_t_stat_basic():
    t, p = t_stat([1.0] * 30 + [0.0] * 30)
    assert t > 0 and 0.0 < p < 1.0


def test_t_stat_degenerate_series():
    # All identical non-zero values: infinite t, zero p. All zeros: t=0, p=1.
    t, p = t_stat([3.0] * 10)
    assert math.isinf(t) and p == 0.0
    t, p = t_stat([0.0] * 10)
    assert t == 0.0 and p == 1.0


def test_t_stat_too_small():
    t, p = t_stat([1.0])
    assert (t, p) == (0.0, 1.0)
