"""SQLite-backed state store for siga packages."""

import os
import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from siga_common.telemetry import registry, measure


class Durability:
    """Durability classification for state writes."""

    CRITICAL_SYNC = "critical_sync"
    CRITICAL_ASYNC = "critical_async"
    BATCHED = "batched"
    EPHEMERAL = "ephemeral"

    ALL = [CRITICAL_SYNC, CRITICAL_ASYNC, BATCHED, EPHEMERAL]


def _get_sqlite_config() -> dict[str, str]:
    """Read SQLite configuration from environment variables.

    Production defaults (Phase 4.1):
      journal_mode = WAL
      synchronous = NORMAL
      busy_timeout_ms = 5000
      wal_autocheckpoint = 1000

    Override via env vars if needed for specific workloads.
    """
    return {
        "journal_mode": os.getenv("SIGA_SQLITE_JOURNAL_MODE", "wal"),
        "synchronous": os.getenv("SIGA_SQLITE_SYNCHRONOUS", "normal"),
        "busy_timeout_ms": os.getenv("SIGA_SQLITE_BUSY_TIMEOUT_MS", "5000"),
        "wal_autocheckpoint": os.getenv("SIGA_SQLITE_WAL_AUTOCHECKPOINT", "1000"),
        "batch_size": os.getenv("SIGA_STATE_BATCH_SIZE", "1"),
        "flush_interval_ms": os.getenv("SIGA_STATE_FLUSH_INTERVAL_MS", "0"),
    }


class StateStore:
    """Simple key-value state store backed by SQLite.

    Each namespace is a separate table. Values are JSON-serialized.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_meta_table()
        self._apply_sqlite_config()
        self._sqlite_metadata = self._collect_sqlite_metadata()

    def _collect_sqlite_metadata(self) -> dict[str, Any]:
        conn = self._get_conn()
        try:
            metadata = {
                "sqlite_version": sqlite3.sqlite_version,
                "journal_mode": self._get_pragma(conn, "journal_mode"),
                "synchronous": self._get_pragma(conn, "synchronous"),
                "busy_timeout_ms": self._get_pragma(conn, "busy_timeout"),
                "wal_autocheckpoint": self._get_pragma(conn, "wal_autocheckpoint"),
                "database_path": str(self.path),
                "config": _get_sqlite_config(),
            }
        finally:
            conn.close()
        return metadata

    def _get_pragma(self, conn, pragma: str) -> Any:
        row = conn.execute(f"PRAGMA {pragma}").fetchone()
        return row[0] if row else None

    def _apply_sqlite_config(self) -> None:
        """Apply SQLite configuration from environment variables."""
        conn = self._get_conn()
        try:
            journal_mode = os.getenv("SIGA_SQLITE_JOURNAL_MODE")
            if journal_mode:
                conn.execute(f"PRAGMA journal_mode={journal_mode}")

            synchronous = os.getenv("SIGA_SQLITE_SYNCHRONOUS")
            if synchronous:
                conn.execute(f"PRAGMA synchronous={synchronous}")

            busy_timeout = os.getenv("SIGA_SQLITE_BUSY_TIMEOUT_MS")
            if busy_timeout:
                conn.execute(f"PRAGMA busy_timeout={int(busy_timeout)}")

            wal_autocheckpoint = os.getenv("SIGA_SQLITE_WAL_AUTOCHECKPOINT")
            if wal_autocheckpoint:
                conn.execute(f"PRAGMA wal_autocheckpoint={int(wal_autocheckpoint)}")
        finally:
            conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def get_sqlite_metadata(self) -> dict[str, Any]:
        """Return collected SQLite metadata and configuration."""
        return dict(self._sqlite_metadata)

    def _init_meta_table(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _state_kv (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (namespace, key)
                )
            """)

    @contextmanager
    def _conn_ctx(self):
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def set(self, namespace: str, key: str, value: Any, durability: str = Durability.CRITICAL_SYNC) -> None:
        """Store a value in a namespace."""
        if durability not in Durability.ALL:
            raise ValueError(f"Invalid durability level: {durability}. Must be one of {Durability.ALL}")

        with measure("state_store.set"):
            with measure("state_store.set.prepare"):
                serialized = json.dumps(value)
            conn = self._get_conn()
            try:
                with measure("state_store.set.execute"):
                    conn.execute("""
                        INSERT INTO _state_kv (namespace, key, value) VALUES (?, ?, ?)
                        ON CONFLICT(namespace, key) DO UPDATE SET
                            value=excluded.value,
                            updated_at=CURRENT_TIMESTAMP
                    """, (namespace, key, serialized))
                with measure("state_store.set.commit"):
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

            registry.counter(f"state_store.set.{durability}").inc()

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        """Get a value from a namespace."""
        with measure("state_store.get"):
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT value FROM _state_kv WHERE namespace=? AND key=?",
                    (namespace, key),
                ).fetchone()
                if row is None:
                    return default
                return json.loads(row[0])

    def delete(self, namespace: str, key: str) -> bool:
        """Delete a value. Returns True if deleted."""
        with self._conn_ctx() as conn:
            cur = conn.execute(
                "DELETE FROM _state_kv WHERE namespace=? AND key=?",
                (namespace, key),
            )
            return cur.rowcount > 0

    def namespace(self, namespace: str) -> dict[str, Any]:
        """Get all key-value pairs in a namespace."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM _state_kv WHERE namespace=?",
                (namespace,),
            ).fetchall()
            return {k: json.loads(v) for k, v in rows}

    def clear(self, namespace: str) -> int:
        """Clear all values in a namespace. Returns count deleted."""
        with self._conn_ctx() as conn:
            cur = conn.execute(
                "DELETE FROM _state_kv WHERE namespace=?",
                (namespace,),
            )
            return cur.rowcount
