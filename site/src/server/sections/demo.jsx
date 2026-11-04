// Demo — live verdict terminal replay. Output below is the verbatim result of
// `siga audit siga-audit/examples/trades_sample.csv` from the public repo.
// No edits, no re-enactment — that's the whole point.

// [className, text] — cls: p=prompt cmd, d=dim, g=green, r=verdict red
const LINES = [
  ['p', 'siga audit siga-audit/examples/trades_sample.csv'],
  ['x', ''],
  ['d', 'siga audit — siga-audit/examples/trades_sample.csv'],
  ['d', '================================================================'],
  ['',  'Full sample   n=120   mean=-6.89   (informational only — never the verdict)'],
  ['',  'IS  (70%)      n=84    mean=+5.04   t=+0.89  p=0.3778'],
  ['g', 'OOS (30%)      n=36    mean=-34.75   t=-3.45  p=0.0015'],
  ['x', ''],
  ['',  'CHECK 01  OOS verdict ......... t=-3.45, p=0.0015 (significant)'],
  ['',  'CHECK 02  Cost sensitivity .... gross edge -34.75/trade — already negative before any cost'],
  ['',  'CHECK 03  Small-sample guard .. OOS n=36 >= 30 (ok)'],
  ['x', ''],
  ['r', 'VERDICT: FAIL'],
  ['r', '  - OOS edge significant and negative (t=-3.45, p=0.0015)'],
  ['x', ''],
  ['d', 'note: verdict is gross of costs — use --cost or --cost-bps for net'],
]

export function Demo() {
  return (
    <section className="demo-section" id="demo">
      <div className="demo-inner">
        <div className="section-tag">// LIVE VERDICT — REAL OUTPUT, NO EDITS</div>
        <h2 className="section-title">One command. One verdict.</h2>
        <p className="demo-sub">
          This is the actual output of <code>siga audit</code> on the synthetic sample
          shipped in the public repo. Run it yourself — same bytes in, same verdict out.
        </p>
        <div className="term-window" id="term-window">
          <div className="term-chrome">
            <span className="term-dot" />
            <span className="term-dot" />
            <span className="term-dot" />
            <span className="term-title">siga — audit</span>
          </div>
          {/* overflow-x:auto makes this a scrollable region, and Chrome puts
              scrollable containers in the tab order. Without a role and a name
              it would announce as an anonymous group. */}
          <div className="term-body" id="term-body" role="region" aria-label="Terminal output">
            {LINES.map(([cls, text], i) => (
              <div className={`term-line tl-${cls}`} data-tl={i} key={i}>
                {cls === 'p' ? <span className="term-prompt">$&nbsp;</span> : null}
                {cls === 'p' ? <span className="term-cmd" data-cmd={text} /> : text}
              </div>
            ))}
          </div>
        </div>
        <div className="demo-foot">
          <span className="demo-foot-note">[REPRODUCIBLE]</span>
          <span className="demo-foot-text">github.com/C1-run/siga → siga audit your_trades.csv</span>
        </div>
      </div>
    </section>
  )
}
