// Section 7: FAQ (accordion with 3D auto-open)
// .faq-item / .faq-toggle are wired to main.js — do not rename.

const ITEMS = [
  {
    q: 'Does siga run in the cloud? Do you see my trades?',
    a: 'No. `siga audit` is a local CLI — the trade log never leaves your machine. There is no account, no upload, no telemetry. Other subcommands, like `siga portfolio value`, do fetch public market prices.',
  },
  {
    q: 'What inputs does it accept?',
    a: 'One CSV: one row per trade, chronological, with a P&L column (auto-detected). It judges the output of any backtester — backtrader, vectorbt, a spreadsheet — because the input is the trade log, not the code.',
  },
  {
    q: 'Why is a PASS verdict so difficult to achieve?',
    a: 'Because PASS requires out-of-sample n ≥ 30, two-tailed p < 0.05, and a positive OOS mean — and the default verdict is gross of costs, stated in the output itself. A PASS is a necessary condition, not proof of edge. Many honest strategies get INCONCLUSIVE instead: FAIL demands a significantly negative OOS edge, and no evidence of edge is not evidence of no edge.',
  },
  {
    q: 'What happens if my strategy gets FAIL or INCONCLUSIVE?',
    a: 'You get the reasons printed with the numbers behind them — means, t, p, cost assumptions. A FAIL is the cheapest outcome available: you just skipped the infrastructure you were about to build. INCONCLUSIVE is not a pass either — it means the sample cannot support any verdict yet.',
  },
  {
    q: 'Why is the audit engine open source?',
    a: "Fair question — a lot of open-source trading tools are open precisely because they have no alpha, and we'd rather say it ourselves than let you wonder. What's open is the measurement machinery: the checks, the verdict rules, the discipline (four of our own strategies died under them — that's the product demo). What's closed is whatever survived: passing strategies get traded, not published. That asymmetry is deliberate — whatever we eventually charge for will be built on the survivors, so the audit itself has no incentive to flatter anyone.",
  },
]

const DELAYS = ['80ms', '160ms', '240ms', '320ms', '400ms']

export function Faq() {
  return (
    <section className="section section-md" id="faq">
      <div className="section-head">
        <span className="section-label">05 — FAQ</span>
        <h2 className="section-title">Frequently asked questions regarding rigor &amp; confidentiality.</h2>
      </div>
      <div className="faq-list" id="faq-accordion">
        {ITEMS.map((item, i) => (
          <div className="faq-item faq-entry" key={item.q} style={{ transitionDelay: DELAYS[i] }}>
            {/* aria-expanded is kept in sync by main.js; the first item auto-opens
                on scroll, so the server must not hardcode "true". */}
            <button
              className="faq-toggle"
              type="button"
              id={`faq-toggle-${i}`}
              aria-expanded="false"
              aria-controls={`faq-panel-${i}`}
            >
              <span className="faq-question">{item.q}</span>
              <span className="faq-icon" aria-hidden="true">+</span>
            </button>
            <div
              className="faq-content"
              id={`faq-panel-${i}`}
              role="region"
              aria-labelledby={`faq-toggle-${i}`}
            >
              <div className="faq-inner">
                <p className="faq-answer">{item.a}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
