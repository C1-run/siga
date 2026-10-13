"""Tick data source — order book micro-structure via ccxt."""

from typing import Any


def get_orderbook_summary(symbol: str = "SOL/USDC", depth: int = 5) -> dict[str, Any]:
    """Get order book summary from Hyperliquid via ccxt."""
    try:
        import ccxt
    except ImportError:
        return {"symbol": symbol, "error": "ccxt not installed"}

    result: dict[str, Any] = {
        "symbol": symbol,
        "bid_price": None,
        "ask_price": None,
        "spread": None,
        "spread_pct": None,
        "mid_price": None,
        "bid_imbalance": None,
        "ask_imbalance": None,
        "sell_wall_levels": [],
        "error": None,
    }
    try:
        exchange = ccxt.hyperliquid()
        ob = exchange.fetch_order_book(symbol, limit=depth * 2)
        bids = ob.get("bids", [])
        asks = ob.get("asks", [])

        if not bids or not asks:
            result["error"] = "Empty order book"
            return result

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        spread_pct = (spread / mid * 100) if mid > 0 else 0.0

        bid_vols = [float(b[1]) for b in bids[:depth]]
        ask_vols = [float(a[1]) for a in asks[:depth]]
        total_bid_vol = sum(bid_vols)
        total_ask_vol = sum(ask_vols)

        bid_imbalance = total_bid_vol / (total_bid_vol + total_ask_vol) if (total_bid_vol + total_ask_vol) > 0 else 0.5

        if ask_vols:
            avg_ask = sum(ask_vols) / len(ask_vols)
            sell_walls = [
                {"price": float(asks[i][0]), "volume": ask_vols[i], "multiple": round(ask_vols[i] / avg_ask, 1)}
                for i in range(len(ask_vols))
                if avg_ask > 0 and ask_vols[i] > avg_ask * 2
            ]
            result["sell_wall_levels"] = sell_walls[:3]

        result.update({
            "bid_price": best_bid,
            "ask_price": best_ask,
            "spread": round(spread, 4),
            "spread_pct": round(spread_pct, 4),
            "mid_price": round(mid, 4),
            "bid_imbalance": round(bid_imbalance, 3),
            "ask_imbalance": round(1 - bid_imbalance, 3),
            "bid_depth": round(total_bid_vol, 4),
            "ask_depth": round(total_ask_vol, 4),
        })
    except Exception as e:
        result["error"] = str(e)

    return result
