"""Shared test fixtures for siga-briefing."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_siga(tmp_path, monkeypatch):
    """Redirect portfolio storage to tmp, reset price source singleton, force stub."""
    # 1. Isolate portfolio file
    monkeypatch.setattr(
        "siga_briefing.portfolio.DEFAULT_PATH",
        tmp_path / "portfolio.json",
    )
    # 2. Reset price source singleton so each test starts fresh
    import siga_briefing.prices as prices_mod
    monkeypatch.setattr(prices_mod, "_default", None)
    # 3. Force stub mode — prevents real CoinGecko calls even if monkeypatch misses
    monkeypatch.setenv("SIGA_PRICE_SOURCE", "stub")
