"""Binance connector — public aggregate trades or authenticated user trades."""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse

import httpx

from siga_connect.models import FetchResult

_BASE = "https://api.binance.com"


def _sign(query_string: str, secret: str) -> str:
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()


def fetch_trades(
    symbol: str,
    api_key: str | None = None,
    api_secret: str | None = None,
    limit: int = 500,
) -> FetchResult:
    """Fetch Binance trade history.

    Two modes:
    - Public: if no api_key, fetches aggregate trades (market data, not your fills)
    - Private: if api_key + api_secret provided, fetches your actual trades

    For audit purposes, private mode is what you want. Public mode gives you
    market data which is NOT your strategy's P&L.
    """
    symbol = symbol.upper()

    if api_key and api_secret:
        return _fetch_private_trades(symbol, api_key, api_secret, limit)
    return _fetch_public_trades(symbol, limit)


def _fetch_public_trades(symbol: str, limit: int) -> FetchResult:
    """Fetch aggregate trades (public market data, no auth needed).

    WARNING: This is market data, not your strategy's fills. The P&L
    computed here assumes you bought at every trade price — useful for
    sanity checks, not for auditing your actual strategy.
    """
    url = f"{_BASE}/api/v3/aggTrades?symbol={symbol}&limit={limit}"
    with httpx.Client(timeout=30) as client:
        resp = client.get(url)
        resp.raise_for_status()
        trades = resp.json()

    # For public aggTrades, we simulate P&L as if you went long at each trade
    # and sold at the next. This is a rough proxy — not real strategy P&L.
    prices = [float(t["p"]) for t in trades]
    qty = [float(t["q"]) for t in trades]

    pnl: list[float] = []
    notional: list[float] = []
    for i in range(len(prices) - 1):
        pnl.append((prices[i + 1] - prices[i]) * qty[i])
        notional.append(prices[i] * qty[i])

    return FetchResult(
        pnl=pnl,
        notional=notional,
        source=f"binance:public:{symbol}",
        n_trades=len(pnl),
    )


def _fetch_private_trades(
    symbol: str, api_key: str, api_secret: str, limit: int
) -> FetchResult:
    """Fetch authenticated user trade history from /api/v3/myTrades."""
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "timestamp": timestamp,
        "limit": min(limit, 1000),  # Binance max
    }
    query_string = urllib.parse.urlencode(params)
    signature = _sign(query_string, api_secret)
    params["signature"] = signature

    url = f"{_BASE}/api/v3/myTrades"
    headers = {"X-MBX-APIKEY": api_key}

    with httpx.Client(timeout=30) as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        trades = resp.json()

    # Binance myTrades returns: id, orderId, price, qty, quoteQty,
    # commission, commissionAsset, time, isBuyer, isMaker, ...
    pnl: list[float] = []
    notional: list[float] = []

    for t in trades:
        price = float(t["price"])
        qty = float(t["qty"])
        quote_qty = float(t["quoteQty"])
        commission = float(t["commission"])
        is_buyer = t["isBuyer"]

        # For audit purposes, we want net P&L per trade.
        # If you bought: you spent quote_qty + commission
        # If you sold: you received quote_qty - commission
        # We compute realized P&L as the delta from the *previous* trade
        # of the opposite side. This is a simplification — a real audit
        # would need to match buy/sell pairs.
        #
        # For now, we return the quoteQty as notional and compute
        # a simple P&L assuming round-trip matching.
        notional.append(quote_qty)

        # Simplified: P&L = quoteQty delta between consecutive opposite trades
        # This is a placeholder — proper P&L requires position tracking.
        pnl.append(0.0)  # placeholder — see below

    # Recompute P&L with proper round-trip matching
    pnl = _compute_round_trip_pnl(trades)

    return FetchResult(
        pnl=pnl,
        notional=notional[: len(pnl)] if pnl else None,
        source=f"binance:{symbol}",
        n_trades=len(pnl),
    )


def _compute_round_trip_pnl(trades: list[dict]) -> list[float]:
    """Compute per-trade P&L by matching buy/sell pairs (FIFO).

    Binance gives you individual fills. To compute P&L, we match
    each sell with the earliest unmatched buy.
    """
    pnl: list[float] = []
    buy_queue: list[tuple[float, float]] = []  # (price, qty)

    for t in trades:
        price = float(t["price"])
        qty = float(t["qty"])
        commission = float(t["commission"])
        is_buyer = t["isBuyer"]

        if is_buyer:
            buy_queue.append((price, qty))
        else:
            # Sell: match against oldest buys
            remaining = qty
            trade_pnl = 0.0
            while remaining > 0 and buy_queue:
                buy_price, buy_qty = buy_queue[0]
                match_qty = min(remaining, buy_qty)
                trade_pnl += (price - buy_price) * match_qty
                remaining -= match_qty
                if match_qty >= buy_qty:
                    buy_queue.pop(0)
                else:
                    buy_queue[0] = (buy_price, buy_qty - match_qty)

            # Subtract commission (both sides)
            trade_pnl -= commission
            # Approximate buy-side commission: 0.1% of matched notional
            trade_pnl -= trade_pnl * 0.001 if trade_pnl > 0 else 0

            pnl.append(trade_pnl)

    return pnl
