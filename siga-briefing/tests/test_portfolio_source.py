"""Unit tests for portfolio-aware briefing source."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from siga_briefing.portfolio import Holding, Portfolio
from siga_briefing.sources.portfolio import get_portfolio_context, _risk_flags


def _portfolio(*holdings: tuple) -> Portfolio:
    pf = Portfolio()
    for sym, qty, cost in holdings:
        pf.add(Holding(sym, qty, cost, date(2025, 1, 1)))
    return pf


class TestRiskFlags:
    def test_concentration_warning(self):
        holding = {"symbol": "BTC", "allocation": 63.0, "pnl_pct": 24.5, "cost_basis": 62000, "current_price": 77000}
        flags = _risk_flags(holding, 100000)
        assert any("63.0% of portfolio" in f for f in flags)

    def test_no_concentration_when_balanced(self):
        holding = {"symbol": "SOL", "allocation": 30.0, "pnl_pct": 10.0, "cost_basis": 150, "current_price": 165}
        flags = _risk_flags(holding, 100000)
        assert not any("of portfolio" in f for f in flags)

    def test_loss_warning(self):
        holding = {"symbol": "SOL", "allocation": 16.0, "pnl_pct": -32.0, "cost_basis": 150, "current_price": 102}
        flags = _risk_flags(holding, 100000)
        assert any("below cost basis" in f for f in flags)

    def test_gain_info(self):
        holding = {"symbol": "BTC", "allocation": 63.0, "pnl_pct": 55.0, "cost_basis": 50000, "current_price": 77500}
        flags = _risk_flags(holding, 100000)
        assert any("above cost basis" in f for f in flags)

    def test_neutral_no_flags(self):
        holding = {"symbol": "ETH", "allocation": 20.0, "pnl_pct": -5.0, "cost_basis": 3000, "current_price": 2850}
        flags = _risk_flags(holding, 100000)
        assert flags == []


class TestGetPortfolioContext:
    @patch("siga_briefing.sources.portfolio.get_prices")
    @patch("siga_briefing.sources.portfolio.get_market_data")
    def test_basic_context(self, mock_market, mock_prices):
        mock_prices.return_value = {"SOL": 200.0, "BTC": 70000.0}
        mock_market.return_value = {"SOL": {"change_24h": 1.5, "change_7d": -2.0}, "BTC": {"change_24h": 0.5, "change_7d": 3.0}}
        pf = _portfolio(("SOL", 100, 150.0), ("BTC", 0.5, 60000.0))
        ctx = get_portfolio_context(pf)
        assert len(ctx["holdings"]) == 2
        assert "total" in ctx

    def test_empty_portfolio(self):
        ctx = get_portfolio_context(Portfolio())
        assert ctx["holdings"] == []
        assert ctx["total"]["cost"] == 0

    @patch("siga_briefing.sources.portfolio.get_prices")
    @patch("siga_briefing.sources.portfolio.get_market_data")
    def test_holdings_sorted_by_allocation(self, mock_market, mock_prices):
        mock_prices.return_value = {"SOL": 200.0, "BTC": 70000.0}
        mock_market.return_value = {}
        pf = _portfolio(("SOL", 100, 150.0), ("BTC", 0.5, 60000.0))
        ctx = get_portfolio_context(pf)
        assert ctx["holdings"][0]["allocation"] >= ctx["holdings"][1]["allocation"]

    @patch("siga_briefing.sources.portfolio.get_prices")
    @patch("siga_briefing.sources.portfolio.get_market_data")
    def test_includes_24h_7d(self, mock_market, mock_prices):
        mock_prices.return_value = {"SOL": 200.0}
        mock_market.return_value = {"SOL": {"change_24h": 1.5, "change_7d": -2.0}}
        pf = _portfolio(("SOL", 100, 150.0))
        ctx = get_portfolio_context(pf)
        h = ctx["holdings"][0]
        assert h["change_24h"] == 1.5
        assert h["change_7d"] == -2.0

    @patch("siga_briefing.sources.portfolio.get_prices")
    @patch("siga_briefing.sources.portfolio.get_market_data")
    def test_includes_flags(self, mock_market, mock_prices):
        mock_prices.return_value = {"SOL": 100.0}  # -33% from cost 150
        mock_market.return_value = {}
        pf = _portfolio(("SOL", 100, 150.0))
        ctx = get_portfolio_context(pf)
        h = ctx["holdings"][0]
        assert len(h["flags"]) > 0
        assert any("below cost" in f for f in h["flags"])
