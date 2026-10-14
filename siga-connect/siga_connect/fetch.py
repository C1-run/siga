"""Unified fetch interface — pull trade history from any supported source."""

from __future__ import annotations

from siga_connect.connectors import binance, dune, helius
from siga_connect.models import FetchResult


def fetch_trades(
    source: str,
    *,
    symbol: str | None = None,
    query_id: int | None = None,
    address: str | None = None,
    api_key: str | None = None,
    api_secret: str | None = None,
    limit: int = 500,
) -> FetchResult:
    """Fetch trade history from a supported source.

    Args:
        source: one of "binance", "dune", "helius"
        symbol: trading pair (required for binance)
        query_id: Dune query ID (required for dune)
        address: Solana address (required for helius)
        api_key: API key (required for dune/helius, optional for binance public data)
        api_secret: API secret (required for binance private endpoints)
        limit: max records to fetch (default 500)

    Returns:
        FetchResult with normalized pnl/notional series
    """
    source = source.lower()

    if source == "binance":
        if not symbol:
            raise ValueError("--symbol is required for binance")
        return binance.fetch_trades(
            symbol=symbol,
            api_key=api_key,
            api_secret=api_secret,
            limit=limit,
        )

    if source == "dune":
        if not query_id:
            raise ValueError("--query-id is required for dune")
        if not api_key:
            raise ValueError("--api-key is required for dune")
        return dune.fetch_trades(query_id=query_id, api_key=api_key, limit=limit)

    if source == "helius":
        if not address:
            raise ValueError("--address is required for helius")
        if not api_key:
            raise ValueError("--api-key is required for helius")
        return helius.fetch_trades(address=address, api_key=api_key, limit=limit)

    raise ValueError(f"unsupported source {source!r} — choose from: binance, dune, helius")
