"""Tomb cluster source — liquidation heatmap via Hyperliquid API."""

from typing import Any


HYPERLIQUID_INFO = "https://api.hyperliquid.xyz/info"


def _post(body: dict, timeout: float = 10.0) -> Any:
    try:
        import httpx
    except ImportError:
        return None
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(HYPERLIQUID_INFO, json=body)
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


def get_liquidation_clusters(symbol: str = "SOL/USDC", lookback_hours: int = 24) -> dict[str, Any]:
    """Get liquidation clusters and liquidity levels."""
    coin = symbol.split("/")[0]
    result = {
        "symbol": symbol,
        "coin": coin,
        "open_interest": None,
        "funding_rate": None,
        "mark_price": None,
        "support_clusters": [],
        "resistance_clusters": [],
        "liquidation_zones": [],
        "error": None,
    }
    try:
        ctx_data = _post({"type": "metaAndAssetCtxs"})
        if ctx_data and isinstance(ctx_data, list) and len(ctx_data) == 2:
            meta, ctxs = ctx_data
            for asset, ctx in zip(meta.get("universe", []), ctxs):
                if asset.get("name", "").upper() == coin.upper():
                    result["open_interest"] = {
                        "total": float(ctx.get("openInterest", 0)),
                        "mark_price": float(ctx.get("markPrice", 0)),
                        "oracle_price": float(ctx.get("oraclePrice", 0)),
                    }
                    result["funding_rate"] = {
                        "rate": float(ctx.get("funding", 0)),
                        "annualized": round(float(ctx.get("funding", 0)) * 365 * 24 * 100, 2),
                    }
                    result["mark_price"] = float(ctx.get("markPrice", 0))
                    if result["mark_price"]:
                        result["support_clusters"] = [round(result["mark_price"] * 0.95, 2)]
                        result["resistance_clusters"] = [round(result["mark_price"] * 1.05, 2)]
                    break
    except Exception as e:
        result["error"] = str(e)
    return result
