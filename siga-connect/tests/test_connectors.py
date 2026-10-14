"""Tests for siga-connect data connectors."""

from __future__ import annotations

import pytest

try:
    import httpx
except ImportError:
    httpx = None

from siga_connect import FetchResult, fetch_trades
from siga_connect.connectors import binance, dune, helius


class TestFetchRouter:
    def test_unknown_source(self):
        with pytest.raises(ValueError, match="unsupported source"):
            fetch_trades("unknown")

    def test_binance_requires_symbol(self):
        with pytest.raises(ValueError, match="--symbol is required"):
            fetch_trades("binance")

    def test_dune_requires_query_id(self):
        with pytest.raises(ValueError, match="--query-id is required"):
            fetch_trades("dune")

    def test_dune_requires_api_key(self):
        with pytest.raises(ValueError, match="--api-key is required"):
            fetch_trades("dune", query_id=123)

    def test_helius_requires_address(self):
        with pytest.raises(ValueError, match="--address is required"):
            fetch_trades("helius")

    def test_helius_requires_api_key(self):
        with pytest.raises(ValueError, match="--api-key is required"):
            fetch_trades("helius", address="abc")


class TestBinanceConnector:
    def test_public_trades_shape(self):
        """Verify the public aggTrades path returns correct types."""
        if httpx is None:
            pytest.skip("httpx not installed")
        # Skip if no network — this is a smoke test
        try:
            result = binance.fetch_trades("BTCUSDT", limit=10)
        except httpx.HTTPError:
            pytest.skip("network unavailable")
        assert isinstance(result, FetchResult)
        assert isinstance(result.pnl, list)
        assert isinstance(result.notional, list)
        assert result.n_trades == len(result.pnl)
        assert "binance" in result.source

    def test_routes_to_public_without_credentials(self, monkeypatch):
        """No api_key → public path; with credentials → private path."""
        called = {}

        def fake_public(symbol, limit):
            called["mode"] = "public"
            return FetchResult(pnl=[1.0], notional=None, source="binance:public:X", n_trades=1)

        def fake_private(symbol, api_key, api_secret, limit):
            called["mode"] = "private"
            return FetchResult(pnl=[1.0], notional=None, source="binance:X", n_trades=1)

        monkeypatch.setattr(binance, "_fetch_public_trades", fake_public)
        monkeypatch.setattr(binance, "_fetch_private_trades", fake_private)

        binance.fetch_trades("BTCUSDT", limit=5)
        assert called["mode"] == "public"

        binance.fetch_trades("BTCUSDT", api_key="k", api_secret="s", limit=5)
        assert called["mode"] == "private"

    def test_sign_is_deterministic_sha256(self):
        sig1 = binance._sign("symbol=BTCUSDT&timestamp=123", "secret")
        sig2 = binance._sign("symbol=BTCUSDT&timestamp=123", "secret")
        assert sig1 == sig2
        assert len(sig1) == 64  # sha256 hex digest

    def test_round_trip_pnl_fifo(self):
        """Buy 1 @ 100, sell 1 @ 110 → gross +10, minus approx buy-side fee."""
        trades = [
            {"price": "100", "qty": "1", "commission": "0", "isBuyer": True},
            {"price": "110", "qty": "1", "commission": "0", "isBuyer": False},
        ]
        pnl = binance._compute_round_trip_pnl(trades)
        assert len(pnl) == 1
        assert pnl[0] == pytest.approx(9.99)  # 10.0 - 0.1% fee approximation

    def test_round_trip_pnl_unmatched_buy_produces_no_pnl(self):
        trades = [{"price": "100", "qty": "1", "commission": "0", "isBuyer": True}]
        assert binance._compute_round_trip_pnl(trades) == []


class TestDuneConnector:
    def test_column_detection(self):
        """Verify _pick_column finds P&L columns by name."""
        assert dune._pick_column(["pnl", "time"], ("pnl", "profit")) == "pnl"
        assert dune._pick_column(["profit_usd", "time"], ("pnl", "profit")) is None
        assert dune._pick_column(["P&L", "time"], ("pnl", "profit", "p&l")) == "P&L"

    def test_number_parsing(self):
        assert dune._parse_number(42) == 42.0
        assert dune._parse_number("42.5") == 42.5
        assert dune._parse_number("$1,234.56") == 1234.56


class TestHeliusConnector:
    def test_swap_extraction_no_transfers(self):
        tx = {"tokenTransfers": []}
        assert helius._extract_swap_pnl(tx) is None

    def test_swap_extraction_one_sided(self):
        tx = {"tokenTransfers": [{"tokenAmount": 100, "mint": "A", "direction": "in"}]}
        assert helius._extract_swap_pnl(tx) is None

    def test_swap_extraction_basic(self):
        tx = {
            "tokenTransfers": [
                {"tokenAmount": 100, "mint": "So11111111111111111111111111111111111111112", "direction": "out"},
                {"tokenAmount": 200, "mint": "TokenA", "direction": "in"},
            ]
        }
        result = helius._extract_swap_pnl(tx)
        assert result is not None
        assert result["pnl"] == 100  # 200 in - 100 out
        assert result["notional"] == 100  # SOL side


class TestIntegration:
    def test_audit_compatibility(self):
        """FetchResult must be directly usable by siga_audit.run_audit."""
        from siga_audit import run_audit

        # Synthetic data that should PASS
        pnl = [100.0, -20.0, 150.0, -30.0, 80.0] * 20  # 100 trades
        result = FetchResult(pnl=pnl, notional=None, source="test", n_trades=100)
        audit = run_audit(result.pnl)
        assert audit.verdict in ("PASS", "FAIL", "INCONCLUSIVE")
