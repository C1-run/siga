// Section 8: CTA + FOOTER (typewriter & magnetic button wired in main.js)

const WORDS = [
  ['Which', '80ms'],
  ['chapter', '150ms'],
  ['does', '220ms'],
  ['your', '290ms'],
  ['strategy', '360ms'],
  ['belong', '430ms'],
  ['to?', '500ms'],
]

export function Cta() {
  return (
    <section className="cta" id="cta">
      <div className="cta-inner">
        <div className="cta-kicker">FINAL RECKONING</div>
        <h2 className="cta-title" id="cta-headline">
          {WORDS.map(([word, delay]) => (
            <span className="cta-word-3d" key={word} style={{ transitionDelay: delay }}>{word}{' '}</span>
          ))}
        </h2>
        <p className="cta-sub">Free and open source — install the CLI and audit your own strategy. Star the repo or join the waitlist.</p>
        <div className="cta-actions">
          <a className="magnetic-btn btn-primary btn-lg" href="https://github.com/C1-run/siga" id="cta-submit-btn">
            <span>Star on GitHub →</span>
          </a>
        </div>
        <form className="waitlist-form" id="waitlist-form" action="/api/waitlist" method="POST">
          <input
            type="email"
            name="email"
            placeholder="you@example.com"
            required
            className="waitlist-input"
            aria-label="Email for waitlist"
          />
          <button type="submit" className="magnetic-btn btn-ghost btn-lg">
            <span>Join waitlist</span>
          </button>
        </form>
        <p className="waitlist-msg" id="waitlist-msg" aria-live="polite"></p>

        {/* C1 backflow: the studio behind siga takes scoped builds and signs every step. */}
        <p className="cta-sub" style={{ marginTop: '2.5rem' }}>
          need it built rather than audited? c1 — the studio behind this — scopes the work
          and ships it with a signed receipt you can verify yourself.
        </p>
        <div className="cta-actions" style={{ marginTop: '1.25rem' }}>
          <a className="magnetic-btn btn-ghost btn-lg" href="https://c1.run/?panel=scope">
            <span>Scope a build with C1 →</span>
          </a>
        </div>
        <footer className="site-footer">
          <div>siga — Honesty / Reproducibility / Verdict</div>
          <div className="typewriter">
            <span id="typewriter-text"></span>
            <span className="type-cursor animate-pulse" id="typewriter-cursor"></span>
          </div>
        </footer>
      </div>
    </section>
  )
}
