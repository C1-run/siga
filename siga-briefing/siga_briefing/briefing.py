"""Morning briefing orchestrator."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from siga_briefing.portfolio import Portfolio, DEFAULT_PATH


class MorningBriefing:
    """Orchestrate all briefing data sources into a single report."""

    def __init__(self, symbol: str = "SOL/USDC", lookback_hours: int = 24):
        self.symbol = symbol
        self.lookback_hours = lookback_hours
        self._cutoff = datetime.now() - timedelta(hours=lookback_hours)

    def generate(self) -> dict:
        """Build the full briefing dict."""
        from siga_briefing.sources import (
            arena, paper, soak, tomb, tick, external,
        )
        return {
            "generated_at": datetime.now().isoformat(),
            "symbol": self.symbol,
            "lookback_hours": self.lookback_hours,
            "arena": arena.get_24h_summary(self._cutoff.isoformat()),
            "paper": paper.get_24h_summary(self._cutoff.isoformat()),
            "soak": soak.get_trends(),
            "tomb": tomb.get_liquidation_clusters(self.symbol),
            "tick": tick.get_orderbook_summary(self.symbol),
            "external": external.get_market_context(),
        }

    def render_markdown(self, report: Optional[dict] = None) -> str:
        """Render briefing to Markdown string."""
        if report is None:
            report = self.generate()
        from siga_briefing.formatters.markdown import render
        return render(report)


class PortfolioBriefing:
    """Portfolio-aware morning briefing — only shows what matters to your holdings."""

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    @classmethod
    def from_file(cls, path: str | Path | None = None) -> PortfolioBriefing:
        """Load portfolio from file and create briefing."""
        return cls(portfolio=Portfolio.load(path or DEFAULT_PATH))

    def generate(self) -> dict:
        """Build portfolio-aware briefing dict."""
        from siga_briefing.sources.portfolio import get_portfolio_context
        ctx = get_portfolio_context(self.portfolio)
        return {
            "type": "portfolio",
            "generated_at": datetime.now().isoformat(),
            "portfolio": ctx,
        }

    def render_markdown(self, report: Optional[dict] = None) -> str:
        """Render portfolio briefing to Markdown string."""
        if report is None:
            report = self.generate()
        from siga_briefing.formatters.markdown import render_portfolio
        return render_portfolio(report)
