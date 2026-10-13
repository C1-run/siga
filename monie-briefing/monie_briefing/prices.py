"""Price sources for monie-briefing."""
from __future__ import annotations


import logging
import os
import time
from typing import Protocol


import httpx


logger = logging.getLogger(__name__)


# CoinGecko uses slugs, not tickers
COINGECKO_IDS: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "LINK": "chainlink",
}


COINGECKO_BASE = "https://api.coingecko.com/api/v3"


class PriceSource(Protocol):
    def get_prices(self, symbols: list[str]) -> dict[str, float]: ...


class StubPriceSource:
    """Returns 0.0 for every symbol. For tests and offline use."""

    def get_prices(self, symbols: list[str]) -> dict[str, float]:
        return {s: 0.0 for s in symbols}


class CoinGeckoPriceSource:
    """Fetches USD prices from CoinGecko with in-memory TTL cache.

    Behavior:
    - Known symbols with fresh cache -> no network call
    - Unknown symbols -> skipped with a warning (no raise)
    - Network/HTTP error -> returns whatever is cached, empty for the rest
    """

    def __init__(
        self,
        cache_ttl: float = 60.0,
        timeout: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.cache_ttl = cache_ttl
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None
        self._cache: dict[str, tuple[float, float]] = {}  # symbol -> (price, monotonic_ts)

    def get_prices(self, symbols: list[str]) -> dict[str, float]:
        symbols = [s.upper().strip() for s in symbols]
        now = time.monotonic()
        result: dict[str, float] = {}
        to_fetch: list[str] = []

        for s in symbols:
            if s not in COINGECKO_IDS:
                logger.warning("unknown symbol, skipping: %s", s)
                continue
            cached = self._cache.get(s)
            if cached and now - cached[1] < self.cache_ttl:
                result[s] = cached[0]
            else:
                to_fetch.append(s)

        if to_fetch:
            fetched = self._fetch(to_fetch)
            for s, p in fetched.items():
                self._cache[s] = (p, now)
                result[s] = p
            # fall back to stale cache if fetch failed
            for s in to_fetch:
                if s not in fetched and s in self._cache:
                    result[s] = self._cache[s][0]

        return result

    def _fetch(self, symbols: list[str]) -> dict[str, float]:
        ids = [COINGECKO_IDS[s] for s in symbols]
        try:
            resp = self._client.get(
                f"{COINGECKO_BASE}/simple/price",
                params={"ids": ",".join(ids), "vs_currencies": "usd"},
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("CoinGecko request failed: %s", e)
            return {}

        try:
            data = resp.json()
        except ValueError:
            logger.error("CoinGecko returned non-JSON response")
            return {}

        out: dict[str, float] = {}
        for s in symbols:
            entry = data.get(COINGECKO_IDS[s])
            if isinstance(entry, dict) and "usd" in entry:
                try:
                    out[s] = float(entry["usd"])
                except (TypeError, ValueError):
                    logger.warning("bad price for %s: %r", s, entry.get("usd"))
        return out

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


# ---------- module-level default ----------


_default: PriceSource | None = None


def _make_default() -> PriceSource:
    if os.environ.get("MONIE_PRICE_SOURCE") == "stub":
        return StubPriceSource()
    return CoinGeckoPriceSource()


def get_prices(symbols: list[str]) -> dict[str, float]:
    global _default
    if _default is None:
        _default = _make_default()
    return _default.get_prices(symbols)


def set_source(source: PriceSource) -> None:
    global _default
    _default = source


# ---------- market data (24h/7d changes) ----------


def get_market_data(symbols: list[str], client: httpx.Client | None = None) -> dict[str, dict]:
    """Fetch 24h and 7d price changes from CoinGecko /coins/markets.

    Returns {symbol: {change_24h: float|None, change_7d: float|None}}.
    Falls back to empty dict on error. Symbols without CoinGecko IDs are skipped.
    """
    symbols = [s.upper().strip() for s in symbols]
    ids = []
    sym_by_id = {}
    for s in symbols:
        cg_id = COINGECKO_IDS.get(s)
        if cg_id:
            ids.append(cg_id)
            sym_by_id[cg_id] = s
    if not ids:
        return {}

    _client = client or httpx.Client(timeout=10.0)
    owns_client = client is None
    try:
        resp = _client.get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": ",".join(ids),
                "price_change_percentage": "24h,7d",
            },
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.error("CoinGecko market data request failed: %s", e)
        return {}
    finally:
        if owns_client:
            _client.close()

    try:
        data = resp.json()
    except ValueError:
        return {}

    out: dict[str, dict] = {}
    for entry in data:
        cg_id = entry.get("id")
        sym = sym_by_id.get(cg_id)
        if not sym:
            continue
        out[sym] = {
            "change_24h": entry.get("price_change_percentage_24h_in_currency"),
            "change_7d": entry.get("price_change_percentage_7d_in_currency"),
        }
    return out
