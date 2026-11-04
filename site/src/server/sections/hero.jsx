// Section 1: HERO (100vh 3D scene)
// IDs/classes here are wired to main.js + scene.js — do not rename.

export function Hero() {
  return (
    <section className="hero" id="hero">
      <div className="hero-meta">
        <span className="dot dot-sm dot-green animate-pulse"></span>
        <span>AUDIT REPORT SUITE — INDEPENDENT VERIFICATION</span>
      </div>

      <div className="hero-main">
        <h1 className="hero-title" id="hero-title">
          <span className="hero-line" id="hero-l1">
            <span className="hero-3d-word" style={{ transitionDelay: '80ms' }}>Your</span>{' '}
            <span className="hero-3d-word" style={{ transitionDelay: '160ms' }}>backtest</span>{' '}
            <span className="hero-3d-word" style={{ transitionDelay: '240ms' }}>is</span>{' '}
            <span className="hero-3d-word" style={{ transitionDelay: '320ms' }}>lying</span>{' '}
            <span className="hero-3d-word" style={{ transitionDelay: '400ms' }}>to</span>{' '}
            <span className="hero-3d-word" style={{ transitionDelay: '480ms' }}>you.</span>
          </span>
          <span className="hero-line hero-line-2" id="hero-l2" style={{ transitionDelay: '580ms' }}>
            <span>We make it{' '}</span>
            <span className="confess">
              confess.<span className="hero-underline" id="hero-underline"></span>
            </span>
          </span>
        </h1>

        <p className="hero-sub" id="hero-sub">Strategy audit. Not signals. Not hope. Verdict.</p>

        <div className="chip-row">
          <div className="verdict-chip-3d glass-card chip chip-pass" style={{ transitionDelay: '850ms' }}>
            <span className="dot dot-green"></span>
            <span className="chip-label">PASS</span>
            <span className="chip-sub">n ≥ 30 · p &lt; 0.05 · OOS only</span>
          </div>
          <div className="verdict-chip-3d glass-card chip chip-fail" style={{ transitionDelay: '1000ms' }}>
            <span className="dot dot-red"></span>
            <span className="chip-label">FAIL</span>
            <span className="chip-sub">OOS significant &amp; negative</span>
          </div>
          <div className="verdict-chip-3d glass-card chip chip-inc" style={{ transitionDelay: '1150ms' }}>
            <span className="dot dot-yellow"></span>
            <span className="chip-label">INCONCLUSIVE</span>
            <span className="chip-sub">n &lt; 30 or p ≥ 0.05</span>
          </div>
        </div>
      </div>

      <div className="hero-foot" id="scroll-hint">
        <div className="hero-foot-left">
          <div className="pulse-line scale-y-line" id="hero-pulse-line"></div>
          <span className="hero-foot-label">scroll to audit</span>
        </div>
        <div className="hero-foot-right">[ 4 DEATHS — 1 SURVIVOR ]</div>
      </div>
    </section>
  )
}
