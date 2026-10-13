"""The audit engine.

Input:  per-trade P&L, chronological order (position in the list is time).
Split:  first (1 - oos_frac) = in-sample, last oos_frac = out-of-sample.
Rule:   the verdict is based on OOS ONLY. IS numbers are shown for contrast.
Guard:  OOS n < min_oos forces INCONCLUSIVE, whatever the t-statistic says.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from monie_audit.stats import mean, stdev, t_stat

ALPHA = 0.05
DEFAULT_OOS_FRAC = 0.30
DEFAULT_MIN_OOS = 30


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
) -> AuditResult:
    """Audit a chronological series of per-trade P&L.

    `assumed_cost` is a fixed cost per trade in the same units as `pnl`
    (already netted costs are fine too — then leave it None and the gross
    edge per trade is reported as the breakeven).
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

    reasons: list[str] = []
    small_sample = oos.n < min_oos

    # Verdict on OOS only.
    if small_sample:
        verdict = "INCONCLUSIVE"
        reasons.append(
            f"OOS sample n={oos.n} < {min_oos} — evidence insufficient, verdict withheld"
        )
    elif oos.p < ALPHA:
        if oos.mean > 0:
            verdict = "PASS"
            reasons.append(f"OOS edge significant and positive (t={oos.t:.2f}, p={oos.p:.4f})")
        else:
            verdict = "FAIL"
            reasons.append(f"OOS edge significant and negative (t={oos.t:.2f}, p={oos.p:.4f})")
    else:
        verdict = "INCONCLUSIVE"
        reasons.append(f"OOS not statistically significant (t={oos.t:.2f}, p={oos.p:.4f} >= {ALPHA})")

    # Cost sensitivity: gross edge per trade IS the breakeven round-trip cost.
    breakeven = oos.mean
    net_at_cost = None
    if assumed_cost is not None:
        if assumed_cost < 0:
            raise ValueError("assumed_cost must be >= 0")
        net = SampleStats.from_series([x - assumed_cost for x in oos_xs])
        net_at_cost = net
        if net.mean <= 0:
            reasons.append(
                f"at assumed cost {assumed_cost:.4f}/trade the OOS edge is gone "
                f"(net mean {net.mean:.4f})"
            )
        elif net.p >= ALPHA:
            reasons.append(
                f"at assumed cost {assumed_cost:.4f}/trade the OOS edge survives "
                f"but is no longer significant (net p={net.p:.4f})"
            )
        else:
            reasons.append(
                f"OOS edge survives assumed cost {assumed_cost:.4f}/trade "
                f"(net t={net.t:.2f}, p={net.p:.4f})"
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
        min_oos=min_oos,
        verdict=verdict,
        reasons=reasons,
        breakeven_cost=breakeven,
        assumed_cost=assumed_cost,
        net_at_cost=net_at_cost,
    )
