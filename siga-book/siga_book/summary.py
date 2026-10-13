"""Single-frame L2 order book summary.

Ported from c1m/briefing/sources/tick.py::get_orderbook_summary.
Split into a pure computation (summarize_book) and a thin fetch
adapter (fetch_summary) so this package has zero dependencies and
never touches the network.
"""

from typing import Any, Callable


def summarize_book(book: dict[str, Any], depth: int = 5) -> dict[str, Any]:
    """Summarize one L2 order book snapshot: BBO, spread, imbalance, walls.

    Args:
        book: {"bids": [[price, size], ...], "asks": [[price, size], ...]}
            ordered best-first, as returned by ccxt fetch_order_book.
        depth: number of levels per side to consider.

    Returns:
        Dict with bid/ask/mid/spread/imbalances/depths/sell_wall_levels,
        or {"error": ...} when the book is empty. Never raises on
        malformed numeric content — unparseable books report an error.
    """
    result: dict[str, Any] = {
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

    bids = book.get("bids", []) if isinstance(book, dict) else []
    asks = book.get("asks", []) if isinstance(book, dict) else []

    if not bids or not asks:
        result["error"] = "Empty order book"
        return result

    try:
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
    except (IndexError, TypeError, ValueError) as e:
        result["error"] = f"Invalid book top: {e}"
        return result

    mid = (best_bid + best_ask) / 2
    spread = best_ask - best_bid
    spread_pct = (spread / mid * 100) if mid > 0 else 0.0

    try:
        bid_vols = [float(b[1]) for b in bids[:depth]]
        ask_vols = [float(a[1]) for a in asks[:depth]]
    except (IndexError, TypeError, ValueError) as e:
        result["error"] = f"Invalid book sizes: {e}"
        return result

    total_bid_vol = sum(bid_vols)
    total_ask_vol = sum(ask_vols)

    bid_imbalance = total_bid_vol / (total_bid_vol + total_ask_vol) if (total_bid_vol + total_ask_vol) > 0 else 0.5
    ask_imbalance = total_ask_vol / (total_bid_vol + total_ask_vol) if (total_bid_vol + total_ask_vol) > 0 else 0.5

    # Detect sell walls (ask levels with > 2x average volume)
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
        "ask_imbalance": round(ask_imbalance, 3),
        "bid_depth": round(total_bid_vol, 4),
        "ask_depth": round(total_ask_vol, 4),
    })

    return result


def fetch_summary(
    fetcher: Callable[[str, int], dict[str, Any]],
    symbol: str,
    depth: int = 5,
) -> dict[str, Any]:
    """Fetch one snapshot via fetcher, then summarize it.

    Args:
        fetcher: callable (symbol, depth) -> raw book dict.
            E.g. with ccxt: lambda s, d: exchange.fetch_order_book(s, limit=d * 2).
        symbol: market symbol, echoed back in the result.
        depth: levels per side.

    Returns:
        summarize_book() output plus {"symbol": symbol}.
        Fetch errors are captured as {"symbol": ..., "error": str}.
    """
    try:
        book = fetcher(symbol, depth)
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}
    result = summarize_book(book, depth)
    result["symbol"] = symbol
    return result
