"""CLI for pre-registered decision cards.

Wire-in point mirrors siga-audit: ``add_card_parser(subparsers)`` registers a
``card`` command, ``run_card_cli(args)`` executes it with a return code.
"""

from __future__ import annotations

import json
import sys
import time

from .card import CardError, to_dict
from .store import CardStore

DEFAULT_JOURNAL = "cards.jsonl"


def _ms(iso: str | None) -> int:
    """Accept epoch-ms or ISO-8601; default to now."""
    if iso is None:
        return int(time.time() * 1000)
    s = iso.strip()
    if s.isdigit():
        return int(s)
    import datetime

    d = datetime.datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.UTC)
    return int(d.timestamp() * 1000)


def add_card_parser(subparsers) -> None:
    p = subparsers.add_parser("card", help="pre-registered, frozen decision cards")
    ps = p.add_subparsers(dest="card_cmd", required=True)
    lst = ps.add_parser("list", help="list cards with their latest state")
    lst.add_argument("--file", default=DEFAULT_JOURNAL)

    n = ps.add_parser("new", help="freeze a decision before entry")
    n.add_argument("--symbol", required=True)
    n.add_argument("--direction", required=True, choices=["long", "short"])
    n.add_argument("--thesis", required=True, help="why this trade — required, frozen")
    n.add_argument("--entry-lo", type=float, required=True)
    n.add_argument("--entry-hi", type=float, required=True)
    n.add_argument("--invalidation", type=float, required=True)
    n.add_argument("--target", type=float, required=True)
    n.add_argument("--notional", type=float, required=True)
    n.add_argument("--created", default=None, help="epoch-ms or ISO-8601 (default: now)")
    n.add_argument("--expire", default=None, help="epoch-ms or ISO-8601 time boundary")
    n.add_argument("--id", default=None)
    n.add_argument("--file", default=DEFAULT_JOURNAL)

    s = ps.add_parser("settle", help="record the outcome of an open card")
    s.add_argument("id")
    s.add_argument("--exit-price", type=float, required=True)
    s.add_argument("--exit", default=None, help="epoch-ms or ISO-8601 (default: now)")
    s.add_argument("--file", default=DEFAULT_JOURNAL)

    c = ps.add_parser("cancel", help="cancel before entry (never counted as PnL)")
    c.add_argument("id")
    c.add_argument("--file", default=DEFAULT_JOURNAL)

    e = ps.add_parser("export", help="export settled cards to audit CSV")
    e.add_argument("--out", required=True)
    e.add_argument("--file", default=DEFAULT_JOURNAL)

    sh = ps.add_parser("show", help="show one card")
    sh.add_argument("id")
    sh.add_argument("--file", default=DEFAULT_JOURNAL)


def run_card_cli(args) -> int:
    store = CardStore(getattr(args, "file", DEFAULT_JOURNAL))
    cmd = args.card_cmd

    if cmd == "new":
        card = store.create(
            symbol=args.symbol,
            direction=args.direction,
            thesis=args.thesis,
            entry_lo=args.entry_lo,
            entry_hi=args.entry_hi,
            invalidation=args.invalidation,
            target=args.target,
            notional=args.notional,
            created_ms=_ms(args.created),
            expire_ms=_ms(args.expire) if args.expire else None,
            id=args.id,
        )
        print(json.dumps(to_dict(card), ensure_ascii=False, indent=2))
        return 0

    if cmd == "list":
        cards = store.all()
        if not cards:
            print("no cards")
            return 0
        for c in cards:
            print(
                f"{c.id:48s} {c.status:9s} {c.direction:5s} "
                f"R={c.r_multiple if c.r_multiple is not None else '-':>8} "
                f"pnl={c.pnl if c.pnl is not None else '-':>10}  {c.thesis[:40]}"
            )
        return 0

    if cmd == "show":
        card = store.get(args.id)
        if card is None:
            print(f"no such card: {args.id}", file=sys.stderr)
            return 2
        print(json.dumps(to_dict(card), ensure_ascii=False, indent=2))
        return 0

    if cmd == "settle":
        card = store.settle(args.id, exit_price=args.exit_price, exit_ms=_ms(args.exit))
        print(
            f"{card.id} settled: exit={card.exit_price} "
            f"pnl={card.pnl} R={card.r_multiple}"
        )
        return 0

    if cmd == "cancel":
        card = store.cancel(args.id)
        print(f"{card.id} cancelled")
        return 0

    if cmd == "export":
        n = store.export_csv(args.out)
        print(f"exported {n} settled cards -> {args.out}")
        return 0

    raise CardError(f"unknown card command: {cmd}")
