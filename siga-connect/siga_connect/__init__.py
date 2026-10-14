"""siga-connect — data connectors for pulling trade history into siga."""

from siga_connect.models import FetchResult
from siga_connect.fetch import fetch_trades

__all__ = ["FetchResult", "fetch_trades"]
