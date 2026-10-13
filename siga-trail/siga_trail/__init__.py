"""siga-trail — append-only JSONL audit trail.

Every record is one JSON line: {ts_ms, action, payload, outcome}.
Writes are locked, flushed, and fsynced — an audit trail that can lose
entries silently is worse than no trail at all.

Design lineage: oneclaw's audit.rs (Mutex-guarded JSONL append), hardened
with per-record fsync and parameterized paths.
"""

from siga_trail.trail import Trail

__version__ = "0.1.0"
__all__ = ["Trail", "__version__"]
