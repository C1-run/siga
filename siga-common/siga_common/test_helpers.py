"""Test helpers for siga packages."""

import tempfile
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def temp_db_path(suffix: str = ".db"):
    """Provide a temporary file path for SQLite testing.

    Cleans up the file on exit.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    Path(path).unlink()
    try:
        yield Path(path)
    finally:
        p = Path(path)
        if p.exists():
            p.unlink()
