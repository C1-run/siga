// Section: fixed top header

export function Header() {
  return (
    <header className="site-header">
      <div className="brand">
        <span className="brand-name">siga</span>
        <span className="brand-tag">audit-engine // v2.6</span>
      </div>
      <nav className="site-nav">
        <a href="#demo" className="nav-link">demo</a>
        <a href="https://github.com/C1-run/siga" className="nav-link" target="_blank" rel="noopener">github</a>
        <a href="https://c1.run/?panel=scope" className="nav-link">scope a build</a>
      </nav>
      <div className="brand-motto">[ honesty / reproducibility / verdict ]</div>
    </header>
  )
}
