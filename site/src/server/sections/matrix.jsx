// Section 5: COMPETITOR MATRIX (sequential flash & draw)
// .matrix-check / .matrix-siga-col-line are wired to main.js — do not rename.
// Rows are limited to what siga-audit actually prints. See siga-audit/README.

const ROWS = [
  'Chronological OOS split — verdict from the last 30% only',
  'Exact t-distribution p-values, no normal approximation',
  'Cost sensitivity re-run: --cost / --cost-bps',
  'Refuses a verdict when OOS n < 30',
  'One-word output: PASS / FAIL / INCONCLUSIVE',
]

function MatrixCheck() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="matrix-check"
      fill="none"
      stroke="currentColor"
      stroke-width="2.5"
      viewBox="0 0 24 24"
    >
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  )
}

export function Matrix() {
  return (
    <section className="section section-table" id="matrix">
      <div className="section-head">
        <span className="section-label">04 — WHY NOT ANOTHER BACKTEST TOOL</span>
        <h2 className="section-title">Optimizers sell optimism. We sell the cold autopsy.</h2>
      </div>
      <div className="matrix-wrap glass-card">
        <table className="matrix-table" id="matrix-table">
          <thead>
            <tr>
              <th className="th-name">Audit Capability</th>
              <th className="th-center" colspan="3">Typical backtest tooling</th>
              <th className="th-siga">
                <span className="siga-name">siga</span>
                <span className="matrix-siga-col-line col-line-left" id="matrix-left-line"></span>
                <span className="matrix-siga-col-line col-line-right" id="matrix-right-line"></span>
              </th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((label) => (
              <tr className="matrix-row" key={label}>
                <td className="matrix-cell-name">{label}</td>
                {/* The visual encoding is a dash versus a check glyph. Screen
                    readers get the meaning as text; the glyph itself is hidden. */}
                <td className="matrix-cell-dash">
                  <span aria-hidden="true">—</span>
                  <span className="sr-only">Not included</span>
                </td>
                <td className="matrix-cell-dash">
                  <span aria-hidden="true">—</span>
                  <span className="sr-only">Not included</span>
                </td>
                <td className="matrix-cell-dash">
                  <span aria-hidden="true">—</span>
                  <span className="sr-only">Not included</span>
                </td>
                <td className="matrix-cell-siga">
                  <MatrixCheck />
                  <span className="sr-only">Included</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="matrix-foot">* Backtest platforms report metrics. They do not issue a statistical verdict on your trade log.</div>
    </section>
  )
}
