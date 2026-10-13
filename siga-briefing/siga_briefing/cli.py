"""Command-line entrypoint — generate the morning briefing or manage portfolio.

Run as ``python -m siga_briefing.cli``.

Briefing mode:
    ``python -m siga_briefing.cli [--symbol SOL/USDC] [--out-dir DIR]``

Portfolio mode:
    ``python -m siga_briefing.cli portfolio [--file PATH] list|add|remove|import|value``

Exit codes:
    0  success
    1  unexpected failure
    2  usage / configuration error
"""

import argparse
import os
import sys
from datetime import date, datetime

from siga_briefing.briefing import MorningBriefing
from siga_briefing.prices import get_prices


# ---------------------------------------------------------------------------
# Portfolio helpers
# ---------------------------------------------------------------------------


def _portfolio_path(args) -> str:
    """Resolve the portfolio file path from --file or default."""
    from siga_briefing.portfolio import DEFAULT_PATH
    return str(getattr(args, "file", None) or DEFAULT_PATH)


def _cmd_portfolio_add(args) -> int:
    from siga_briefing.portfolio import Holding, Portfolio

    path = _portfolio_path(args)
    pf = Portfolio.load(path)
    holding = Holding(
        symbol=args.symbol,
        quantity=args.quantity,
        cost_basis=args.cost,
        acquired_at=date.fromisoformat(args.date) if args.date else date.today(),
        notes=args.notes or "",
    )
    pf.add(holding)
    pf.save(path)
    merged = pf.find(args.symbol.upper())
    print(f"Added {merged.symbol}: {merged.quantity} @ ${merged.cost_basis:.2f}")
    return 0


def _cmd_portfolio_import(args) -> int:
    from siga_briefing.portfolio import Portfolio

    path = _portfolio_path(args)
    pf = Portfolio.load(path)
    new_pf = Portfolio.from_csv(args.csv)
    for h in new_pf:
        pf.add(h)
    pf.save(path)
    print(f"Imported {len(new_pf)} holding(s) into portfolio ({len(pf)} total)")
    return 0


def _cmd_portfolio_list(args) -> int:
    from siga_briefing.portfolio import Portfolio

    path = _portfolio_path(args)
    pf = Portfolio.load(path)
    if not pf:
        print("No holdings yet.\n")
        print("Quick start:")
        print("  siga add BTC 0.5@62000")
        print("  siga add ETH 5@3200")
        print("  siga brief")
        return 0
    print(f"{'Symbol':<8} {'Qty':>12} {'Cost':>12} {'Total Cost':>14}")
    print("-" * 48)
    for h in pf:
        cost_str = f"${h.cost_basis:.2f}" if h.has_cost else "—"
        print(f"{h.symbol:<8} {h.quantity:>12.4f} {cost_str:>12} ${h.cost_total:>13.2f}")
    print(f"\nTotal cost: ${pf.total_cost():,.2f}")
    return 0


def _cmd_portfolio_remove(args) -> int:
    from siga_briefing.portfolio import Portfolio

    path = _portfolio_path(args)
    pf = Portfolio.load(path)
    removed = pf.remove(args.symbol)
    if removed is None:
        print(f"Symbol {args.symbol.upper()} not found in portfolio.", file=sys.stderr)
        return 1
    pf.save(path)
    print(f"Removed {removed.symbol}: {removed.quantity} @ ${removed.cost_basis:.2f}")
    return 0


def _cmd_portfolio_value(args) -> int:
    from siga_briefing.portfolio import Portfolio

    path = _portfolio_path(args)
    pf = Portfolio.load(path)
    if not pf:
        print("Portfolio is empty.")
        return 0

    prices = get_prices(pf.symbols())
    missing = [s for s in pf.symbols() if s not in prices]
    if missing:
        print(f"note: no price for {', '.join(missing)}", file=sys.stderr)

    result = pf.pnl(prices)
    alloc = pf.allocation(prices)

    t = result["total"]
    print(f"\n{'Symbol':<8} {'Qty':>10} {'Price':>12} {'Value':>12} {'P&L':>12} {'P&L%':>8} {'Alloc':>7}")
    print("-" * 73)
    for sym, s in result["per_symbol"].items():
        h = pf.find(sym)
        price = prices.get(sym)
        price_str = f"${price:,.2f}" if price else "\u2014"
        alloc_pct = alloc.get(sym, 0.0)
        print(
            f"{sym:<8} {h.quantity:>10.4f} "
            f"{price_str:>12} ${s['value']:>11.2f} "
            f"${s['pnl']:>+11.2f} {s['pnl_pct']:>+7.1f}% "
            f"{alloc_pct:>6.1f}%"
        )
    print("-" * 73)
    print(f"{'TOTAL':<8} {'':>10} {'':>12} ${t['value']:>11.2f} ${t['pnl']:>+11.2f} {t['pnl_pct']:>+7.1f}%")
    print(f"\nTotal cost:  ${t['cost']:,.2f}")
    print(f"Total value: ${t['value']:,.2f}")
    print(f"Total P&L:   ${t['pnl']:>+,.2f} ({t['pnl_pct']:+.1f}%)")
    return 0


# ---------------------------------------------------------------------------
# Briefing subcommand (portfolio-aware)
# ---------------------------------------------------------------------------


def _cmd_briefing(args) -> int:
    from siga_briefing.briefing import PortfolioBriefing
    from siga_briefing.portfolio import Portfolio, DEFAULT_PATH

    path = getattr(args, "file", None)
    pf = Portfolio.load(path or DEFAULT_PATH)
    if not pf:
        print("No holdings yet.\n")
        print("Quick start:")
        print("  siga add BTC 0.5@62000")
        print("  siga add ETH 5@3200")
        print("  siga brief")
        return 0

    briefing = PortfolioBriefing(pf)
    report = briefing.generate()
    markdown = briefing.render_markdown(report)
    print(markdown)

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)
        out = os.path.join(args.out_dir, datetime.now().strftime("briefing-%Y%m%d.md"))
        with open(out, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"[siga-briefing] wrote {out}", file=sys.stderr)

    return 0


# ---------------------------------------------------------------------------
# Portfolio subcommand parser
# ---------------------------------------------------------------------------


def _add_portfolio_parser(subparsers) -> None:
    p = subparsers.add_parser("portfolio", help="manage your portfolio")
    p.add_argument("--file", default=None, help="portfolio file path (default: ~/.siga/portfolio.json)")
    ps = p.add_subparsers(dest="portfolio_cmd", required=True)

    # portfolio add
    add_p = ps.add_parser("add", help="add a holding")
    add_p.add_argument("symbol", help="coin symbol (e.g. SOL, BTC, ETH)")
    add_p.add_argument("quantity", type=float, help="quantity held")
    add_p.add_argument("--cost", type=float, default=0.0, help="cost basis per unit (USD, optional)")
    add_p.add_argument("--date", default=None, help="acquired date YYYY-MM-DD (default: today)")
    add_p.add_argument("--notes", default=None, help="optional note")

    # portfolio import
    imp_p = ps.add_parser("import", help="import holdings from CSV")
    imp_p.add_argument("csv", help="path to CSV file")

    # portfolio list
    ps.add_parser("list", help="list all holdings")

    # portfolio remove
    rm_p = ps.add_parser("remove", help="remove a holding by symbol")
    rm_p.add_argument("symbol", help="coin symbol to remove")

    # portfolio value
    ps.add_parser("value", help="show current value and P&L")

    # portfolio brief
    brief_p = ps.add_parser("brief", help="generate portfolio-aware briefing")
    brief_p.add_argument("--out-dir", default=None, help="write briefing to directory")


def _add_briefing_parser(subparsers) -> None:
    p = subparsers.add_parser("brief", help="generate portfolio-aware morning briefing")
    p.add_argument("--file", default=None, help="portfolio file path (default: ~/.siga/portfolio.json)")
    p.add_argument("--out-dir", default=None, help="write briefing-YYYYMMDD.md into this directory")


# ---------------------------------------------------------------------------
# Briefing CLI (existing)
# ---------------------------------------------------------------------------


def _parse_args(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="siga",
        description="siga-briefing — portfolio-aware crypto briefing.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Top-level aliases (short form) — always use default portfolio path
    add_p = subparsers.add_parser("add", help="add a holding (shorthand)")
    add_p.add_argument("symbol", help="coin symbol (e.g. BTC, ETH, SOL)")
    add_p.add_argument("quantity", type=float, help="quantity held")
    add_p.add_argument("--cost", type=float, default=0.0, help="cost basis per unit (optional)")
    add_p.add_argument("--date", default=None, help="acquired date YYYY-MM-DD")
    add_p.add_argument("--notes", default=None, help="optional note")

    subparsers.add_parser("list", help="list all holdings")
    subparsers.add_parser("value", help="show current value and P&L")

    rm_p = subparsers.add_parser("remove", help="remove a holding")
    rm_p.add_argument("symbol", help="coin symbol to remove")

    imp_p = subparsers.add_parser("import", help="import from CSV")
    imp_p.add_argument("csv", help="path to CSV file")

    brief_p = subparsers.add_parser("brief", help="generate portfolio-aware briefing")
    brief_p.add_argument("--out-dir", default=None, help="write briefing to directory")

    # Backtest audit (siga-audit)
    from siga_audit.cli import add_audit_parser

    add_audit_parser(subparsers)

    # Full portfolio subcommand (advanced, with --file)
    _add_portfolio_parser(subparsers)

    return parser.parse_args(argv)


def _run(args) -> int:
    # Top-level aliases
    if args.command == "add":
        return _cmd_portfolio_add(args)
    if args.command == "list":
        return _cmd_portfolio_list(args)
    if args.command == "value":
        return _cmd_portfolio_value(args)
    if args.command == "remove":
        return _cmd_portfolio_remove(args)
    if args.command == "import":
        return _cmd_portfolio_import(args)
    if args.command == "brief":
        return _cmd_briefing(args)
    if args.command == "audit":
        from siga_audit.cli import run_audit_cli

        return run_audit_cli(args)

    # Full portfolio subcommand
    if args.command == "portfolio":
        dispatch = {
            "add": _cmd_portfolio_add,
            "import": _cmd_portfolio_import,
            "list": _cmd_portfolio_list,
            "remove": _cmd_portfolio_remove,
            "value": _cmd_portfolio_value,
            "brief": _cmd_briefing,
        }
        return dispatch[args.portfolio_cmd](args)

    # No command — show help
    return 0


def main(argv=None) -> int:
    """Run the briefing once; returns a process exit code."""
    args = _parse_args(argv)
    if args.command is None and getattr(args, "lookback_hours", 24) < 1:
        print("error: --lookback-hours must be >= 1", file=sys.stderr)
        return 2
    try:
        return _run(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
