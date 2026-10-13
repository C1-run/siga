"""Unit tests for monie-briefing price sources."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import pytest

from monie_briefing.prices import (
    COINGECKO_IDS,
    CoinGeckoPriceSource,
    StubPriceSource,
)


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


class TestStubPriceSource:
    def test_stub_returns_zeros(self):
        src = StubPriceSource()
        assert src.get_prices(["BTC", "SOL"]) == {"BTC": 0.0, "SOL": 0.0}

    def test_stub_empty_input(self):
        src = StubPriceSource()
        assert src.get_prices([]) == {}


class TestCoinGeckoPriceSource:
    def test_success(self):
        def handler(request):
            return httpx.Response(200, json={
                "bitcoin": {"usd": 65000.0},
                "solana": {"usd": 150.0},
            })
        src = CoinGeckoPriceSource(client=_client(handler))
        assert src.get_prices(["BTC", "SOL"]) == {"BTC": 65000.0, "SOL": 150.0}

    def test_unknown_symbol_skipped(self):
        def handler(request):
            return httpx.Response(200, json={"bitcoin": {"usd": 65000.0}})
        src = CoinGeckoPriceSource(client=_client(handler))
        assert src.get_prices(["BTC", "FAKE"]) == {"BTC": 65000.0}

    def test_empty_symbols_no_request(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={})
        src = CoinGeckoPriceSource(client=_client(handler))
        assert src.get_prices([]) == {}
        assert calls == []

    def test_network_error_returns_empty(self):
        def handler(request):
            raise httpx.ConnectError("boom")
        src = CoinGeckoPriceSource(client=_client(handler))
        assert src.get_prices(["BTC"]) == {}

    def test_http_500_returns_empty(self):
        def handler(request):
            return httpx.Response(500)
        src = CoinGeckoPriceSource(client=_client(handler))
        assert src.get_prices(["BTC"]) == {}

    def test_cache_hit_within_ttl(self):
        calls = []
        def handler(request):
            calls.append(1)
            return httpx.Response(200, json={"bitcoin": {"usd": 65000.0}})
        src = CoinGeckoPriceSource(cache_ttl=60, client=_client(handler))
        src.get_prices(["BTC"])
        src.get_prices(["BTC"])
        assert len(calls) == 1

    def test_cache_miss_after_ttl(self):
        calls = []
        def handler(request):
            calls.append(1)
            return httpx.Response(200, json={"bitcoin": {"usd": 65000.0}})
        src = CoinGeckoPriceSource(cache_ttl=0, client=_client(handler))
        src.get_prices(["BTC"])
        src.get_prices(["BTC"])
        assert len(calls) == 2

    def test_stale_cache_used_on_network_failure(self):
        calls = {"n": 0}
        def handler(request):
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(200, json={"bitcoin": {"usd": 65000.0}})
            raise httpx.ConnectError("boom")
        src = CoinGeckoPriceSource(cache_ttl=0, client=_client(handler))
        src.get_prices(["BTC"])  # populate cache
        assert src.get_prices(["BTC"]) == {"BTC": 65000.0}


class TestGetMarketData:
    def test_success(self):
        from monie_briefing.prices import get_market_data

        def handler(request):
            return httpx.Response(200, json=[{
                "id": "bitcoin",
                "current_price": 77000,
                "price_change_percentage_24h_in_currency": 2.1,
                "price_change_percentage_7d_in_currency": 5.3,
            }])
        result = get_market_data(["BTC"], client=_client(handler))
        assert result["BTC"]["change_24h"] == 2.1
        assert result["BTC"]["change_7d"] == 5.3

    def test_empty_symbols(self):
        from monie_briefing.prices import get_market_data
        assert get_market_data([]) == {}

    def test_unknown_symbol_skipped(self):
        from monie_briefing.prices import get_market_data

        def handler(request):
            return httpx.Response(200, json=[])
        result = get_market_data(["FAKE"], client=_client(handler))
        assert result == {}

    def test_network_error_returns_empty(self):
        from monie_briefing.prices import get_market_data

        def handler(request):
            raise httpx.ConnectError("boom")
        result = get_market_data(["BTC"], client=_client(handler))
        assert result == {}
