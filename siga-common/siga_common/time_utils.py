"""UTC time helpers."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def utc_iso(dt: datetime = None) -> str:
    """Return ISO 8601 string for the given or current UTC datetime.

    Args:
        dt: Datetime to format (default: now)

    Returns:
        ISO 8601 string in UTC
    """
    if dt is None:
        dt = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def iso_to_dt(iso_str: str) -> datetime:
    """Parse an ISO 8601 string to a timezone-aware datetime."""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
