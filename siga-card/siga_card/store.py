"""Append-only journal of cards. The decision is immutable once written."""

from __future__ import annotations

import json
import os
import threading

from .card import (
    OPEN,
    SETTLED,
    Card,
    CardError,
    cancel,
    from_dict,
    new_card,
    settle,
    to_dict,
)


class CardStore:
    """JSONL journal with fsync-per-write and no update/delete path.

    Every line is a full card snapshot carrying its own frozen hash. Replaying
    the file reconstructs state; changing a decision requires writing a *new*
    card, never editing an existing line.
    """

    def __init__(self, path: str):
        self._path = os.path.abspath(os.path.expanduser(path))
        self._lock = threading.Lock()
        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    @property
    def path(self) -> str:
        return self._path

    def _append(self, card: Card) -> None:
        line = json.dumps(to_dict(card), separators=(",", ":"), ensure_ascii=False)
        with self._lock, open(self._path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

    def create(
        self,
        *,
        symbol: str,
        direction: str,
        thesis: str,
        entry_lo: float,
        entry_hi: float,
        invalidation: float,
        target: float,
        notional: float,
        created_ms: int,
        expire_ms: int | None = None,
        id: str | None = None,
    ) -> Card:
        card = new_card(
            symbol=symbol,
            direction=direction,
            thesis=thesis,
            entry_lo=entry_lo,
            entry_hi=entry_hi,
            invalidation=invalidation,
            target=target,
            notional=notional,
            created_ms=created_ms,
            expire_ms=expire_ms,
            id=id,
        )
        if any(c.id == card.id for c in self.all()):
            raise CardError(f"card id already exists: {card.id}")
        self._append(card)
        return card

    def get(self, card_id: str) -> Card | None:
        for c in self.all():
            if c.id == card_id:
                return c
        return None

    def all(self) -> list[Card]:
        if not os.path.exists(self._path):
            return []
        with self._lock, open(self._path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        return [from_dict(r) for r in rows]

    def _latest(self, card_id: str) -> Card:
        matches = [c for c in self.all() if c.id == card_id]
        if not matches:
            raise CardError(f"no such card: {card_id}")
        return matches[-1]

    def settle(self, card_id: str, *, exit_price: float, exit_ms: int) -> Card:
        card = self._latest(card_id)
        out = settle(card, exit_price=exit_price, exit_ms=exit_ms)
        self._append(out)
        return out

    def cancel(self, card_id: str) -> Card:
        card = self._latest(card_id)
        out = cancel(card)
        self._append(out)
        return out

    def open_cards(self) -> list[Card]:
        """Latest state of each id that is still open."""
        latest: dict[str, Card] = {}
        for c in self.all():
            latest[c.id] = c
        return [c for c in latest.values() if c.status == OPEN]

    def export_csv(self, path: str) -> int:
        """Write settled cards as ts,pnl,notional,side,symbol for `siga audit`."""
        import csv

        settled: dict[str, Card] = {}
        for c in self.all():
            if c.status == SETTLED:
                settled[c.id] = c
        rows = sorted(settled.values(), key=lambda c: (c.exit_ms or 0, c.id))
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ts", "pnl", "notional", "side", "symbol"])
            for c in rows:
                w.writerow([c.exit_ms, c.pnl, c.notional, c.direction, c.symbol])
        return len(rows)
