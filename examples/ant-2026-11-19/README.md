# Case: ANT, 2026-11-19/20

A real, self-reported discretionary trade sequence on `xyz:ANT` (Hyperliquid
pre-IPO perp). No broker statement was imported; prices are the prices reported
by the user and cross-checked against the public `candleSnapshot` feed.

## What happened

1. First printed trade `111.005` (00:48:30 UTC+8). The user shorted near `111`
   from their phone and covered near `97` about 30 minutes later. **Realized
   profit. One trade.**
2. The user then went **long from `97`** and, at the time of writing, was still
   holding near `91.4` (unrealized ≈ −5.8%). **Unsettled.**

Those two positions are the opposite sides of the same question. If the short
at `111` was right because a first-day pop mean-reverts, the long at `97` is a
different claim: that the reversion has already gone far enough. A single
profitable short does not establish either claim.

## What the tool actually says

```bash
PYTHONPATH=siga-audit:siga-trail python3 - <<'PY'
import argparse
from siga_audit.cli import add_audit_parser, run_audit_cli
p = argparse.ArgumentParser(prog='siga')
add_audit_parser(p.add_subparsers(dest='cmd'))
run_audit_cli(p.parse_args(['audit', 'examples/ant-2026-11-19/trades.csv',
                            '--cost-bps', '10']))
PY
```

Output, verbatim:

```
error: need at least 10 trades to audit, got 1
```

Not `PASS`. Not `FAIL`. Not "no edge". **The instrument refuses to judge n=1.**
That refusal is the entire point of the repo: it would rather give no answer
than a fake one.

`open_position.md` is deliberately **not** in `trades.csv`. An unsettled trade
is not an outcome; adding it would silently turn a mark-to-market number into a
"result".

## What would change the verdict

To move from `n=1` to something the tool can judge:

- log **at least 10 settled trades** with the same rule applied (`ts,pnl,notional`);
- reach **OOS n ≥ 30** before reading the verdict (chronological 70/30 split);
- report **net of cost** (`--cost-bps`), not gross;
- keep the rule text frozen in `rule.md` before the next trade — changing the
  rule after seeing the result is how a log becomes a story.

Until then the honest statement is: *one discretionary short made money; its
edge is unmeasured.* Both "you have an edge" and "you have no edge" are claims
without evidence.

## Why this is in `siga`

Because the repo's job is to turn a P&L sequence into a verdict with an explicit
small-sample guard. This case is the guard firing on a real, profitable trade —
the most common way a genuine result gets mistaken for a repeatable strategy.
