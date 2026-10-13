"""News sources for siga-briefing — per-holding news aggregation."""
from __future__ import annotations


import logging
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


import httpx


logger = logging.getLogger(__name__)


# ---------- data model ----------


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str | None = None
    symbols: list[str] = field(default_factory=list)


# ---------- symbol tagging ----------


SYMBOL_ALIASES: dict[str, list[str]] = {
    "BTC": ["bitcoin", "btc"],
    "ETH": ["ethereum", "eth", "ether"],
    "SOL": ["solana", "sol"],
    "DOGE": ["dogecoin", "doge"],
    "USDT": ["tether", "usdt"],
    "USDC": ["usd-coin", "usdc"],
    "BNB": ["binancecoin", "bnb", "binance"],
    "XRP": ["ripple", "xrp"],
    "ADA": ["cardano", "ada"],
    "AVAX": ["avalanche", "avax"],
    "DOT": ["polkadot", "dot"],
    "LINK": ["chainlink", "link"],
}

# Pre-compile word-boundary patterns per alias.
# Built once at import time for performance.
_ALIAS_PATTERNS: dict[str, list[tuple[str, re.Pattern]]] = {}
for _sym, _aliases in SYMBOL_ALIASES.items():
    _AliasPatternList = []
    for _alias in _aliases:
        # Use \b for word boundaries; re.escape in case alias has special chars
        _pat = re.compile(r"(?<!\w)" + re.escape(_alias) + r"(?!\w)", re.IGNORECASE)
        _AliasPatternList.append((_alias, _pat))
    _ALIAS_PATTERNS[_sym] = _AliasPatternList


def tag_symbols(text: str, portfolio_symbols: list[str]) -> list[str]:
    """Return portfolio symbols referenced in *text*, case-insensitive.

    Uses word-boundary regex against known aliases. No fuzzy matching.
    """
    if not text or not portfolio_symbols:
        return []

    matched: list[str] = []
    text_lower = text.lower()

    for sym in portfolio_symbols:
        patterns = _ALIAS_PATTERNS.get(sym)
        if patterns is None:
            # No known alias — try exact ticker match with word boundaries
            pat = re.compile(r"(?<!\w)" + re.escape(sym.lower()) + r"(?!\w)")
            if pat.search(text_lower):
                matched.append(sym)
            continue
        for _alias, pat in patterns:
            if pat.search(text):
                matched.append(sym)
                break  # one match per symbol is enough

    return matched


# ---------- sources ----------


class NewsSource(Protocol):
    def fetch(self, symbols: list[str]) -> list[NewsItem]: ...


MAX_ITEMS_PER_SYMBOL = 5
REQUEST_TIMEOUT = 10.0


COINDESK_RSS = "https://feeds.feedburner.com/CoinDesk"
COINDESK_RSS_ALT = "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"


class CoinDeskRSSSource:
    """Fetches news from CoinDesk RSS feed."""

    def __init__(self, client: httpx.Client | None = None, url: str = COINDESK_RSS) -> None:
        self._client = client or httpx.Client(timeout=REQUEST_TIMEOUT)
        self._owns_client = client is None
        self._url = url

    def fetch(self, symbols: list[str]) -> list[NewsItem]:
        try:
            resp = self._client.get(self._url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("CoinDesk RSS fetch failed: %s", e)
            return []

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            logger.warning("CoinDesk RSS malformed XML: %s", e)
            return []

        items: list[NewsItem] = []
        for item_el in root.iter("item"):
            title = (item_el.findtext("title") or "").strip()
            link = (item_el.findtext("link") or "").strip()
            pub_date_str = (item_el.findtext("pubDate") or "").strip()
            description = (item_el.findtext("description") or "").strip() or None

            if not title or not link:
                continue

            published_at = _parse_rss_date(pub_date_str)
            tagged = tag_symbols(f"{title} {description or ''}", symbols)

            items.append(NewsItem(
                title=title,
                url=link,
                source="coindesk",
                published_at=published_at,
                summary=description,
                symbols=tagged,
            ))

        logger.info("CoinDesk RSS: fetched %d items", len(items))
        return items

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class StubNewsSource:
    """Returns empty list. For tests and offline mode."""

    def fetch(self, symbols: list[str]) -> list[NewsItem]:
        return []


# ---------- helpers ----------


def _parse_rss_date(date_str: str) -> datetime:
    """Parse RFC 2822 / RSS pubDate to timezone-aware UTC datetime."""
    if not date_str:
        return datetime.now(timezone.utc)
    # Common RSS formats
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    logger.warning("unparseable date: %s", date_str)
    return datetime.now(timezone.utc)


def _dedup(items: list[NewsItem]) -> list[NewsItem]:
    """Deduplicate by URL, keeping the earliest fetched."""
    seen: dict[str, NewsItem] = {}
    for item in items:
        if item.url not in seen:
            seen[item.url] = item
    return list(seen.values())


def _cap_per_symbol(items: list[NewsItem], limit: int = MAX_ITEMS_PER_SYMBOL) -> list[NewsItem]:
    """Keep at most *limit* items per symbol, by published_at desc."""
    by_sym: dict[str, list[NewsItem]] = {}
    for item in items:
        for sym in item.symbols:
            by_sym.setdefault(sym, []).append(item)

    keep_urls: set[str] = set()
    for sym, sym_items in by_sym.items():
        sorted_items = sorted(sym_items, key=lambda x: x.published_at, reverse=True)
        for item in sorted_items[:limit]:
            keep_urls.add(item.url)

    return [item for item in items if item.url in keep_urls]


# ---------- module-level default ----------


_default: NewsSource | None = None


def _make_default() -> NewsSource:
    if os.environ.get("SIGA_NEWS_SOURCE") == "stub":
        return StubNewsSource()
    return CoinDeskRSSSource()


def get_news(symbols: list[str]) -> dict[str, list[NewsItem]]:
    """Fetch and tag news for portfolio symbols.

    Returns ``{symbol: [items]}`` sorted by ``published_at`` desc.
    Symbols with no news map to ``[]``. Never raises.
    """
    global _default
    if _default is None:
        _default = _make_default()

    if not symbols:
        return {}

    try:
        raw = _default.fetch(symbols)
    except Exception as e:
        logger.warning("news source failed unexpectedly: %s", e)
        raw = []

    # Filter to items that matched at least one symbol
    tagged = [item for item in raw if item.symbols]

    # Dedup and cap
    deduped = _dedup(tagged)
    capped = _cap_per_symbol(deduped)

    # Group by symbol
    result: dict[str, list[NewsItem]] = {s: [] for s in symbols}
    for item in capped:
        for sym in item.symbols:
            if sym in result:
                result[sym].append(item)

    # Sort each symbol's items by published_at desc
    for sym in result:
        result[sym].sort(key=lambda x: x.published_at, reverse=True)

    return result


def set_source(source: NewsSource) -> None:
    """Override the default news source (for testing)."""
    global _default
    _default = source
