"""CLI for the audit engine — ``siga audit trades.csv``.

CSV format: one row per trade, chronological. A P&L column is required
(detected among: pnl, pnl_usd, p&l, profit, net, return, ret, pl — or set
explicitly with --column). An optional notional column (notional, value,
trade_value) enables --cost-bps, and an optional time column (ts, time,
timestamp, date, datetime) enables --cluster-days.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import sys
from dataclasses import dataclass

from siga_audit.audit import (
    DEFAULT_MIN_DAYS,
    DEFAULT_MIN_OOS,
    DEFAULT_OOS_FRAC,
    AuditResult,
    run_audit,
)
from siga_audit.plant import DEFAULT_DELTAS, contrast, detectable_delta, ladder

_PNL_CANDIDATES = ("pnl", "pnl_usd", "p&l", "profit", "net_pnl", "net", "return", "ret", "pl")
_NOTIONAL_CANDIDATES = ("notional", "notional_usd", "trade_value", "value")
_TIME_CANDIDATES = (
    # Exit time wins over signal time when both exist: an outcome is only a fact
    # once it has settled, and clustering it onto the day it was opened would
    # credit the edge to a day it had not been paid for yet.
    "exit_ms",
    "exit_time",
    "ts",
    "time",
    "timestamp",
    "date",
    "datetime",
    "signal_ms",
    "signal_time",
)
_STRATUM_CANDIDATES = ("stratum", "arm", "label", "group", "side", "symbol", "strategy")


def _parse_number(raw: str) -> float:
    return float(raw.strip().replace("$", "").replace(",", ""))


def _day_key(raw: str) -> int | None:
    """Bucket a timestamp into a day index, or None if it is not a time.

    Epoch values are normalised from µs/ms/s by magnitude — the same field can
    mix units in one column, and a 13-digit millisecond stamp is not a day.
    """
    s = (raw or "").strip()
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        v = None
    if v is not None:
        if v < 0:
            return None
        while v >= 1e11:  # ms -> s, us -> s, ns-ish -> s
            v /= 1000.0
        return int(v // 86_400)
    # ISO-ish leading date: 2026-11-02, with or without a time tail.
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        try:
            d = datetime.date.fromisoformat(s[:10])
        except ValueError:
            return None
        return d.toordinal()
    return None


def _pick_column(header: list[str], candidates: tuple[str, ...]) -> str | None:
    lowered = [h.strip().lower() for h in header]
    for cand in candidates:
        if cand in lowered:
            return header[lowered.index(cand)]
    return None


@dataclass
class TradeLog:
    """Everything one CSV read can give the auditor, in row order."""

    pnl: list[float]
    notional: list[float] | None = None
    days: list[int] | None = None
    stratum: list[str] | None = None
    time_col: str | None = None
    stratum_col: str | None = None
    unparseable_days: int = 0

    def members(self, value: str) -> list[bool]:
        if self.stratum is None:
            return []
        return [s == value for s in self.stratum]


def load_trades_csv(
    path: str, column: str | None = None, stratum_column: str | None = None
) -> TradeLog:
    """Read a trade log into a TradeLog. Only the P&L column is required."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("empty CSV or missing header row")
        pnl_col = column or _pick_column(reader.fieldnames, _PNL_CANDIDATES)
        if pnl_col is None:
            raise ValueError(
                "no P&L column found (looked for: "
                + ", ".join(_PNL_CANDIDATES)
                + "). Use --column to name it."
            )
        if column and column not in reader.fieldnames:
            raise ValueError(f"column {column!r} not in CSV header: {reader.fieldnames}")
        notional_col = _pick_column(reader.fieldnames, _NOTIONAL_CANDIDATES)
        ts_col = _pick_column(reader.fieldnames, _TIME_CANDIDATES)
        strat_col = (
            stratum_column
            if stratum_column and stratum_column in reader.fieldnames
            else _pick_column(reader.fieldnames, _STRATUM_CANDIDATES)
        )
        if stratum_column and stratum_column not in reader.fieldnames:
            raise ValueError(
                f"stratum column {stratum_column!r} not in CSV header: {reader.fieldnames}"
            )
        prev_ts: float | str | None = None
        ts_warned = False

        pnl: list[float] = []
        notional: list[float] = []
        days: list[int] = []
        stratum: list[str] = []
        bad_days = 0
        for i, row in enumerate(reader, start=2):  # header is line 1
            if ts_col and not ts_warned:
                raw_ts = row.get(ts_col)
                if raw_ts:
                    try:
                        cur_ts: float | str = float(raw_ts)
                    except ValueError:
                        cur_ts = raw_ts.strip()
                    if (
                        prev_ts is not None
                        and isinstance(cur_ts, type(prev_ts))
                        and cur_ts < prev_ts
                    ):
                        print(
                            f"warning: {ts_col} column is not chronological "
                            f"at line {i} — using row order as time",
                            file=sys.stderr,
                        )
                        ts_warned = True
                    prev_ts = cur_ts
            raw = row.get(pnl_col)
            try:
                pnl.append(_parse_number(raw or ""))
            except ValueError:
                raise ValueError(f"line {i}: cannot parse P&L value {raw!r}") from None
            if notional_col:
                raw_n = row.get(notional_col)
                try:
                    notional.append(abs(_parse_number(raw_n or "")))
                except ValueError:
                    raise ValueError(
                        f"line {i}: cannot parse notional value {raw_n!r}"
                    ) from None
            if ts_col:
                dk = _day_key(row.get(ts_col) or "")
                if dk is None:
                    bad_days += 1
                    dk = 0
                days.append(dk)
            if strat_col:
                stratum.append((row.get(strat_col) or "").strip())
    if len(pnl) < 10:
        raise ValueError(f"need at least 10 trades to audit, got {len(pnl)}")
    return TradeLog(
        pnl=pnl,
        notional=notional if notional_col else None,
        days=days if ts_col and bad_days == 0 else None,
        stratum=stratum if strat_col else None,
        time_col=ts_col,
        stratum_col=strat_col,
        unparseable_days=bad_days,
    )


def _check(label: str, value: str) -> str:
    """Dot-leader a CHECK line to a fixed column."""
    pad = max(3, 34 - len(label) - 2)
    return f"{label} {'.' * pad} {value}"


def render_text(res: AuditResult, source: str, oos_frac: float) -> str:
    def fmt_money(x: float) -> str:
        return f"{x:+,.2f}"

    def fmt_p(p: float) -> str:
        return "<0.0001" if p < 1e-4 else f"{p:.4f}"

    lines = []
    lines.append(f"siga audit — {source}")
    lines.append("=" * 64)
    lines.append(
        f"Full sample   n={res.full.n:<5} mean={fmt_money(res.full.mean)}   "
        "(informational only — never the verdict)"
    )
    lines.append(
        f"IS  ({1 - oos_frac:.0%})      n={res.in_sample.n:<5} mean={fmt_money(res.in_sample.mean)}   "
        f"t={res.in_sample.t:+.2f}  p={fmt_p(res.in_sample.p)}"
    )
    lines.append(
        f"OOS ({oos_frac:.0%})      n={res.oos.n:<5} mean={fmt_money(res.oos.mean)}   "
        f"t={res.oos.t:+.2f}  p={fmt_p(res.oos.p)}"
    )
    lines.append("")

    sig_series = res.judged or res.oos
    basis = []
    if res.assumed_cost is not None:
        basis.append("net of assumed cost")
    if res.clustered:
        basis.append(f"{sig_series.n} daily means")
    basis_txt = f", {' / '.join(basis)}" if basis else ", gross per ticket"
    sig = "significant" if sig_series.p < 0.05 else "not significant"
    lines.append(
        _check("CHECK 01  OOS verdict",
               f"t={sig_series.t:+.2f}, p={fmt_p(sig_series.p)} ({sig}{basis_txt})")
    )
    if res.assumed_cost is not None and res.net_at_cost is not None:
        net = res.net_at_cost
        lines.append(
            _check("CHECK 02  Cost sensitivity",
                   f"assumed {res.assumed_cost:.4f}/trade -> "
                   f"net mean {fmt_money(net.mean)}, t={net.t:+.2f}, p={fmt_p(net.p)}")
        )
    else:
        if res.breakeven_cost > 0:
            lines.append(
                _check("CHECK 02  Cost sensitivity",
                       f"breakeven {fmt_money(res.breakeven_cost)}/trade — "
                       "any round-trip cost above this kills the edge")
            )
        else:
            lines.append(
                _check("CHECK 02  Cost sensitivity",
                       f"gross edge {fmt_money(res.breakeven_cost)}/trade — "
                       "already negative before any cost")
            )
    unit = "UTC days" if res.clustered else "n"
    guard = (
        f"OOS {unit}={sig_series.n} >= {res.min_oos} (ok)"
        if sig_series.n >= res.min_oos
        else f"OOS {unit}={sig_series.n} < {res.min_oos} -> verdict withheld"
    )
    lines.append(_check("CHECK 03  Small-sample guard", guard))
    lines.append("")
    lines.append(f"VERDICT: {res.verdict}")
    for r in res.reasons:
        lines.append(f"  - {r}")
    if res.assumed_cost is None:
        lines.append("")
        lines.append(
            "note: verdict is gross of costs — use --cost or --cost-bps for net"
        )
    return "\n".join(lines)


def _parse_deltas(raw: str | None) -> list[float]:
    if not raw:
        return list(DEFAULT_DELTAS)
    try:
        deltas = [float(x) for x in raw.split(",") if x.strip()]
    except ValueError:
        raise ValueError(f"--deltas needs comma-separated numbers, got {raw!r}") from None
    if deltas != sorted(deltas):
        raise ValueError(f"--deltas must be ascending, got {raw!r}")
    return deltas


def _plant_rungs(log: "TradeLog", value: str, deltas: list[float], audit_kwargs: dict):
    """Audit the stratum once per planted delta. None when the log has no such stratum."""
    if log.stratum is None:
        return None
    idx = [i for i, m in enumerate(log.members(value)) if m]
    if not idx:
        return None
    kwargs = dict(audit_kwargs)
    day_keys = kwargs.pop("days", None)
    rung_days = [day_keys[i] for i in idx] if day_keys else None
    return ladder([log.pnl[i] for i in idx], deltas, days=rung_days, **kwargs)


def render_plant(rungs, *, stratum: str, stratum_n: int, total_n: int,
                 basis: str, control_before: float, control_after: float) -> str:
    unit = "daily means" if rungs[0].result.clustered else "tickets"
    lines = []
    lines.append("")
    lines.append(
        f"PLANT — {stratum!r}: {stratum_n} of {total_n} trades, {basis}, "
        f"judged on {rungs[0].n} {unit}"
    )
    lines.append(f"{'planted delta':>14}  {'judged n':>9}  {'mean':>9}  {'t':>7}  {'p':>8}  verdict")
    for r in rungs:
        p = "<0.0001" if r.p < 1e-4 else f"{r.p:.4f}"
        lines.append(
            f"{r.delta:>14.4f}  {r.n:>9}  {r.mean:>+9.4f}  {r.t:>+7.2f}  {p:>8}  {r.verdict}"
        )
    lines.append(
        f"control: the contrast leaves the whole-log mean where it found it "
        f"({control_before:+.4f} -> {control_after:+.4f}) — the plant is only "
        "visible inside the stratum"
    )
    top = rungs[-1].delta
    found = detectable_delta(rungs)
    if rungs[0].verdict == "PASS":
        lines.append(
            "plant says nothing: this stratum clears unplanted, so the ladder cannot "
            "calibrate it"
        )
    elif found is None:
        lines.append(
            f"this log cannot prove an edge as large as {top:.4f}/trade — "
            "read the verdict as 'no answer', not 'no edge'"
        )
    else:
        lines.append(
            f"smallest planted edge this log can prove: {found:.4f}/trade — "
            f"a FAIL/INCONCLUSIVE here only rules out edges bigger than that"
        )
    return "\n".join(lines)


def add_audit_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "audit", help="audit a backtest trade log (CSV) and print a verdict"
    )
    p.add_argument("csv", nargs="?", default=None,
                   help="path to trades CSV (one row per trade, chronological). "
                        "Not needed if --from is used.")
    p.add_argument("--from", dest="source", default=None, metavar="SOURCE",
                   help="pull trades directly from a data source: binance, dune, helius. "
                        "Requires siga-connect (pip install siga-connect).")
    p.add_argument("--symbol", default=None, help="trading pair (required for binance)")
    p.add_argument("--query-id", type=int, default=None, help="Dune query ID (required for dune)")
    p.add_argument("--address", default=None, help="Solana address (required for helius)")
    p.add_argument("--api-key", default=None, help="API key (dune, helius, or binance private)")
    p.add_argument("--api-secret", default=None, help="API secret (binance private)")
    p.add_argument("--column", default=None, help="name of the P&L column (auto-detected by default)")
    p.add_argument("--cost", type=float, default=None,
                   help="assumed fixed cost per trade (same units as P&L)")
    p.add_argument("--cost-bps", type=float, default=None,
                   help="assumed round-trip cost in bps of notional (requires a notional column)")
    p.add_argument("--oos", type=float, default=DEFAULT_OOS_FRAC,
                   help=f"out-of-sample fraction (default {DEFAULT_OOS_FRAC})")
    p.add_argument("--min-oos", type=int, default=DEFAULT_MIN_OOS,
                   help=f"minimum OOS trades before any verdict (default {DEFAULT_MIN_OOS})")
    p.add_argument("--cluster-days", action="store_true",
                   help="judge the verdict on per-UTC-day means, not per-ticket ones "
                        "(needs a time column); one day counts once however many trades it held")
    p.add_argument("--min-days", type=int, default=DEFAULT_MIN_DAYS,
                   help=f"minimum OOS days when clustering (default {DEFAULT_MIN_DAYS})")
    p.add_argument("--plant", action="store_true",
                   help="positive control: plant a known edge into one stratum and report "
                        "the smallest planted edge this log can prove")
    p.add_argument("--stratum", default=None, metavar="VALUE",
                   help="stratum value to plant into (with --plant)")
    p.add_argument("--stratum-col", default=None, metavar="NAME",
                   help="column holding the stratum labels (auto-detected by default)")
    p.add_argument("--deltas", default=None, metavar="A,B,C",
                   help=f"planted edge ladder, ascending, in P&L units "
                        f"(default {','.join(str(d) for d in DEFAULT_DELTAS)})")
    p.add_argument("--trail", default=None, metavar="PATH",
                   help="append the verdict to an audit trail (JSONL) at PATH")
    p.add_argument("--json", action="store_true", help="print machine-readable JSON")


def run_audit_cli(args: argparse.Namespace) -> int:
    try:
        if getattr(args, "source", None):
            # Pull from a data source via siga-connect (optional dependency)
            try:
                from siga_connect import fetch_trades
            except ImportError:
                print(
                    "error: --from requires siga-connect. "
                    "Install with: pip install siga-connect",
                    file=sys.stderr,
                )
                return 2
            fetch_result = fetch_trades(
                args.source,
                symbol=getattr(args, "symbol", None),
                query_id=getattr(args, "query_id", None),
                address=getattr(args, "address", None),
                api_key=getattr(args, "api_key", None),
                api_secret=getattr(args, "api_secret", None),
            )
            log = TradeLog(pnl=fetch_result.pnl, notional=fetch_result.notional)
            pnl = fetch_result.pnl
            notional = fetch_result.notional
            source_desc = fetch_result.source
        else:
            if not args.csv:
                print("error: either provide a CSV file or use --from to pull from a data source", file=sys.stderr)
                return 2
            log = load_trades_csv(args.csv, args.column, args.stratum_col)
            pnl = log.pnl
            notional = log.notional
            source_desc = args.csv

        cost = args.cost
        if args.cost_bps is not None:
            if notional is None:
                print(
                    "error: --cost-bps requires a notional column "
                    "(notional, value, trade_value) in the CSV",
                    file=sys.stderr,
                )
                return 2
            # Convert bps to an equivalent fixed cost using average notional,
            # so the verdict math stays a plain per-trade subtraction.
            avg_notional = sum(notional) / len(notional)
            cost = args.cost_bps / 1e4 * avg_notional

        if args.cluster_days and log.days is None:
            print(
                "error: --cluster-days needs a time column that parses as a day "
                "(ts, time, timestamp, date, datetime or signal_ms)",
                file=sys.stderr,
            )
            return 2
        if args.plant and not args.stratum:
            print("error: --plant needs --stratum=VALUE (and a stratum column)", file=sys.stderr)
            return 2

        audit_kwargs = {
            "oos_frac": args.oos,
            "min_oos": args.min_oos,
            "assumed_cost": cost,
            "days": log.days if args.cluster_days else None,
            "cluster_days": args.cluster_days,
            "min_days": args.min_days,
        }
        res = run_audit(pnl, **audit_kwargs)
        rungs = None
        if args.plant:
            rungs = _plant_rungs(log, args.stratum, _parse_deltas(args.deltas), audit_kwargs)
            if rungs is None:
                print(
                    f"error: no stratum column found for {args.stratum!r} "
                    "(looked for: " + ", ".join(_STRATUM_CANDIDATES) + "; use --stratum-col)",
                    file=sys.stderr,
                )
                return 2
    except FileNotFoundError:
        print(f"error: file not found: {args.csv}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if getattr(args, "trail", None):
        from siga_trail import Trail

        judged = res.judged or res.oos
        Trail(args.trail).record(
            "audit",
            payload={
                "file": args.csv or source_desc,
                "n": res.full.n,
                "oos_t": round(judged.t, 4),
                "oos_p": round(judged.p, 6),
                "judged_net": res.assumed_cost is not None,
                "clustered": res.clustered,
            },
            outcome=res.verdict,
        )

    plant_json = None
    if rungs is not None:
        member = log.members(args.stratum)
        idx = [i for i, m in enumerate(member) if m]
        plant_text = render_plant(
            rungs,
            stratum=args.stratum,
            stratum_n=len(idx),
            total_n=len(pnl),
            basis=(f"net of {cost:.4f}/trade" if cost is not None else "gross"),
            control_before=sum(pnl) / len(pnl),
            control_after=sum(contrast(pnl, member, rungs[-1].delta)) / len(pnl),
        )
        plant_json = [
            {"delta": r.delta, "verdict": r.verdict, "mean": r.mean, "t": r.t, "p": r.p, "n": r.n}
            for r in rungs
        ]
    if args.json:
        d = res.to_dict()
        if plant_json is not None:
            d["plant"] = plant_json
        print(json.dumps(d, indent=2))
    else:
        print(render_text(res, source_desc, args.oos))
        if rungs is not None:
            print(plant_text)
    return 0
