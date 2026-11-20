"""siga-card tests — a frozen decision must stay frozen."""

import csv

import pytest
from siga_card import (
    CANCELLED,
    SETTLED,
    CardError,
    CardStore,
    freeze,
    new_card,
    settle,
)

CREATED = 1_763_000_000_000


def short(**kw):
    base = {
        "symbol": "ANT",
        "direction": "short",
        "thesis": "first-day pop reverts",
        "entry_lo": 110.0,
        "entry_hi": 112.0,
        "invalidation": 116.0,
        "target": 97.0,
        "notional": 111.0,
        "created_ms": CREATED,
    }
    base.update(kw)
    return new_card(**base)


def test_geometry_short_valid():
    c = short()
    assert 110 <= c.entry_mid <= 112
    assert c.risk_per_unit > 0
    assert c.rr > 2.0


def test_geometry_long_valid():
    c = new_card(
        symbol="ANT", direction="long", thesis="rebound",
        entry_lo=90, entry_hi=92, invalidation=88, target=97,
        notional=100, created_ms=CREATED,
    )
    assert c.entry_mid == 91
    assert c.rr >= 2.0


def test_missing_thesis_rejected():
    with pytest.raises(CardError, match="thesis"):
        short(thesis="   ")


def test_long_inverted_geometry_rejected():
    with pytest.raises(CardError, match="long card requires"):
        new_card(
            symbol="X", direction="long", thesis="x",
            entry_lo=90, entry_hi=92, invalidation=95, target=97,
            notional=100, created_ms=CREATED,
        )


def test_short_inverted_geometry_rejected():
    with pytest.raises(CardError, match="short card requires"):
        short(invalidation=100.0)


def test_freeze_hash_excludes_outcome():
    c = short()
    out = settle(c, exit_price=97.0, exit_ms=CREATED + 1000)
    assert freeze(c) == freeze(out) == out.frozen
    assert c.status == "open"          # original immutable
    assert out.status == SETTLED


def test_settlement_math_short():
    c = short()
    out = settle(c, exit_price=97.0, exit_ms=CREATED + 1000)
    assert out.pnl == pytest.approx(111.0 * (111.0 - 97.0) / 111.0)
    assert out.r_multiple == pytest.approx(2.8, abs=0.01)


def test_settlement_math_long_loss():
    c = new_card(
        symbol="ANT", direction="long", thesis="x",
        entry_lo=90, entry_hi=92, invalidation=88, target=97,
        notional=100, created_ms=CREATED,
    )
    out = settle(c, exit_price=87.0, exit_ms=CREATED + 1000)
    assert out.pnl < 0
    assert out.r_multiple < -1


def test_double_settle_rejected():
    out = settle(short(), exit_price=97.0, exit_ms=CREATED + 1)
    with pytest.raises(CardError, match="already settled"):
        settle(out, exit_price=95.0, exit_ms=CREATED + 2)


def test_settle_after_expiry_rejected():
    c = short(expire_ms=CREATED + 500)
    with pytest.raises(CardError, match="expired"):
        settle(c, exit_price=97.0, exit_ms=CREATED + 501)


def test_settle_before_creation_rejected():
    with pytest.raises(CardError, match="exit_ms"):
        settle(short(), exit_price=97.0, exit_ms=CREATED - 1)


def test_store_append_only_and_idempotent_id(tmp_path):
    s = CardStore(str(tmp_path / "cards.jsonl"))
    c = s.create(
        symbol="ANT", direction="short", thesis="x",
        entry_lo=110, entry_hi=112, invalidation=116, target=97,
        notional=111, created_ms=CREATED,
    )
    with pytest.raises(CardError, match="already exists"):
        s.create(
            symbol="ANT", direction="short", thesis="y",
            entry_lo=110, entry_hi=112, invalidation=116, target=97,
            notional=111, created_ms=CREATED, id=c.id,
        )
    assert len(s.all()) == 1


def test_store_settle_appends_same_decision_hash(tmp_path):
    s = CardStore(str(tmp_path / "cards.jsonl"))
    c = s.create(
        symbol="ANT", direction="short", thesis="x",
        entry_lo=110, entry_hi=112, invalidation=116, target=97,
        notional=111, created_ms=CREATED,
    )
    out = s.settle(c.id, exit_price=97.0, exit_ms=CREATED + 1)
    rows = s.all()
    assert len(rows) == 2
    assert rows[0].frozen == rows[1].frozen == out.frozen
    assert rows[0].status == "open"


def test_store_cancel_excluded_from_export(tmp_path):
    s = CardStore(str(tmp_path / "cards.jsonl"))
    c = s.create(
        symbol="X", direction="long", thesis="x",
        entry_lo=10, entry_hi=11, invalidation=9, target=13,
        notional=100, created_ms=CREATED,
    )
    assert s.cancel(c.id).status == CANCELLED
    out = str(tmp_path / "settled.csv")
    assert s.export_csv(out) == 0
    with open(out, encoding="utf-8") as f:
        assert len(list(csv.reader(f))) == 1  # header only


def test_export_csv_shape_for_siga_audit(tmp_path):
    s = CardStore(str(tmp_path / "cards.jsonl"))
    c = s.create(
        symbol="ANT", direction="short", thesis="x",
        entry_lo=110, entry_hi=112, invalidation=116, target=97,
        notional=111, created_ms=CREATED,
    )
    s.settle(c.id, exit_price=97.0, exit_ms=CREATED + 1)
    out = str(tmp_path / "settled.csv")
    assert s.export_csv(out) == 1
    with open(out, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert set(rows[0]) >= {"ts", "pnl", "notional"}
    assert float(rows[0]["pnl"]) > 0


def test_tampered_journal_rejected(tmp_path):
    p = tmp_path / "cards.jsonl"
    s = CardStore(str(p))
    s.create(
        symbol="ANT", direction="short", thesis="x",
        entry_lo=110, entry_hi=112, invalidation=116, target=97,
        notional=111, created_ms=CREATED,
    )
    import json

    row = json.loads(p.read_text(encoding="utf-8").strip())
    row["invalidation"] = 200.0          # change the decision after the fact
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(CardError, match="tampered"):
        s.all()
