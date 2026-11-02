"""The auditor has to be auditable: clustering and the planted-edge control."""

import random

import pytest

from siga_audit.audit import daily_means, run_audit
from siga_audit.plant import contrast, detectable_delta, ladder


def _one_day_tape():
    """20 days x 50 trades; every cent of profit sits inside a single day."""
    pnl = [0.0] * 950 + [2.0] * 50
    days = [i // 50 for i in range(1000)]
    return pnl, days


def _noisy_log(n_days=30, per_day=30, seed=42):
    rng = random.Random(seed)
    pnl, days = [], []
    for d in range(n_days):
        for _ in range(per_day):
            pnl.append(rng.gauss(0.0, 1.0))
            days.append(d)
    return pnl, days


def test_daily_means_equal_weights_each_day():
    assert daily_means([1.0, 2.0, 3.0, 10.0], [0, 0, 1, 1]) == pytest.approx([1.5, 6.5])


def test_daily_means_rejects_a_mismatched_key():
    with pytest.raises(ValueError, match="one day key per value"):
        daily_means([1.0, 2.0], [0])


def test_a_one_day_edge_passes_per_ticket_and_fails_per_day():
    pnl, days = _one_day_tape()
    tickets = run_audit(pnl)
    assert tickets.verdict == "PASS"
    assert tickets.judged.t > 5

    clustered = run_audit(pnl, days=days, cluster_days=True)
    assert clustered.verdict == "INCONCLUSIVE"
    assert clustered.clustered is True
    # The split is positional, so the judged unit is the day *inside* the OOS slice.
    assert clustered.judged.n == len(set(days[700:]))
    assert clustered.oos_days == clustered.judged.n
    assert clustered.judged.n < 20


def test_clustering_counts_days_against_the_day_floor():
    pnl, days = _one_day_tape()
    res = run_audit(pnl, days=days, cluster_days=True, min_days=40)
    assert res.verdict == "INCONCLUSIVE"
    assert "UTC days" in " ".join(res.reasons)


def test_cluster_days_without_a_time_column_is_an_error_not_a_default():
    with pytest.raises(ValueError, match="day key"):
        run_audit([1.0] * 40, cluster_days=True)


def test_contrast_leaves_the_population_sum_alone():
    pnl = [1.0, -1.0, 2.0, -2.0, 3.0, 100.0]
    member = [False, False, False, False, False, True]
    planted = contrast(pnl, member, 0.25)
    assert sum(planted) == pytest.approx(sum(pnl))
    assert planted[5] == pytest.approx(100.25)
    # The remainder pays: 1 share of 6, so the other five lose 0.25/5 each.
    assert planted[0] == pytest.approx(1.0 - 0.05)


def test_contrast_needs_members_and_a_remainder():
    with pytest.raises(ValueError, match="empty"):
        contrast([1.0, 2.0], [False, False], 0.1)
    with pytest.raises(ValueError, match="whole log"):
        contrast([1.0, 2.0], [True, True], 0.1)


def test_the_ladder_moves_when_an_edge_is_planted():
    pnl, days = _noisy_log(n_days=60)
    rungs = ladder(
        pnl, [0.0, 0.05, 0.1, 0.25], days=days, cluster_days=True, min_days=10
    )
    assert rungs[0].verdict != "PASS", "the plant must not clear unplanted"
    found = detectable_delta(rungs)
    assert found is not None
    assert found > 0.0
    assert rungs[-1].verdict == "PASS"


def test_a_ladder_that_never_moves_reports_no_detectable_edge():
    pnl, days = _noisy_log(n_days=4, per_day=5)
    rungs = ladder(
        pnl, [0.0, 0.25, 0.5], days=days, cluster_days=True, min_days=10
    )
    assert all(r.verdict == "INCONCLUSIVE" for r in rungs)
    assert detectable_delta(rungs) is None


def test_ladder_requires_ascending_deltas():
    with pytest.raises(ValueError, match="ascending"):
        ladder([0.0] * 20, [0.5, 0.0])
