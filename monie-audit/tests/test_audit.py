"""Tests for verdict logic — the part that must never lie."""

import pytest

from monie_audit.audit import run_audit


def _series(is_vals, oos_vals):
    return list(is_vals) + list(oos_vals)


def test_pass_on_significant_positive_oos():
    # 84 IS trades noise, 36 OOS trades with a real edge.
    oos = [25.0 if i % 3 else -10.0 for i in range(36)]  # mean ~13.3
    res = run_audit(_series([5.0, -5.0] * 42, oos))
    assert res.verdict == "PASS"
    assert res.oos.n == 36
    assert res.in_sample.n == 84
    assert res.oos.p < 0.05
    assert res.breakeven_cost == pytest.approx(res.oos.mean)


def test_fail_on_significant_negative_oos():
    oos = [-25.0 if i % 3 else 10.0 for i in range(36)]  # mean ~-13.3
    res = run_audit(_series([5.0, -5.0] * 42, oos))
    assert res.verdict == "FAIL"


def test_small_sample_forces_inconclusive():
    # 60 total -> OOS n=18 < 30, even with a glaring edge.
    oos = [100.0 if i % 2 else 50.0 for i in range(18)]
    res = run_audit(_series([1.0, -1.0] * 21, oos))
    assert res.verdict == "INCONCLUSIVE"
    assert any("n=18 < 30" in r for r in res.reasons)


def test_insignificant_oos_is_inconclusive():
    oos = [30.0, -30.0] * 18  # mean 0, huge variance
    res = run_audit(_series([1.0, -1.0] * 42, oos))
    assert res.verdict == "INCONCLUSIVE"
    assert any("not statistically significant" in r for r in res.reasons)


def test_cost_kills_edge():
    oos = [45.0 if i % 3 else -15.0 for i in range(36)]  # mean 25
    res = run_audit(_series([1.0] * 84, oos), assumed_cost=30.0)
    assert res.net_at_cost is not None
    assert res.net_at_cost.mean == pytest.approx(-5.0)
    assert any("edge is gone" in r for r in res.reasons)


def test_cost_survives_edge():
    oos = [45.0 if i % 3 else -15.0 for i in range(36)]  # mean 25
    res = run_audit(_series([1.0] * 84, oos), assumed_cost=5.0)
    assert res.net_at_cost is not None
    assert res.net_at_cost.mean == pytest.approx(20.0)


def test_negative_full_sample_note():
    # Small OOS (withholds verdict) but full sample clearly negative.
    xs = [-20.0, -10.0, 5.0] * 20  # 60 trades, mean -8.3
    res = run_audit(xs)
    assert res.verdict == "INCONCLUSIVE"
    assert any("full-sample P&L is significantly negative" in r for r in res.reasons)


def test_too_few_trades_raises():
    with pytest.raises(ValueError, match="at least 10"):
        run_audit([1.0] * 5)


def test_bad_oos_frac_raises():
    with pytest.raises(ValueError):
        run_audit([1.0] * 50, oos_frac=0.9)


def test_split_is_positional_and_correct():
    xs = list(range(100))
    res = run_audit([float(x) for x in xs])
    assert res.in_sample.n == 70
    assert res.oos.n == 30
    # OOS must be the LAST 30 trades.
    assert res.oos.mean == pytest.approx(sum(xs[70:]) / 30)


def test_to_dict_shape():
    res = run_audit([5.0, -5.0] * 30)
    d = res.to_dict()
    assert d["verdict"] in ("PASS", "FAIL", "INCONCLUSIVE")
    assert d["oos"]["n"] == 18
    assert "breakeven_cost" in d
