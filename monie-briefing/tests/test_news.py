"""Tests for the monie-briefing news module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from unittest.mock import MagicMock

import httpx
import pytest

import monie_briefing.news as news
from monie_briefing.news import (
    CoinDeskRSSSource,
    NewsItem,
    StubNewsSource,
    get_news,
    set_source,
    tag_symbols,
)


# ---------- stub source ----------


class TestStubSource:
    def test_returns_empty_list(self):
        src = StubNewsSource()
        assert src.fetch(["BTC"]) == []


# ---------- CoinDesk RSS (mocked) ----------


VALID_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>CoinDesk</title>
  <item>
    <title>Bitcoin Hits New All-Time High</title>
    <link>https://coindesk.com/news/btc-ath</link>
    <pubDate>Sat, 12 Sep 2026 10:00:00 +0000</pubDate>
    <description>Bitcoin reached $100k today.</description>
  </item>
  <item>
    <title>Ethereum Merge Complete</title>
    <link>https://coindesk.com/news/eth-merge</link>
    <pubDate>Sat, 12 Sep 2026 09:00:00 +0000</pubDate>
    <description>The Ethereum network has finished its merge.</description>
  </item>
  <item>
    <title>Gold Prices Steady</title>
    <link>https://coindesk.com/news/gold-steady</link>
    <pubDate>Sat, 12 Sep 2026 08:00:00 +0000</pubDate>
    <description>Gold prices held steady.</description>
  </item>
</channel>
</rss>"""


def _mock_client(response_text: str, status_code: int = 200) -> httpx.Client:
    """Create an httpx.Client that returns fixed response."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=status_code,
            text=response_text,
            headers={"content-type": "application/rss+xml"},
        )
    )
    return httpx.Client(transport=transport, timeout=5.0)


class TestCoinDeskRSS:
    def test_parses_valid_rss(self):
        client = _mock_client(VALID_RSS)
        src = CoinDeskRSSSource(client=client)
        items = src.fetch(["BTC", "ETH"])
        urls = [i.url for i in items]
        assert "https://coindesk.com/news/btc-ath" in urls
        assert "https://coindesk.com/news/eth-merge" in urls
        # Gold article should be included (unfiltered at fetch level)
        assert len(items) == 3

    def test_handles_malformed_xml(self):
        client = _mock_client("this is not xml <<<>>>")
        src = CoinDeskRSSSource(client=client)
        items = src.fetch(["BTC"])
        assert items == []

    def test_handles_network_error(self):
        def _raise(request):
            raise httpx.ConnectError("connection refused")
        transport = httpx.MockTransport(_raise)
        client = httpx.Client(transport=transport, timeout=5.0)
        src = CoinDeskRSSSource(client=client)
        items = src.fetch(["BTC"])
        assert items == []

    def test_handles_non_200(self):
        client = _mock_client("error", status_code=503)
        src = CoinDeskRSSSource(client=client)
        items = src.fetch(["BTC"])
        assert items == []


# ---------- symbol tagging ----------


class TestTagSymbols:
    def test_exact_ticker_match(self):
        assert tag_symbols("BTC hits $100k", ["BTC", "ETH"]) == ["BTC"]

    def test_alias_match(self):
        assert tag_symbols("Bitcoin hits new high", ["BTC", "ETH"]) == ["BTC"]

    def test_word_boundary_no_false_positive(self):
        """SOLD must NOT match SOL."""
        result = tag_symbols("SOLD all my tokens", ["SOL", "BTC"])
        assert "SOL" not in result

    def test_case_insensitive(self):
        assert tag_symbols("bitCOIN is up", ["BTC"]) == ["BTC"]

    def test_multiple_matches(self):
        text = "Bitcoin and Ethereum both rally"
        result = tag_symbols(text, ["BTC", "ETH", "SOL"])
        assert "BTC" in result
        assert "ETH" in result
        assert "SOL" not in result

    def test_no_match_returns_empty(self):
        assert tag_symbols("Gold prices steady", ["BTC", "ETH"]) == []

    def test_empty_text(self):
        assert tag_symbols("", ["BTC"]) == []

    def test_empty_symbols(self):
        assert tag_symbols("Bitcoin is up", []) == []


# ---------- get_news integration ----------


class TestGetNews:
    def test_never_raises_all_sources_down(self, monkeypatch):
        def _fail(symbols):
            raise RuntimeError("boom")
        set_source(_fail)  # type: ignore[arg-type]
        # monkeypatch won't work for module-level; use set_source
        result = get_news(["BTC"])
        assert result == {"BTC": []}
        # Reset
        set_source(StubNewsSource())

    def test_empty_symbols_returns_empty(self):
        result = get_news([])
        assert result == {}

    def test_groups_by_symbol(self):
        items = [
            NewsItem(
                title="BTC surges",
                url="https://example.com/1",
                source="test",
                published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                symbols=["BTC"],
            ),
            NewsItem(
                title="ETH rally",
                url="https://example.com/2",
                source="test",
                published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                symbols=["ETH"],
            ),
            NewsItem(
                title="BTC correction",
                url="https://example.com/3",
                source="test",
                published_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                symbols=["BTC"],
            ),
        ]

        class FakeSource:
            def fetch(self, symbols):
                return items

        set_source(FakeSource())
        result = get_news(["BTC", "ETH", "SOL"])
        assert len(result["BTC"]) == 2
        assert len(result["ETH"]) == 1
        assert result["SOL"] == []
        # BTC items sorted by date desc
        assert result["BTC"][0].title == "BTC correction"
        # Reset
        set_source(StubNewsSource())

    def test_dedup_by_url(self):
        items = [
            NewsItem(
                title="BTC up",
                url="https://example.com/same",
                source="test",
                published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                symbols=["BTC"],
            ),
            NewsItem(
                title="BTC up again",
                url="https://example.com/same",
                source="test2",
                published_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                symbols=["BTC"],
            ),
        ]

        class FakeSource:
            def fetch(self, symbols):
                return items

        set_source(FakeSource())
        result = get_news(["BTC"])
        assert len(result["BTC"]) == 1
        # Keeps the first one seen
        assert result["BTC"][0].title == "BTC up"
        set_source(StubNewsSource())

    def test_caps_at_5_per_symbol(self):
        items = [
            NewsItem(
                title=f"News {i}",
                url=f"https://example.com/{i}",
                source="test",
                published_at=datetime(2026, 1, 1, i, tzinfo=timezone.utc),
                symbols=["BTC"],
            )
            for i in range(10)
        ]

        class FakeSource:
            def fetch(self, symbols):
                return items

        set_source(FakeSource())
        result = get_news(["BTC"])
        assert len(result["BTC"]) == 5
        # Should be the 5 most recent
        assert result["BTC"][0].title == "News 9"
        set_source(StubNewsSource())

    def test_strips_unmatched_items(self):
        """Items that match 0 portfolio symbols are dropped."""
        items = [
            NewsItem(
                title="Gold rally",
                url="https://example.com/gold",
                source="test",
                published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                symbols=[],  # no match
            ),
            NewsItem(
                title="Bitcoin surge",
                url="https://example.com/btc",
                source="test",
                published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                symbols=["BTC"],
            ),
        ]

        class FakeSource:
            def fetch(self, symbols):
                return items

        set_source(FakeSource())
        result = get_news(["BTC"])
        assert len(result["BTC"]) == 1
        assert result["BTC"][0].title == "Bitcoin surge"
        set_source(StubNewsSource())
