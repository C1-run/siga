"""siga-card — pre-registered decision cards, frozen before entry.

A card is the object siga was missing: it records the *decision* (direction,
thesis, entry zone, invalidation, target, expiry) at the moment it is made,
not after the outcome is known. Once created a card is immutable; the only
later events are settlement (outcome) and explicit cancellation. Settled
cards export straight into the ``ts,pnl,notional`` CSV that ``siga audit``
consumes, so the verdict engine judges the plan you actually committed to.

Concept distilled from ZenTrade's opportunity card (wuyangfan234/zentrade,
MIT original code). No code was copied: this is an independent, zero-dependency
implementation under siga's MIT license. ZenTrade's repo bundles third-party
GPL-3.0 / MPL-2.0 / CC BY-NC-SA components; none of them are used here.
"""

from __future__ import annotations

from .card import (
    CANCELLED,
    OPEN,
    SETTLED,
    Card,
    CardError,
    cancel,
    freeze,
    from_dict,
    new_card,
    settle,
    to_dict,
    validate_geometry,
)
from .store import CardStore

__all__ = [
    "CANCELLED",
    "OPEN",
    "SETTLED",
    "Card",
    "CardError",
    "CardStore",
    "cancel",
    "freeze",
    "from_dict",
    "new_card",
    "settle",
    "to_dict",
    "validate_geometry",
]

__version__ = "0.1.0"
