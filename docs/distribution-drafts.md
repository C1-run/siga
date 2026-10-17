# Distribution Drafts — 2026-10-17

---

## 1. Show HN

**Title:**
Show HN: siga – a backtest audit engine that prints PASS/FAIL/INCONCLUSIVE

**Body:**

Most backtesting tools give you an equity curve and leave the judgment to you. siga answers a different question: "is this backtest actually real?"

You give it a CSV of per-trade P&L. It splits your data chronologically (70% in-sample, 30% out-of-sample), judges only the OOS portion with exact p-values, and prints one of three verdicts:

- PASS — the edge survives out-of-sample
- FAIL — it doesn't
- INCONCLUSIVE — not enough OOS data to say either way

```
$ siga audit trades.csv
OOS (30%)      n=36    mean=-34.75   t=-3.45  p=0.0015
VERDICT: FAIL
```

We built this because four of our own strategies died under it (lookahead leaks, cost drag, overfit parameters). One survived. Every check in the tool exists because it killed something we believed in.

It's not a backtesting engine — it's a complement to whatever you already use. Its input is a plain trade log, so it audits the output of any backtester: backtrader, vectorbt, Excel, whatever. The closer analogy is a linter: pylint never runs your code, it judges it.

GitHub: https://github.com/C1-run/siga
Landing: https://siga.c1.run

MIT, Python ≥3.11, zero dependencies for the core engine. `pip install` from source, one command to get a verdict.

---

## 2. r/algotrading

**Title:**
I audited 4 of my own strategies. 4 died. I open-sourced the tool that killed them.

**Body:**

Been lurking here for a while. Wanted to share something that saved me from myself.

I had a funding-rate strategy that looked great in backtest — t=7.86, 22/23 coins positive, clean equity curve. I was about to size up. Then I ran it through a chronological OOS audit (70/30 split, exact p-values, cost sensitivity) and it fell apart: the edge was concentrated in a regime that had already ended. The full-sample numbers were noise dressed as evidence.

That happened three more times with different strategies. Lookahead leaks, cost drag, parameter overfitting. Each time the audit caught it before I lost real money.

So I packaged the audit engine into a CLI: `siga audit your_trades.csv` → PASS / FAIL / INCONCLUSIVE. That's it. No backtesting framework, no indicators, no strategy generation. It audits the output of whatever backtester you already use — the input is just a CSV of per-trade P&L.

A few things it does that most tools don't:

- Verdict comes from OOS only. Full-sample stats are labeled "informational only — never the verdict"
- OOS n < 30 forces INCONCLUSIVE — refuses to give a fake answer on small samples
- Exact p-values (incomplete beta function), not normal approximations — small samples are exactly where the lie usually hides
- Cost sensitivity: `--cost-bps 10` re-runs the verdict net of assumed round-trip cost

The uncomfortable truth I had to accept: most backtests that look good are lying. Not because the statistics are wrong, but because nobody forces you to look at the OOS portion honestly.

GitHub: https://github.com/C1-run/siga (MIT, Python ≥3.11)
Landing: https://siga.c1.run

Happy to answer questions about the methodology. And if you have a strategy you're convinced is real — run it through and tell me what it says.

---

## 3. V2EX（量化交易节点）

**标题：**
我审计了自己的 4 个策略，4 个全挂了。我把杀死它们的工具开源了。

**正文：**

分享一下最近的教训，可能对你有用。

之前有个资金费率策略，回测数据很好看：t=7.86，22/23 个币为正，净值曲线漂亮。准备加仓之前跑了一次时序 OOS 审计（70/30 切分，精确 p 值，成本敏感性），直接崩了——edge 集中在已经结束的 regime 里，全样本数据就是噪音披着证据的外衣。

同样的事又发生了三次：前视偏差、成本侵蚀、参数过拟合。每次都是审计在实盘亏损之前抓住了问题。

于是把审计引擎做成了 CLI：`siga audit your_trades.csv` → PASS / FAIL / INCONCLUSIVE。没有回测框架，没有指标库，没有策略生成。它的输入就是每笔交易 P&L 的 CSV，审计任何回测器的输出。

几个大多数工具不做的事：

- 判决只看 OOS，全样本数字标注为 "informational only — never the verdict"
- OOS n < 30 强制 INCONCLUSIVE——宁可不给答案也不给假答案
- 精确 p 值（不完全贝塔函数），不用正态近似——小样本恰恰是谎言藏身的地方
- 成本敏感性：`--cost-bps 10` 扣除假设成本后重新判决

一个不得不接受的残酷事实：大多数看起来好的回测都在说谎。不是统计方法错了，是没人逼你诚实地看 OOS 部分。

GitHub: https://github.com/C1-run/siga（MIT，Python ≥3.11）
落地页: https://siga.c1.run

方法论相关问题欢迎讨论。如果你有自信的策略——跑一遍，告诉我结果。

---

## 发帖注意事项

- **Show HN**：最佳发布时间是美东上午 8-10 点（北京时间晚 8-10 点）。发布后第一个小时回复每条评论
- **r/algotrading**：先发，然后在评论区补充方法论细节（DSR、置换检验等），别全堆在正文里
- **V2EX**：选「量化交易」或「加密货币」节点。评论区会有人问"为什么不直接看 Sharpe"——回复指向精确 p 值和小样本闸门

## 追踪

发完帖后 24-48 小时检查：
- `wrangler kv key list --binding WAITLIST --remote`（waitlist 新增数）
- GitHub repo 的 star 增长
- Cloudflare Web Analytics 流量来源
