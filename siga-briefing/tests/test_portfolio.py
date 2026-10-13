"""Unit tests for siga-briefing portfolio model."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from pathlib import Path

import pytest

from siga_briefing.portfolio import Holding, Portfolio, DEFAULT_PATH


# ---------------------------------------------------------------------------
# Holding tests
# ---------------------------------------------------------------------------


class TestHolding:
    def test_add_new_holding(self):
        pf = Portfolio()
        pf.add(Holding("SOL", 100, 150.0, date(2025, 1, 1)))
        assert len(pf) == 1
        assert pf.find("SOL").quantity == 100

    def test_add_merge_same_symbol(self):
        pf = Portfolio()
        pf.add(Holding("SOL", 100, 150.0, date(2025, 1, 1)))
        pf.add(Holding("SOL", 50, 200.0, date(2025, 2, 1)))
        assert len(pf) == 1
        h = pf.find("SOL")
        assert h.quantity == 150
        assert h.cost_basis == pytest.approx(166.6667, abs=0.01)


class TestHoldingValidation:
    def test_empty_symbol_raises(self):
        with pytest.raises(ValueError, match="symbol cannot be empty"):
            Holding("", 10, 100.0, date(2025, 1, 1))

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="quantity must be positive"):
            Holding("SOL", -10, 100.0, date(2025, 1, 1))

    def test_negative_cost_raises(self):
        with pytest.raises(ValueError, match="cost_basis must be non-negative"):
            Holding("SOL", 10, -100.0, date(2025, 1, 1))

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="quantity must be positive"):
            Holding("SOL", 0, 100.0, date(2025, 1, 1))

    def test_string_date_coerced(self):
        h = Holding("SOL", 10, 100.0, "2025-03-15")
        assert h.acquired_at == date(2025, 3, 15)

    def test_invalid_date_string_raises(self):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            Holding("SOL", 10, 100.0, "not-a-date")


# ---------------------------------------------------------------------------
# Portfolio mutations
# ---------------------------------------------------------------------------


class TestPortfolioIO:
    def test_remove_holding(self):
        pf = Portfolio(holdings=[
            Holding("SOL", 100, 150.0, date(2025, 1, 1)),
            Holding("BTC", 1, 60000.0, date(2025, 1, 1)),
        ])
        removed = pf.remove("SOL")
        assert removed.symbol == "SOL"
        assert len(pf) == 1
        assert pf.find("SOL") is None

    def test_remove_nonexistent_returns_none(self):
        pf = Portfolio(holdings=[Holding("SOL", 100, 150.0, date(2025, 1, 1))])
        assert pf.remove("BTC") is None
        assert len(pf) == 1


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------


class TestCSVImport:
    def test_from_csv(self, tmp_path):
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,quantity,cost_basis,acquired_at,notes\n"
            "SOL,100,150.00,2025-01-15,early position\n"
            "BTC,0.5,62000.00,2024-11-20,\n"
            "ETH,5,3200.00,2025-02-01,\n",
            encoding="utf-8",
        )
        pf = Portfolio.from_csv(csv_file)
        assert len(pf) == 3
        assert pf.find("SOL").notes == "early position"
        assert pf.find("BTC").quantity == 0.5

    def test_from_csv_minimal(self, tmp_path):
        """CSV with only symbol+quantity works (cost_basis optional)."""
        csv_file = tmp_path / "minimal.csv"
        csv_file.write_text("symbol,quantity\nSOL,100\n", encoding="utf-8")
        pf = Portfolio.from_csv(csv_file)
        assert len(pf) == 1
        assert pf.find("SOL").cost_basis == 0.0

    def test_from_csv_missing_symbol(self, tmp_path):
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text("quantity\n100\n", encoding="utf-8")
        with pytest.raises(ValueError, match="CSV missing columns"):
            Portfolio.from_csv(csv_file)

    def test_from_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Portfolio.from_csv("/nonexistent/path.csv")


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_save_and_load(self, tmp_path):
        pf = Portfolio(holdings=[
            Holding("SOL", 100, 150.0, date(2025, 1, 1), notes="test"),
            Holding("BTC", 0.5, 60000.0, date(2025, 2, 1)),
        ])
        out = tmp_path / "p.json"
        pf.save(out)
        loaded = Portfolio.load(out)
        assert len(loaded) == 2
        assert loaded.find("SOL").notes == "test"
        assert loaded.find("BTC").cost_basis == 60000.0

    def test_load_missing_file_returns_empty(self, tmp_path):
        pf = Portfolio.load(tmp_path / "nonexistent.json")
        assert len(pf) == 0


# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------


class TestCalculation:
    def test_total_cost(self):
        pf = Portfolio(holdings=[
            Holding("SOL", 100, 150.0, date(2025, 1, 1)),
            Holding("BTC", 0.5, 60000.0, date(2025, 1, 1)),
        ])
        assert pf.total_cost() == pytest.approx(100 * 150 + 0.5 * 60000)

    def test_total_value(self):
        pf = Portfolio(holdings=[
            Holding("SOL", 100, 150.0, date(2025, 1, 1)),
            Holding("BTC", 0.5, 60000.0, date(2025, 1, 1)),
        ])
        prices = {"SOL": 200.0, "BTC": 70000.0}
        assert pf.total_value(prices) == pytest.approx(100 * 200 + 0.5 * 70000)

    def test_pnl(self):
        pf = Portfolio(holdings=[
            Holding("SOL", 100, 150.0, date(2025, 1, 1)),
        ])
        prices = {"SOL": 200.0}
        result = pf.pnl(prices)
        assert result["total"]["cost"] == 15000.0
        assert result["total"]["value"] == 20000.0
        assert result["total"]["pnl"] == 5000.0
        assert result["total"]["pnl_pct"] == pytest.approx(33.333, abs=0.01)
        assert result["per_symbol"]["SOL"]["pnl"] == 5000.0

    def test_allocation(self):
        pf = Portfolio(holdings=[
            Holding("SOL", 100, 150.0, date(2025, 1, 1)),
            Holding("BTC", 0.5, 60000.0, date(2025, 1, 1)),
        ])
        prices = {"SOL": 200.0, "BTC": 70000.0}
        alloc = pf.allocation(prices)
        # SOL: 20000, BTC: 35000, total: 55000
        assert alloc["SOL"] == pytest.approx(20000 / 55000 * 100, abs=0.1)
        assert alloc["BTC"] == pytest.approx(35000 / 55000 * 100, abs=0.1)

    def test_allocation_empty_portfolio(self):
        pf = Portfolio()
        assert pf.allocation({}) == {}
