// Section 4: THE CHECKS (3D tilt cards) — every card maps 1:1 to a real
// siga-audit CHECK line. No feature here that the CLI doesn't ship.

const CHECKS = [
  {
    num: 'CHECK 01',
    title: 'Out-of-Sample Verdict',
    desc: 'Chronological 70/30 split. The verdict comes from the last 30% only — the full sample is printed, labeled informational, and never used. p-values come from the t-distribution via the incomplete beta function, with no normal approximation to flatter small samples.',
    foot: 'OOS ONLY',
    delay: '80ms',
    icon: (
      <svg className="check-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="9"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
      </svg>
    ),
  },
  {
    num: 'CHECK 02',
    title: 'Cost Sensitivity',
    desc: '--cost for a fixed per-trade cost, --cost-bps for basis points of notional. The verdict re-runs net — and the default verdict is labeled gross in the output itself.',
    foot: 'NET RE-RUN',
    delay: '160ms',
    icon: (
      <svg className="check-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
      </svg>
    ),
  },
  {
    num: 'CHECK 03',
    title: 'Small-Sample Refusal',
    desc: 'OOS n < 30 forces INCONCLUSIVE. No answer rather than a fake one — the 30-trade minimum is a guardrail, not a judgment call. Under 10 trades total, the run errors out instead of guessing.',
    foot: 'N < 30 → WITHHELD',
    delay: '240ms',
    icon: (
      <svg className="check-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
      </svg>
    ),
  },
]

export function FiveChecks() {
  return (
    <section className="section section-lg" id="checks">
      <div className="section-head head-narrow">
        <span className="section-label">03 — THE CHECKS</span>
        <h2 className="section-title">Three checks. One verdict.</h2>
        <p className="section-sub">Every check exists because it killed one of our own strategies. Nothing here runs your code — it judges the trade log your backtester already produced.</p>
      </div>
      <div className="checks-grid" id="checks-grid">
        {CHECKS.map((check) => (
          <div className="glass-card check-card check-card-entry interactive-tilt-card" key={check.num} style={{ transitionDelay: check.delay }}>
            <div className="check-top-border"></div>
            <div>
              {check.icon}
              <div className="check-num">{check.num}</div>
              <h3 className="check-title">{check.title}</h3>
              <p className="check-desc">{check.desc}</p>
            </div>
            <div className="check-foot">{check.foot}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
