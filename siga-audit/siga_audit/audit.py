"""The audit engine.

Input:  per-trade P&L, chronological order (position in the list is time).
Split:  first (1 - oos_frac) = in-sample, last oos_frac = out-of-sample.
Rule:   the verdict is based on OOS ONLY. IS numbers are shown for contrast.
Cost:   when an assumed cost per trade is given, it is subtracted before the
        verdict — a gross edge that costs more than it earns is not an edge.
Cluster: with `cluster_days`, the verdict is computed on per-UTC-day means
        instead of per-trade ones: a profit that lives inside one day is one
        observation, not fifty.
Guard:  fewer judged observations than the floor forces INCONCLUSIVE, whatever
        the t-statistic says.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from siga_audit.stats import mean, stdev, t_stat

ALPHA = 0.05
DEFAULT_OOS_FRAC = 0.30
DEFAULT_MIN_OOS = 30
DEFAULT_MIN_DAYS = 10


def daily_means(xs: list[float], days: list[int]) -> list[float]:
    """Mean of `xs` per day key, in first-seen order — the unit a clustered test reads.

    Days equal-weight: one day contributes its average, however many trades
    happened in it. A quiet week then cannot hide behind a loud afternoon.
    """
    if len(xs) != len(days):
        raise ValueError(f"need one day key per value, got {len(xs)} values / {len(days)} days")
    per: dict[int, list[float]] = {}
    for x, d in zip(xs, days):
        per.setdefault(d, []).append(x)
    return [sum(v) / len(v) for v in per.values()]


@dataclass
class SampleStats:
    n: int
    mean: float
    stdev: float
    t: float
    p: float

    @classmethod
    def from_series(cls, xs: list[float]) -> "SampleStats":
        t, p = t_stat(xs)
        return cls(n=len(xs), mean=mean(xs), stdev=stdev(xs), t=t, p=p)


@dataclass
class AuditResult:
    full: SampleStats
    in_sample: SampleStats
    oos: SampleStats
    min_oos: int
    verdict: str  # "PASS" | "FAIL" | "INCONCLUSIVE"
    reasons: list[str] = field(default_factory=list)
    # Cost sensitivity (gross edge per trade = breakeven cost)
    breakeven_cost: float = 0.0
    assumed_cost: float | None = None
    net_at_cost: SampleStats | None = None
    # The series the verdict was actually computed on (net when a cost was given,
    # day-equal-weighted when clustered).
    judged: SampleStats | None = None
    clustered: bool = False
    oos_days: int | None = None

    def to_dict(self) -> dict:
        def s(x: SampleStats | None) -> dict | None:
            if x is None:
                return None
            return {"n": x.n, "mean": x.mean, "stdev": x.stdev, "t": x.t, "p": x.p}

        return {
            "verdict": self.verdict,
            "reasons": self.reasons,
            "full": s(self.full),
            "in_sample": s(self.in_sample),
            "oos": s(self.oos),
            "judged": s(self.judged),
            "judged_net": self.assumed_cost is not None,
            "clustered": self.clustered,
            "oos_days": self.oos_days,
            "min_oos": self.min_oos,
            "breakeven_cost": self.breakeven_cost,
            "assumed_cost": self.assumed_cost,
            "net_at_cost": s(self.net_at_cost),
        }


def run_audit(
    pnl: list[float],
    *,
    oos_frac: float = DEFAULT_OOS_FRAC,
    min_oos: int = DEFAULT_MIN_OOS,
    assumed_cost: float | None = None,
    days: list[int] | None = None,
    cluster_days: bool = False,
    min_days: int = DEFAULT_MIN_DAYS,
) -> AuditResult:
    """Audit a chronological series of per-trade P&L.

    `assumed_cost` is a fixed cost per trade in the same units as `pnl`
    (already netted costs are fine too — then leave it None and the gross
    edge per trade is reported as the breakeven).

    `days` is one day key per trade (any hashable; the CLI uses the UTC day
    index). With `cluster_days`, `days` is required and the verdict is computed
    on the per-day means of the judged OOS slice, floored at `min_days` days
    rather than `min_oos` tickets.
    """
    if len(pnl) < 10:
        raise ValueError(f"need at least 10 trades to audit, got {len(pnl)}")
    if not 0.05 <= oos_frac <= 0.5:
        raise ValueError("oos_frac must be within [0.05, 0.5]")

    cut = int(len(pnl) * (1.0 - oos_frac))
    cut = max(1, min(cut, len(pnl) - 1))
    is_xs = pnl[:cut]
    oos_xs = pnl[cut:]

    full = SampleStats.from_series(pnl)
    ins = SampleStats.from_series(is_xs)
    oos = SampleStats.from_series(oos_xs)

    # Cost sensitivity: gross edge per trade IS the breakeven round-trip cost.
    breakeven = oos.mean
    net_at_cost = None
    if assumed_cost is not None:
        if assumed_cost < 0:
            raise ValueError("assumed_cost must be >= 0")
        net_at_cost = SampleStats.from_series([x - assumed_cost for x in oos_xs])

    # The verdict is judged on the money actually kept — net of the assumed cost
    # when one is given, gross otherwise — and on the day, not the ticket, when
    # the trades are clustered.
    judged_values = (
        [x - assumed_cost for x in oos_xs] if assumed_cost is not None else list(oos_xs)
    )
    clustered = cluster_days
    oos_days = None
    if clustered:
        if days is None:
            raise ValueError("cluster_days needs a day key per trade (a time column)")
        oos_day_means = daily_means(judged_values, days[cut:])
        oos_days = len(oos_day_means)
        judged = SampleStats.from_series(oos_day_means)
        floor = min_days
    else:
        judged = SampleStats.from_series(judged_values)
        floor = min_oos

    reasons: list[str] = []
    small_sample = judged.n < floor

    if small_sample:
        verdict = "INCONCLUSIVE"
        unit = " (UTC days)" if clustered else ""
        reasons.append(
            f"OOS sample n={judged.n} < {floor}{unit} — evidence insufficient, verdict withheld"
        )
    elif judged.p < ALPHA:
        if judged.mean > 0:
            verdict = "PASS"
            reasons.append(
                f"OOS edge significant and positive "
                f"(t={judged.t:+.2f}, p={judged.p:.4f})"
            )
        else:
            verdict = "FAIL"
            reasons.append(
                f"OOS edge significant and negative "
                f"(t={judged.t:+.2f}, p={judged.p:.4f})"
            )
    else:
        verdict = "INCONCLUSIVE"
        reasons.append(
            f"OOS not statistically significant "
            f"(t={judged.t:+.2f}, p={judged.p:.4f} >= {ALPHA})"
        )

    if clustered:
        reasons.append(
            f"clustered: judged on {judged.n} UTC-day means, not {len(oos_xs)} tickets"
        )

    if net_at_cost is not None:
        if net_at_cost.mean <= 0:
            reasons.append(
                f"at assumed cost {assumed_cost:.4f}/trade the OOS edge is gone "
                f"(net mean {net_at_cost.mean:.4f})"
            )
        elif net_at_cost.p >= ALPHA:
            reasons.append(
                f"at assumed cost {assumed_cost:.4f}/trade the OOS edge survives "
                f"but is no longer significant (net p={net_at_cost.p:.4f})"
            )
        else:
            reasons.append(
                f"OOS edge survives assumed cost {assumed_cost:.4f}/trade "
                f"(net t={net_at_cost.t:+.2f}, p={net_at_cost.p:.4f})"
            )

    if small_sample and full.p < ALPHA and full.mean < 0:
        reasons.append(
            "note: full-sample P&L is significantly negative — "
            "even zero-cost, this strategy loses money"
        )

    return AuditResult(
        full=full,
        in_sample=ins,
        oos=oos,
        # The floor actually applied: days when clustered, tickets otherwise.
        min_oos=floor,
        verdict=verdict,
        reasons=reasons,
        breakeven_cost=breakeven,
        assumed_cost=assumed_cost,
        net_at_cost=net_at_cost,
        judged=judged,
        clustered=clustered,
        oos_days=oos_days,
    )
