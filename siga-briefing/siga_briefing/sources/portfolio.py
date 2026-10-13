"""Portfolio-aware market context — holdings P&L, 24h/7d changes, risk flags."""
from __future__ import annotations


import logging
from typing import Any

from siga_briefing.portfolio import Portfolio
from siga_briefing.prices import get_prices, get_market_data


logger = logging.getLogger(__name__)


def _risk_flags(holding: dict, total_value: float) -> list[str]:
    """Generate fact-based risk flags for a single holding. No advice — just observations."""
    flags: list[str] = []
    sym = holding["symbol"]
    alloc = holding.get("allocation", 0.0)
    pnl_pct = holding.get("pnl_pct", 0.0)
    cost = holding.get("cost_basis", 0.0)
    price = holding.get("current_price", 0.0)

    if alloc >= 50:
        flags.append(f"{alloc:.1f}% of portfolio")

    if cost > 0 and price > 0:
        pct_from_cost = ((price - cost) / cost) * 100
        if pnl_pct <= -20:
            flags.append(f"{abs(pnl_pct):.1f}% below cost basis")
        elif pnl_pct >= 50:
            flags.append(f"{pnl_pct:.1f}% above cost basis")

    return flags


def get_portfolio_context(portfolio: Portfolio) -> dict[str, Any]:
    """Build portfolio-aware briefing context.

    Returns a dict with:
    - holdings: per-holding P&L, allocation, 24h/7d changes, risk flags
    - total: aggregate P&L
    """
    if not portfolio:
        return {
            "holdings": [],
            "total": {"cost": 0, "value": 0, "pnl": 0, "pnl_pct": 0},
        }

    prices = get_prices(portfolio.symbols())
    pnl_data = portfolio.pnl(prices)
    alloc = portfolio.allocation(prices)

    # Fetch 24h/7d market data in one call
    market = get_market_data(portfolio.symbols())

    total_value = pnl_data["total"].get("value", 0.0)

    holdings = []
    for h in portfolio:
        sym = h.symbol
        price = prices.get(sym, 0.0)
        s = pnl_data["per_symbol"].get(sym, {})
        md = market.get(sym, {})
        holding_dict = {
            "symbol": sym,
            "quantity": h.quantity,
            "cost_basis": h.cost_basis,
            "current_price": price,
            "value": s.get("value", 0.0),
            "pnl": s.get("pnl", 0.0),
            "pnl_pct": s.get("pnl_pct", 0.0),
            "allocation": alloc.get(sym, 0.0),
            "change_24h": md.get("change_24h"),
            "change_7d": md.get("change_7d"),
            "flags": _risk_flags(
                {**s, "symbol": sym, "cost_basis": h.cost_basis, "current_price": price, "allocation": alloc.get(sym, 0.0)},
                total_value,
            ),
        }
        holdings.append(holding_dict)

    holdings.sort(key=lambda x: x["allocation"], reverse=True)

    # Fear & Greed
    fear_greed = None
    try:
        from siga_briefing.sources.external import get_market_context
        ext = get_market_context()
        fear_greed = {
            "value": ext.get("fear_greed_index"),
            "value_classification": ext.get("fear_greed_label"),
        }
    except Exception:
        pass

    return {
        "holdings": holdings,
        "total": pnl_data["total"],
        "fear_greed": fear_greed,
    }
