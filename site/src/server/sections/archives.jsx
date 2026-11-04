// Section 2: DEATH ARCHIVE NARRATIVE (3 case cards + connectors)
// IDs/classes here are wired to main.js — do not rename.

export function DeathArchive() {
  return (
    <section className="section section-md" id="death-archive">
      <div className="section-head">
        <span className="section-label">01 — FOUR DEATHS, ONE SURVIVOR</span>
        <h2 className="section-title">The forensic record of strategies that looked invincible.</h2>
        <p className="section-sub">These case files come from our private forensics tooling — leak detection and multiple-testing penalties. The open-source CLI judges trade logs: out-of-sample verdict, cost sensitivity, sample size.</p>
      </div>

      <div className="case-flow">
        {/* CARD 1: casea (FAIL) */}
        <article className="glass-card case-card case-fail card-casea-entry" id="card-casea">
          <div className="case-head">
            <div className="case-badges">
              <span className="fail-stamp-anim stamp stamp-fail" id="casea-fail-stamp">FAIL</span>
              <span className="case-id">CASE #01 // STRATEGY A</span>
            </div>
            <span className="case-tag">Lookahead Leak</span>
          </div>
          <h3 className="case-title">One line of NumPy lied to you 15×</h3>

          <div className="case-stats case-stats-casea">
            <div className="stat-pair">
              <div>
                <div className="stat-label">Reported Walk-Forward</div>
                <div className="stat-value stat-lg stat-bright casea-split-crack" id="casea-reported-stat">+236%</div>
              </div>
              <div className="stat-arrow">
                <svg fill="none" height="24" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" width="24">
                  <path className="svg-connector-line" d="M5 12h14M13 6l6 6-6 6" id="casea-arrow-path"></path>
                </svg>
              </div>
              <div>
                <div className="stat-label">Leak Removed</div>
                <div className="stat-value stat-lg stat-muted" id="casea-leak-stat">+15.30%</div>
              </div>
            </div>
            <div className="stat-side">
              <div className="stat-label">With 5bps Round-Trip Slippage</div>
              <div className="stat-value stat-md stat-red" id="casea-slip-stat">-48.60%</div>
            </div>
          </div>

          {/* Interactive AST forensic side-by-side code diff */}
          <div className="sync-diff" id="casea-sync-diff">
            <div className="sync-diff-head">
              <span className="sync-diff-title">INTERACTIVE AST FORENSIC INSPECTION</span>
              <div className="sync-badge">
                <span className="dot dot-sm dot-green animate-pulse"></span>
                <span>[SYNC HOVER ACTIVE]</span>
              </div>
            </div>
            <div className="diff-grid">
              {/* Panel 01.A (defective leak) */}
              <div className="diff-panel" id="diff-panel-a">
                <div className="diff-panel-head">
                  <span className="diff-panel-title">01.A // LEAK DETECTED</span>
                  <span className="diff-flag flag-fail">[FAIL] mode="same"</span>
                </div>
                <div className="diff-lines">
                  <div className="diff-code-line" data-line="1" data-sync-group="header">
                    <span className="line-num">1</span>
                    <span><span className="tok-kw">def</span> <span className="tok-fn">generate_alpha</span>(prices, window=20):</span>
                  </div>
                  <div className="diff-code-line" data-line="2" data-sync-group="weights">
                    <span className="line-num">2</span>
                    <span>&nbsp;&nbsp;&nbsp;&nbsp;weights = np.exp(np.linspace(-1, 0, window))</span>
                  </div>
                  <div className="tooltip-anchor">
                    <div className="diff-code-line diff-line-leak" data-line="3" data-sync-group="leak">
                      <span className="leak-left">
                        <span className="line-num">3</span>
                        <span className="tok-comment"># LOOKAHEAD: mode='same' samples t+1..t+9</span>
                      </span>
                      <span className="leak-tag"><span className="dot dot-sm dot-red animate-pulse"></span><span>AST DIAGNOSTIC</span></span>
                    </div>
                    <div className="diff-tooltip">
                      <div className="tt-head">
                        <span className="tt-title">[AST AUDIT // CRITICAL LOOKAHEAD DETECTED]</span>
                        <span className="tt-lines">LINE 3–4</span>
                      </div>
                      <p className="tt-body">Static AST trace discovered <code className="code-inline code-red">numpy.convolve(..., mode='same')</code> centered sliding kernel. Because window is centered at bar t, kernel indices (t+1 ... t+k) access unclosed future prices within backtest training, generating false Sharpe inflation (+236%) that collapses immediately on live tick execution.</p>
                      <div className="tt-grid">
                        <div><span className="tt-k">GATE</span><span className="tt-v">01_TEMPORAL</span></div>
                        <div><span className="tt-k">INDEX OFFSET</span><span className="tt-v tt-v-red">+5 BARS</span></div>
                        <div><span className="tt-k">SEVERITY</span><span className="tt-v tt-v-red">TERMINAL</span></div>
                      </div>
                    </div>
                  </div>
                  <div className="diff-code-line diff-line-leak" data-line="4" data-sync-group="leak">
                    <span className="line-num">4</span>
                    <span>&nbsp;&nbsp;&nbsp;&nbsp;raw_signal = np.convolve(prices, weights, mode=<span className="tok-flag tok-flag-red">'same'</span>)</span>
                  </div>
                  <div className="diff-code-line" data-line="5" data-sync-group="return">
                    <span className="line-num">5</span>
                    <span>&nbsp;&nbsp;&nbsp;&nbsp;<span className="tok-kw">return</span> np.sign(raw_signal)</span>
                  </div>
                </div>
                <div className="diff-verdict diff-verdict-fail">
                  <span className="verdict-label">[FAIL]</span>
                  <span>Centered convolution spans future bars. Theoretical +236% is a paper mirage.</span>
                </div>
              </div>
              {/* Panel 01.B (causal fix) */}
              <div className="diff-panel" id="diff-panel-b">
                <div className="diff-panel-head">
                  <span className="diff-panel-title">01.B // CAUSAL FIX</span>
                  <span className="diff-flag flag-pass">[PASS] mode="valid"</span>
                </div>
                <div className="diff-lines diff-lines-scroll">
                  <div className="diff-code-line" data-line="1" data-sync-group="header">
                    <span className="line-num">1</span>
                    <span><span className="tok-kw">def</span> <span className="tok-fn">generate_alpha</span>(prices, window=20):</span>
                  </div>
                  <div className="diff-code-line" data-line="2" data-sync-group="weights">
                    <span className="line-num">2</span>
                    <span>&nbsp;&nbsp;&nbsp;&nbsp;weights = np.exp(np.linspace(-1, 0, window))</span>
                  </div>
                  <div className="diff-code-line diff-line-fix" data-line="3" data-sync-group="leak">
                    <span className="line-num">3</span>
                    <span className="tok-comment"># STRICT CAUSAL: pad left, mode='valid'</span>
                  </div>
                  <div className="diff-code-line diff-line-fix" data-line="4" data-sync-group="leak">
                    <span className="line-num">4</span>
                    <span>&nbsp;&nbsp;&nbsp;&nbsp;padded = np.pad(prices, (window-1, 0), 'edge')</span>
                  </div>
                  <div className="diff-code-line diff-line-fix" data-line="5" data-sync-group="leak">
                    <span className="line-num">5</span>
                    <span>&nbsp;&nbsp;&nbsp;&nbsp;raw_signal = np.convolve(padded, weights, mode=<span className="tok-flag tok-flag-green">'valid'</span>)</span>
                  </div>
                  <div className="diff-code-line" data-line="6" data-sync-group="return">
                    <span className="line-num">6</span>
                    <span>&nbsp;&nbsp;&nbsp;&nbsp;<span className="tok-kw">return</span> np.sign(raw_signal)</span>
                  </div>
                </div>
                <div className="diff-verdict diff-verdict-pass">
                  <span className="verdict-label">[PASS]</span>
                  <span>Strict t-lag causal alignment. Leak eliminated (+15.30%), real slip exposed (-48.60%).</span>
                </div>
              </div>
            </div>
          </div>

          <p className="case-note"><code className="code-inline">np.convolve(mode='same')</code> silently indexed future bars during convolution alignment. Fixed: 5bps → −48.60%. Total paper mirage.</p>
        </article>

        <div className="case-connector">
          <svg fill="none" height="48" viewBox="0 0 20 48" width="20">
            <line className="svg-connector-line" stroke="rgba(255,255,255,0.18)" stroke-width="1.5" x1="10" x2="10" y1="0" y2="40"></line>
            <polygon fill="rgba(255,255,255,0.25)" points="6,38 10,46 14,38"></polygon>
          </svg>
        </div>

        {/* CARD 2: caseb + casec (FAIL) */}
        <article className="glass-card case-card case-fail card-caseb-entry" id="card-caseb">
          <svg aria-hidden="true" className="rejection-overlay" preserveAspectRatio="none" viewBox="0 0 100 100">
            <line className="rejection-stroke" id="caseb-reject-line" stroke="#FF4D4D" stroke-linecap="round" stroke-opacity="0.35" stroke-width="0.8" x1="2" x2="98" y1="98" y2="2"></line>
          </svg>
          <div className="case-head">
            <div className="case-badges">
              <span className="stamp stamp-fail-soft">FAIL</span>
              <span className="case-id">CASE #02 // STRATEGIES B &amp; C</span>
            </div>
            <span className="case-tag">Overfitting &amp; DSR Failure</span>
          </div>
          <h3 className="case-title">345 tests green. Zero revenue. Correct ≠ profitable.</h3>

          <div className="case-stats case-stats-3">
            <div>
              <div className="stat-label">Strategy B t-stat</div>
              <div className="stat-value stat-md stat-red count-target" data-prefix="t=" data-suffix="" data-target="-4.16">t=-4.16</div>
              <div className="stat-sub">58 trades, gross PnL</div>
            </div>
            <div>
              <div className="stat-label">Strategy C OOS</div>
              <div className="stat-value stat-md stat-muted count-target" data-prefix="t=" data-suffix="" data-target="0.38">t=0.38</div>
              <div className="stat-sub">DSR=0.298 (noise)</div>
            </div>
            <div>
              <div className="stat-label">Rust Test Suite</div>
              <div className="stat-value stat-md stat-bright stat-fade count-target" data-prefix="" data-suffix=" tests" data-target="345" id="caseb-tests-green">345 tests</div>
              <div className="stat-sub">44,408 LOC verified</div>
            </div>
          </div>

          <p className="case-note">Unit test perfection cannot engineer edge. High engineering rigor masked severe statistical insignificance under deflated Sharpe ratio tests.</p>
        </article>

        <div className="case-connector">
          <svg fill="none" height="48" viewBox="0 0 20 48" width="20">
            <line className="svg-connector-line" stroke="rgba(255,255,255,0.18)" stroke-width="1.5" x1="10" x2="10" y1="0" y2="40"></line>
            <polygon fill="rgba(255,255,255,0.25)" points="6,38 10,46 14,38"></polygon>
          </svg>
        </div>

        {/* CARD 3: cased (INCONCLUSIVE, survivor) */}
        <article className="glass-card case-card survivor-glow-border card-cased-entry" id="card-cased">
          <div className="case-head">
            <div className="case-badges">
              <span className="stamp stamp-inc">INCONCLUSIVE</span>
              <span className="case-id">CASE #03 // STRATEGY D</span>
            </div>
            <span className="case-survivor">
              <span className="dot dot-green sonar-dot"></span>
              SURVIVOR CANDIDATE
            </span>
          </div>
          <h3 className="case-title">t=7.86 but no real money yet</h3>

          <div className="case-stats case-stats-3">
            <div>
              {/* Deliberately NOT server-rendered with its final value like the
                  other cards. This t=7.86 is one of the three t-stats that
                  docs/audit-intrabar-bug-2026-10-13.md invalidated: it came from
                  the engine judging barriers on daily closes only. Until the card
                  copy is settled, keep it out of the indexable HTML. */}
              <div className="stat-label">Nested 5-Fold OOS</div>
              <div className="stat-value stat-md stat-green count-target" data-prefix="t=" data-suffix="" data-target="7.86">t=0.00</div>
              <div className="stat-sub">1,070 trades (min t=2.94)</div>
            </div>
            <div>
              <div className="stat-label">Coin Consistency</div>
              <div className="stat-value stat-md stat-bright">22/23</div>
              <div className="stat-sub">Only AAVE negative</div>
            </div>
            <div>
              <div className="stat-label">Live Execution</div>
              <div className="stat-value stat-md stat-yellow animate-pulse">false</div>
              <div className="stat-sub">60d kline lock to 2026-12</div>
            </div>
          </div>

          <p className="case-note">Pre-registered → pure OOS → verdict. Honest about success too. Until real order fills clear the exchange book, we refuse to stamp PASS.</p>
        </article>

      </div>
    </section>
  )
}
