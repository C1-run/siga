"""External market context — SOL price, Fear & Greed, ecosystem tokens."""

import urllib.request
import json
from typing import Any


BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/24hr"
COINGECKO_API = "https://api.coingecko.com/api/v3"
FEAR_GREED_API = "https://api.alternative.me/fng/"


def _get_json(url: str, timeout: float = 10.0) -> Any:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def get_market_context() -> dict[str, Any]:
    """Get external market context for briefing."""
    result: dict[str, Any] = {
        "sol_price": None,
        "sol_24h_change_pct": None,
        "sol_7d_change_pct": None,
        "fear_greed_index": None,
        "fear_greed_label": None,
        "eco_tokens": {},
        "error": None,
    }
    try:
        # SOL price (Binance primary, CoinGecko fallback)
        ticker = _get_json(f"{BINANCE_TICKER}?symbol=SOLUSDT")
        if ticker and isinstance(ticker, dict) and ticker.get("lastPrice"):
            result["sol_price"] = round(float(ticker["lastPrice"]), 2)
            result["sol_24h_change_pct"] = round(float(ticker.get("priceChangePercent", 0)), 2)
        else:
            cg = _get_json(f"{COINGECKO_API}/simple/price?ids=solana&vs_currencies=usd&include_24hr_change=true")
            if cg and isinstance(cg, dict):
                sol = cg.get("solana", {})
                if sol.get("usd"):
                    result["sol_price"] = round(float(sol["usd"]), 2)
                if sol.get("usd_24h_change"):
                    result["sol_24h_change_pct"] = round(float(sol["usd_24h_change"]), 2)

        # 7d momentum
        cg = _get_json(f"{COINGECKO_API}/coins/solana?localization=false&tickers=false&community_data=false&developer_data=false")
        if cg and isinstance(cg, dict):
            market = cg.get("market_data", {})
            changes = market.get("price_change_percentage_7d", {})
            if isinstance(changes, dict) and changes.get("usd") is not None:
                result["sol_7d_change_pct"] = round(changes["usd"], 2)

        # Fear & Greed
        fng = _get_json(FEAR_GREED_API)
        if fng and isinstance(fng, dict):
            data = fng.get("data", [{}])[0] if fng.get("data") else {}
            result["fear_greed_index"] = data.get("value")
            result["fear_greed_label"] = data.get("value_classification")
    except Exception as e:
        result["error"] = str(e)
    return result
