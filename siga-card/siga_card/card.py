"""The frozen decision card and its settlement math."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace

OPEN = "open"
SETTLED = "settled"
CANCELLED = "cancelled"
VALID_DIRECTIONS = ("long", "short")
VALID_STATUS = (OPEN, SETTLED, CANCELLED)


class CardError(ValueError):
    """Raised when a card is malformed, mutated, or settled illegally."""


@dataclass(frozen=True)
class Card:
    id: str
    created_ms: int
    symbol: str
    direction: str
    thesis: str
    entry_lo: float
    entry_hi: float
    invalidation: float
    target: float
    notional: float
    expire_ms: int | None = None
    status: str = OPEN
    exit_price: float | None = None
    exit_ms: int | None = None
    pnl: float | None = None
    r_multiple: float | None = None

    @property
    def entry_mid(self) -> float:
        return (self.entry_lo + self.entry_hi) / 2.0

    @property
    def risk_per_unit(self) -> float:
        """Distance from entry mid to invalidation, always positive."""
        return abs(self.entry_mid - self.invalidation)

    @property
    def reward_per_unit(self) -> float:
        return abs(self.target - self.entry_mid)

    @property
    def rr(self) -> float:
        """Planned reward:risk. Geometric only — not an edge estimate."""
        r = self.risk_per_unit
        return self.reward_per_unit / r if r else math.inf

    @property
    def frozen(self) -> str:
        """Hash of the decision fields only. Never changes on settlement."""
        return freeze(self)


def _num(v: object, name: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise CardError(f"{name} must be a number")
    x = float(v)
    if not math.isfinite(x) or x <= 0:
        raise CardError(f"{name} must be finite and > 0")
    return x


def validate_geometry(card: Card) -> None:
    """Fail closed on a card that cannot be settled unambiguously.

    long  : invalidation < entry_lo <= entry_hi < target
    short : target < entry_lo <= entry_hi < invalidation
    """
    if card.direction not in VALID_DIRECTIONS:
        raise CardError(f"direction must be one of {VALID_DIRECTIONS}")
    if not isinstance(card.thesis, str) or not card.thesis.strip():
        raise CardError("thesis is required and must be non-empty")
    if not isinstance(card.symbol, str) or not card.symbol.strip():
        raise CardError("symbol must be non-empty")
    if not isinstance(card.created_ms, int) or card.created_ms <= 0:
        raise CardError("created_ms must be a positive epoch-ms integer")
    if card.expire_ms is not None and (
        not isinstance(card.expire_ms, int) or card.expire_ms <= card.created_ms
    ):
        raise CardError("expire_ms must be an epoch-ms integer after created_ms")

    lo, hi = _num(card.entry_lo, "entry_lo"), _num(card.entry_hi, "entry_hi")
    inv, tgt = _num(card.invalidation, "invalidation"), _num(card.target, "target")
    _num(card.notional, "notional")
    if lo > hi:
        raise CardError("entry_lo must be <= entry_hi")
    if card.direction == "long" and not (inv < lo <= hi < tgt):
        raise CardError("long card requires invalidation < entry_lo <= entry_hi < target")
    if card.direction == "short" and not (tgt < lo <= hi < inv):
        raise CardError("short card requires target < entry_lo <= entry_hi < invalidation")
    if card.status not in VALID_STATUS:
        raise CardError(f"status must be one of {VALID_STATUS}")


def freeze(card: Card) -> str:
    """Canonical hash of the decision. Outcome fields are deliberately excluded."""
    decision = {
        "symbol": card.symbol,
        "direction": card.direction,
        "thesis": card.thesis.strip(),
        "entry_lo": card.entry_lo,
        "entry_hi": card.entry_hi,
        "invalidation": card.invalidation,
        "target": card.target,
        "notional": card.notional,
        "created_ms": card.created_ms,
        "expire_ms": card.expire_ms,
    }
    blob = json.dumps(decision, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def new_card(
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
    """Create a pre-registered card. Refuse a card that cannot be judged later."""
    card = Card(
        id=id or "",
        created_ms=created_ms,
        symbol=symbol.strip().upper(),
        direction=direction.strip().lower(),
        thesis=thesis.strip(),
        entry_lo=float(entry_lo),
        entry_hi=float(entry_hi),
        invalidation=float(invalidation),
        target=float(target),
        notional=float(notional),
        expire_ms=expire_ms,
    )
    validate_geometry(card)
    cid = id or f"{card.symbol}-{created_ms}-{card.frozen[:12]}"
    return replace(card, id=cid)


def settle(card: Card, *, exit_price: float, exit_ms: int) -> Card:
    """Settle an open card. Returns a new Card; the original stays immutable."""
    if card.status != OPEN:
        raise CardError(f"card {card.id} is already {card.status}")
    px = _num(exit_price, "exit_price")
    if not isinstance(exit_ms, int) or exit_ms < card.created_ms:
        raise CardError("exit_ms must be an epoch-ms integer >= created_ms")
    if card.expire_ms is not None and exit_ms > card.expire_ms:
        raise CardError(
            f"card {card.id} expired at {card.expire_ms}; do not settle past the time boundary"
        )
    sign = 1.0 if card.direction == "long" else -1.0
    pnl = sign * (px - card.entry_mid) / card.entry_mid * card.notional
    r = sign * (px - card.entry_mid) / card.risk_per_unit if card.risk_per_unit else math.inf
    return replace(
        card,
        status=SETTLED,
        exit_price=px,
        exit_ms=exit_ms,
        pnl=round(pnl, 6),
        r_multiple=round(r, 6),
    )


def cancel(card: Card) -> Card:
    """Cancel before entry. A cancelled card is never settled or exported as PnL."""
    if card.status != OPEN:
        raise CardError(f"card {card.id} is already {card.status}")
    return replace(card, status=CANCELLED)


def to_dict(card: Card) -> dict:
    return {
        "id": card.id,
        "created_ms": card.created_ms,
        "symbol": card.symbol,
        "direction": card.direction,
        "thesis": card.thesis,
        "entry_lo": card.entry_lo,
        "entry_hi": card.entry_hi,
        "invalidation": card.invalidation,
        "target": card.target,
        "notional": card.notional,
        "expire_ms": card.expire_ms,
        "status": card.status,
        "exit_price": card.exit_price,
        "exit_ms": card.exit_ms,
        "pnl": card.pnl,
        "r_multiple": card.r_multiple,
        "frozen": card.frozen,
    }


def from_dict(raw: dict) -> Card:
    """Rehydrate a card from the append-only journal, checking its frozen hash."""
    d = dict(raw)
    recorded = d.pop("frozen", None)
    card = Card(**d)
    validate_geometry(card)
    if recorded is not None and recorded != card.frozen:
        raise CardError(f"card {card.id} was tampered with: frozen hash mismatch")
    if (
        card.status == SETTLED
        and (card.pnl is None or card.exit_price is None or card.exit_ms is None)
    ):
        raise CardError(f"settled card {card.id} is missing outcome fields")
    return card
