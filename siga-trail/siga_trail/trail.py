"""Append-only JSONL audit trail.

A new file handle is opened (and fsynced) per record. Slightly slower than
holding an fd open, but immune to buffered-loss on crash and to fd leaks.
Audit trails are low-frequency writes; correctness beats throughput here.
"""

from __future__ import annotations

import json
import os
import threading
import time


class Trail:
    def __init__(self, path: str):
        self._path = os.path.abspath(os.path.expanduser(path))
        self._lock = threading.Lock()
        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    @property
    def path(self) -> str:
        return self._path

    def record(self, action: str, payload=None, outcome: str = "ok") -> dict:
        """Append one entry; returns the entry as written."""
        if not action:
            raise ValueError("action must be non-empty")
        entry = {
            "ts_ms": int(time.time() * 1000),
            "action": action,
            "payload": payload,
            "outcome": outcome,
        }
        line = json.dumps(entry, separators=(",", ":"), ensure_ascii=False)
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
        return entry

    def read_all(self) -> list[dict]:
        """Read every entry back, in append order."""
        if not os.path.exists(self._path):
            return []
        with self._lock:
            with open(self._path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]

    def __len__(self) -> int:
        return len(self.read_all())
