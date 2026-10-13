"""CLI for the audit engine — ``siga audit trades.csv``.

CSV format: one row per trade, chronological. A P&L column is required
(detected among: pnl, pnl_usd, p&l, profit, net, return, ret, pl — or set
explicitly with --column). An optional notional column (notional, value,
trade_value) enables --cost-bps.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys

from siga_audit.audit import DEFAULT_MIN_OOS, DEFAULT_OOS_FRAC, AuditResult, run_audit

_PNL_CANDIDATES = ("pnl", "pnl_usd", "p&l", "profit", "net_pnl", "net", "return", "ret", "pl")
_NOTIONAL_CANDIDATES = ("notional", "notional_usd", "trade_value", "value")


def _parse_number(raw: str) -> float:
    return float(raw.strip().replace("$", "").replace(",", ""))


def _pick_column(header: list[str], candidates: tuple[str, ...]) -> str | None:
    lowered = [h.strip().lower() for h in header]
    for cand in candidates:
        if cand in lowered:
            return header[lowered.index(cand)]
    return None


def load_trades_csv(path: str, column: str | None = None) -> tuple[list[float], list[float] | None]:
    """Return (pnl_series, notional_series_or_None) in row order."""
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

        pnl: list[float] = []
        notional: list[float] = []
        for i, row in enumerate(reader, start=2):  # header is line 1
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
    if len(pnl) < 10:
        raise ValueError(f"need at least 10 trades to audit, got {len(pnl)}")
    return pnl, (notional if notional_col else None)


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

    sig = "significant" if res.oos.p < 0.05 else "not significant"
    lines.append(
        f"CHECK 01  OOS verdict ......... t={res.oos.t:+.2f}, p={fmt_p(res.oos.p)} ({sig})"
    )
    if res.assumed_cost is not None and res.net_at_cost is not None:
        net = res.net_at_cost
        lines.append(
            f"CHECK 02  Cost sensitivity .... assumed {res.assumed_cost:.4f}/trade -> "
            f"net mean {fmt_money(net.mean)}, t={net.t:+.2f}, p={fmt_p(net.p)}"
        )
    else:
        lines.append(
            f"CHECK 02  Cost sensitivity .... gross edge {fmt_money(res.breakeven_cost)}/trade — "
            "any round-trip cost above this kills it"
        )
    guard = (
        f"OOS n={res.oos.n} >= {res.min_oos} (ok)"
        if res.oos.n >= res.min_oos
        else f"OOS n={res.oos.n} < {res.min_oos} -> verdict withheld"
    )
    lines.append(f"CHECK 03  Small-sample guard .. {guard}")
    lines.append("")
    lines.append(f"VERDICT: {res.verdict}")
    for r in res.reasons:
        lines.append(f"  - {r}")
    return "\n".join(lines)


def add_audit_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "audit", help="audit a backtest trade log (CSV) and print a verdict"
    )
    p.add_argument("csv", help="path to trades CSV (one row per trade, chronological)")
    p.add_argument("--column", default=None, help="name of the P&L column (auto-detected by default)")
    p.add_argument("--cost", type=float, default=None,
                   help="assumed fixed cost per trade (same units as P&L)")
    p.add_argument("--cost-bps", type=float, default=None,
                   help="assumed round-trip cost in bps of notional (requires a notional column)")
    p.add_argument("--oos", type=float, default=DEFAULT_OOS_FRAC,
                   help=f"out-of-sample fraction (default {DEFAULT_OOS_FRAC})")
    p.add_argument("--min-oos", type=int, default=DEFAULT_MIN_OOS,
                   help=f"minimum OOS trades before any verdict (default {DEFAULT_MIN_OOS})")
    p.add_argument("--json", action="store_true", help="print machine-readable JSON")


def run_audit_cli(args: argparse.Namespace) -> int:
    try:
        pnl, notional = load_trades_csv(args.csv, args.column)
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
        res = run_audit(
            pnl,
            oos_frac=args.oos,
            min_oos=args.min_oos,
            assumed_cost=cost,
        )
    except FileNotFoundError:
        print(f"error: file not found: {args.csv}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
    else:
        print(render_text(res, args.csv, args.oos))
    return 0
