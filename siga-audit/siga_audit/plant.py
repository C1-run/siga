"""Positive control — plant a known edge and check the verdict can see it.

A "no edge" answer from a log nobody has proven readable is not a measurement,
it is a mood. The plant is the cheapest proof the audit is pointed at something:
lift one labeled stratum by a known amount and require the verdict to move.

Two invariants carry the weight:

* A contrast plant lifts the stratum by `delta` and drags the remainder so the
  **population total is unchanged**. Whatever the stratum gains, the rest of the
  log pays for it. An audit that moves on the whole-log verdict is therefore
  reading something that is not the planted edge.
* The plant says nothing about the market. It calibrates the instrument: the
  smallest planted edge this log can prove is the doubt radius of the answer
  it just gave.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from siga_audit.audit import AuditResult, run_audit

DEFAULT_DELTAS = (0.0, 0.05, 0.1, 0.25, 0.5)


def contrast(
    values: Sequence[float], member: Sequence[bool], delta: float
) -> list[float]:
    """Lift members by `delta`, drag the rest so the population sum is preserved."""
    if len(values) != len(member):
        raise ValueError(
            f"need one membership flag per value, got {len(values)} values / {len(member)} flags"
        )
    in_n = sum(1 for m in member if m)
    if in_n == 0:
        raise ValueError("stratum is empty — nothing was planted")
    if in_n == len(values):
        raise ValueError(
            "stratum is the whole log — a contrast needs a remainder to pay for it "
            "(use a level plant, or label a smaller stratum)"
        )
    share = in_n / len(values)
    shift = -delta * share / (1.0 - share)
    return [v + (delta if m else shift) for v, m in zip(values, member)]


@dataclass
class Rung:
    delta: float
    verdict: str
    mean: float
    t: float
    p: float
    n: int
    result: AuditResult


def ladder(
    values: Sequence[float],
    deltas: Sequence[float] = DEFAULT_DELTAS,
    *,
    days: Sequence[int] | None = None,
    **audit_kwargs,
) -> list[Rung]:
    """Audit the same series once per planted delta, ascending.

    `values` is the stratum's own P&L: a member's rung value is `v + delta`, so
    the ladder only needs the members. Anything else (cost, clustering, the OOS
    split) is passed straight through to `run_audit` and applies to every rung.
    """
    if list(deltas) != sorted(deltas):
        raise ValueError("deltas must be ascending")
    rungs: list[Rung] = []
    for d in deltas:
        res = run_audit([v + d for v in values], days=days, **audit_kwargs)
        j = res.judged or res.oos
        rungs.append(Rung(delta=d, verdict=res.verdict, mean=j.mean, t=j.t, p=j.p, n=j.n, result=res))
    return rungs


def detectable_delta(rungs: Sequence[Rung]) -> float | None:
    """Smallest planted delta that earns a PASS, or None if the ladder never moves."""
    for r in rungs:
        if r.verdict == "PASS":
            return r.delta
    return None
