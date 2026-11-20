# siga-card

Pre-registered decision cards, frozen before entry. Zero dependencies.

`siga audit` judges PnL after the fact. `siga-card` records the **decision**
before the outcome is known — direction, thesis, entry zone, invalidation,
target, time boundary — so the audit engine can judge the plan you actually
committed to, not a story reconstructed afterwards.

## Why

The concept is distilled from ZenTrade's opportunity card
(`wuyangfan234/zentrade`, original code MIT). No code was copied: this is an
independent implementation under siga's MIT license. ZenTrade bundles
third-party GPL-3.0 / MPL-2.0 / CC BY-NC-SA components; none are used here.

What was kept: **a card is a frozen object with a geometric invalidation and
a time boundary, and settle rules are fixed before entry.**
What was left out: the strategy scoring, data feeds, UI, and paper broker.
Those are not siga's job.

## The rules (fail-closed)

- long: `invalidation < entry_lo <= entry_hi < target`
- short: `target < entry_lo <= entry_hi < invalidation`
- `thesis` is required and non-empty — a card without a reason cannot be frozen
- a card has an optional `expire_ms`; settling after it is refused, not silently allowed
- once written, a card line is immutable; settlement appends a new snapshot with
  the **same decision hash** and the outcome fields added
- cancelled cards are never exported as PnL

## Library

```python
from siga_card import CardStore

store = CardStore("cards.jsonl")
card = store.create(
    symbol="ANT", direction="short",
    thesis="first-day pop reverts toward issue price",
    entry_lo=110.0, entry_hi=112.0,
    invalidation=116.0, target=97.0,
    notional=111.0, created_ms=1763000000000,
)
out = store.settle(card.id, exit_price=97.0, exit_ms=1763001800000)
print(out.pnl, out.r_multiple)          # 14.00, 2.8
store.export_csv("settled.csv")          # ts,pnl,notional,side,symbol
```

Then:

```bash
siga audit settled.csv --cost-bps 10
```

## CLI

```bash
siga card new --symbol ANT --direction short \
  --thesis "first-day pop reverts" \
  --entry-lo 110 --entry-hi 112 --invalidation 116 --target 97 \
  --notional 111 --file cards.jsonl

siga card settle <id> --exit-price 97 --file cards.jsonl
siga card list --file cards.jsonl
siga card export --out settled.csv --file cards.jsonl
```

## What this does not do

It does not find edges, size positions, place orders, or tell you the direction.
It makes your own decision auditable. A single card is still n=1 — `siga audit`
will refuse to judge it, correctly.
