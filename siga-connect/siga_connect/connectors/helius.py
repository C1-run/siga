"""Helius connector — fetch Solana address transaction history."""

from __future__ import annotations

import httpx

from siga_connect.models import FetchResult

_BASE = "https://api.helius.xyz/v0"


def fetch_trades(address: str, api_key: str, limit: int = 500) -> FetchResult:
    """Fetch Solana address transactions via Helius.

    Extracts swap/trade events from transaction history and computes
    approximate P&L from token balance changes.

    Note: Solana transactions are program invocations, not simple trades.
    This connector extracts token swaps (e.g., Jupiter, Raydium) and
    computes P&L from the SOL/USDC value delta.
    """
    url = f"{_BASE}/addresses/{address}/transactions"
    params = {"api-key": api_key, "limit": min(limit, 100)}  # Helius max 100
    all_txs: list[dict] = []

    with httpx.Client(timeout=60) as client:
        # Helius paginates with before/after signatures
        before = None
        while len(all_txs) < limit:
            if before:
                params["before"] = before
            resp = client.get(url, params=params)
            resp.raise_for_status()
            txs = resp.json()
            if not txs:
                break
            all_txs.extend(txs)
            if len(txs) < params["limit"]:
                break
            before = txs[-1]["signature"]

    # Extract swap events and compute P&L
    pnl: list[float] = []
    notional: list[float] = []

    for tx in all_txs:
        # Look for token transfer events that look like swaps
        # This is a heuristic — a full implementation would parse
        # Jupiter/Raydium program logs
        trade = _extract_swap_pnl(tx)
        if trade is not None:
            pnl.append(trade["pnl"])
            notional.append(trade["notional"])

    return FetchResult(
        pnl=pnl,
        notional=notional if notional else None,
        source=f"helius:{address[:8]}...",
        n_trades=len(pnl),
    )


def _extract_swap_pnl(tx: dict) -> dict | None:
    """Extract approximate P&L from a Solana swap transaction.

    Looks for tokenTransfers that indicate a two-sided swap.
    Returns None if the transaction doesn't look like a trade.
    """
    transfers = tx.get("tokenTransfers", [])
    if len(transfers) < 2:
        return None

    # Heuristic: find the largest in/out pair
    in_amt = 0.0
    out_amt = 0.0
    in_mint = None
    out_mint = None

    for t in transfers:
        amt = float(t.get("tokenAmount", 0))
        mint = t.get("mint", "")
        direction = t.get("direction", "")

        if direction == "in" and amt > in_amt:
            in_amt = amt
            in_mint = mint
        elif direction == "out" and amt > out_amt:
            out_amt = amt
            out_mint = mint

    if in_amt == 0 or out_amt == 0:
        return None

    # If one side is SOL or USDC, we can compute approximate USD value
    sol_mints = {"So11111111111111111111111111111111111111112"}
    usdc_mints = {"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"}

    pnl = 0.0
    notional = 0.0

    if out_mint in sol_mints or out_mint in usdc_mints:
        # Sold token for SOL/USDC
        pnl = in_amt - out_amt  # rough approximation
        notional = out_amt
    elif in_mint in sol_mints or in_mint in usdc_mints:
        # Bought token with SOL/USDC
        pnl = in_amt - out_amt  # rough approximation
        notional = in_amt

    if notional == 0:
        return None

    return {"pnl": pnl, "notional": notional}
