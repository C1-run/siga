"""Trail tests — the trail itself must be beyond reproach."""

import json
import threading

import pytest

from siga_trail import Trail


def test_record_schema(tmp_path):
    t = Trail(str(tmp_path / "audit.jsonl"))
    entry = t.record("audit", payload={"file": "x.csv"}, outcome="FAIL")
    assert entry["action"] == "audit"
    assert entry["payload"] == {"file": "x.csv"}
    assert entry["outcome"] == "FAIL"
    assert isinstance(entry["ts_ms"], int)


def test_append_only(tmp_path):
    p = str(tmp_path / "audit.jsonl")
    t = Trail(p)
    t.record("first")
    t.record("second")
    t.record("third")
    entries = t.read_all()
    assert [e["action"] for e in entries] == ["first", "second", "third"]


def test_default_outcome_and_null_payload(tmp_path):
    t = Trail(str(tmp_path / "a.jsonl"))
    entry = t.record("ping")
    assert entry["outcome"] == "ok"
    assert entry["payload"] is None


def test_nested_path_created(tmp_path):
    p = str(tmp_path / "deep" / "nested" / "audit.jsonl")
    t = Trail(p)
    t.record("x")
    assert len(t.read_all()) == 1


def test_empty_read(tmp_path):
    t = Trail(str(tmp_path / "missing.jsonl"))
    assert t.read_all() == []
    assert len(t) == 0


def test_empty_action_rejected(tmp_path):
    t = Trail(str(tmp_path / "a.jsonl"))
    with pytest.raises(ValueError):
        t.record("")


def test_concurrent_writes_lose_nothing(tmp_path):
    p = str(tmp_path / "concurrent.jsonl")
    t = Trail(p)
    threads = [
        threading.Thread(target=lambda: [t.record(f"e{i}") for i in range(20)])
        for _ in range(10)
    ]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    entries = t.read_all()
    assert len(entries) == 200
    # Every line must be intact JSON — no interleaved writes.
    with open(p) as f:
        for line in f:
            json.loads(line)


def test_lines_are_compact_json(tmp_path):
    p = str(tmp_path / "a.jsonl")
    Trail(p).record("x", payload={"k": "v"})
    with open(p) as f:
        line = f.readline()
    assert '"action":"x"' in line  # no spaces — compact separators
