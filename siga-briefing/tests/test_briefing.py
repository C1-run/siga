"""Unit tests for siga-briefing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock

from siga_briefing import MorningBriefing
from siga_briefing.formatters.markdown import render, _verdict


class TestMorningBriefing:
    def test_default_construction(self):
        b = MorningBriefing()
        assert b.symbol == "SOL/USDC"
        assert b.lookback_hours == 24

    def test_custom_symbol(self):
        b = MorningBriefing(symbol="BTC/USDC", lookback_hours=12)
        assert b.symbol == "BTC/USDC"
        assert b.lookback_hours == 12

    def test_generate_returns_dict(self):
        b = MorningBriefing()
        report = b.generate()
        assert isinstance(report, dict)
        assert "arena" in report
        assert "paper" in report
        assert "soak" in report
        assert "tomb" in report
        assert "tick" in report
        assert "external" in report
        assert report["arena"].get("error") is not None
        assert report["paper"].get("error") is not None
        assert report["soak"].get("error") is not None

    def test_render_marks_unavailable_sources(self):
        report = {
            "generated_at": "2026-09-07T08:00:00",
            "symbol": "SOL/USDC",
            "lookback_hours": 24,
            "external": {"sol_price": 106.5, "sol_24h_change_pct": 3.1, "fear_greed_index": 71, "fear_greed_label": "Greed"},
            "arena": {"error": "unavailable: arena.db not found"},
            "paper": {"error": "unavailable: state.db not found"},
            "soak": {"error": "unavailable: engine_health_history table not found"},
            "tomb": {"open_interest": {"total": 5000000}, "support_clusters": [100.0], "resistance_clusters": [110.0]},
        }
        md = render(report)
        assert "Arena v3 Report" in md
        assert "Unavailable" in md
        assert "Paper Trading" in md
        assert "Soak Testing" in md
        assert "Tomb Cluster" in md


class TestMarkdownRenderer:
    def test_renders_basic_sections(self):
        report = {
            "generated_at": "2026-09-07T08:00:00",
            "symbol": "SOL/USDC",
            "lookback_hours": 24,
            "external": {"sol_price": 106.5, "sol_24h_change_pct": 3.1, "fear_greed_index": 71, "fear_greed_label": "Greed"},
            "arena": {"total_bets": 3, "win_rate": 0.33, "total_pnl": 5.0},
            "paper": {"signals_generated": 2, "trades_taken": 1, "win_rate": 1.0, "total_pnl": 5.0},
            "soak": {"status": "running", "avg_cycle_ms": 500.0, "trend": "stable"},
            "tomb": {"open_interest": {"total": 5000000}, "support_clusters": [100.0], "resistance_clusters": [110.0]},
        }
        md = render(report)
        assert "# Morning Operational Briefing" in md
        assert "## Market Context" in md
        assert "## Arena v3 Report" in md
        assert "## Verdict" in md

    def test_verdict_includes_market_context(self):
        report = {
            "external": {"fear_greed_index": 71, "fear_greed_label": "Greed"},
            "tomb": {"support_clusters": [100.0], "resistance_clusters": [110.0]},
        }
        v = _verdict(report)
        assert "Greed" in v
        assert "100" in v or "110" in v
