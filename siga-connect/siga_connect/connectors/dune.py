"""Dune Analytics connector — fetch query results as trade history."""

from __future__ import annotations

import httpx

from siga_connect.models import FetchResult

_BASE = "https://api.dune.com/api/v1"


def fetch_trades(query_id: int, api_key: str, limit: int = 500) -> FetchResult:
    """Fetch Dune query results and normalize to trade P&L series.

    The Dune query must return a result set with at minimum:
    - A column that can be interpreted as P&L (pnl, profit, return, etc.)
    - Optionally: notional, time, symbol

    The connector auto-detects the P&L column by name matching.
    """
    url = f"{_BASE}/query/{query_id}/results"
    headers = {"X-Dune-API-Key": api_key}
    params = {"limit": limit}

    with httpx.Client(timeout=60) as client:
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    rows = data.get("result", {}).get("rows", [])
    if not rows:
        raise ValueError(f"Dune query {query_id} returned no rows")

    # Auto-detect P&L column
    first_row = rows[0]
    pnl_col = _pick_column(
        list(first_row.keys()),
        ("pnl", "profit", "return", "net", "pl", "pnl_usd", "net_pnl"),
    )
    if pnl_col is None:
        raise ValueError(
            f"no P&L column found in Dune result (looked for: pnl, profit, return, net, pl). "
            f"Available columns: {list(first_row.keys())}"
        )

    notional_col = _pick_column(
        list(first_row.keys()),
        ("notional", "notional_usd", "trade_value", "value", "volume"),
    )

    pnl: list[float] = []
    notional: list[float] = []
    for row in rows:
        pnl.append(_parse_number(row.get(pnl_col)))
        if notional_col:
            notional.append(abs(_parse_number(row.get(notional_col, 0))))

    return FetchResult(
        pnl=pnl,
        notional=notional if notional_col else None,
        source=f"dune:query-{query_id}",
        n_trades=len(pnl),
    )


def _pick_column(header: list[str], candidates: tuple[str, ...]) -> str | None:
    lowered = [h.strip().lower() for h in header]
    for cand in candidates:
        if cand in lowered:
            return header[lowered.index(cand)]
    return None


def _parse_number(raw) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    return float(str(raw).strip().replace("$", "").replace(",", ""))
