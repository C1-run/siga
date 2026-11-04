// Section 3: PAIN POINTS (what you see vs what's real)

const ROWS = [
  { num: '01', seen: 'Win rate 65% in backtest', real: 'OOS n=13 = pure sample noise', badge: 'UNSTABLE', delay: '100ms' },
  { num: '02', seen: 'Sharpe 2.8 over 4 years', real: 'Zero transaction slippage modeled', badge: 'DRAG=100%', delay: '200ms' },
  { num: '03', seen: '10,000 parameter sweeps', real: 'Deflated Sharpe collapses to 0.12', badge: 'P-HACKED', delay: '300ms' },
  { num: '04', seen: 'Standard train/test random split', real: 'Serial autocorrelation temporal bleed', badge: 'LEAKAGE', delay: '400ms' },
]

export function PainPoints() {
  return (
    <section className="section section-md" id="pain-points">
      <div className="section-head">
        <span className="section-label">02 — WHAT YOU SEE vs WHAT'S REAL</span>
        <h2 className="section-title">The four fatal discrepancies in quant modeling.</h2>
      </div>
      <div className="pain-list" id="pain-points-list">
        {ROWS.map((row) => (
          <div className="pain-row-entry" key={row.num} style={{ transitionDelay: row.delay }}>
            <div className="pain-left">
              <span className="pain-num">{row.num}</span>
              <span className="pain-seen">{row.seen}</span>
            </div>
            <div className="pain-divider divider-expand"></div>
            <div className="pain-right">
              <span className="pain-real">{row.real}</span>
              <span className="pain-badge">{row.badge}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
