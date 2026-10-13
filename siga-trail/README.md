# siga-trail

Append-only JSONL audit trail. Zero dependencies.

```python
from siga_trail import Trail

trail = Trail("~/.siga/audit.jsonl")
trail.record("audit", payload={"file": "trades.csv", "t": -3.45}, outcome="FAIL")
```

Every record is one JSON line — `{ts_ms, action, payload, outcome}` — locked,
flushed, and fsynced. An audit trail that can lose entries silently is worse
than no trail at all.

Design lineage: oneclaw's `audit.rs` (Mutex-guarded JSONL append), hardened
with per-record fsync and parameterized paths.

MIT — Selo <team@c1.run>
