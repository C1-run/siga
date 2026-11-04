// siga landing — document shell (hono/jsx, server-rendered)

const IMPORTMAP = JSON.stringify({
  imports: {
    three: 'https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js',
    'three/addons/': 'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/',
  },
})

export function Layout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>siga — open-source backtest audit CLI</title>
        <meta
          name="description"
          content="siga is an open-source CLI for chronological trade logs. It judges the final 30% only and reports exact p-values, sample-size limits, and optional cost sensitivity."
        />
        {/* Open Graph / Twitter cards */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://siga.c1.run/" />
        <meta property="og:title" content="siga — open-source backtest audit CLI" />
        <meta
          property="og:description"
          content="Audit chronological trade logs with an out-of-sample-only verdict, exact p-values, and optional cost sensitivity."
        />
        <meta property="og:image" content="https://siga.c1.run/og.png" />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="siga — open-source backtest audit CLI" />
        <meta
          name="twitter:description"
          content="Audit chronological trade logs with an out-of-sample-only verdict, exact p-values, and optional cost sensitivity."
        />
        <meta name="twitter:image" content="https://siga.c1.run/og.png" />
        <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23070a09'/%3E%3Ctext x='16' y='22' font-family='monospace' font-size='18' font-weight='bold' fill='%2300ff94' text-anchor='middle'%3Es%3C/text%3E%3C/svg%3E" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        <link rel="canonical" href="https://siga.c1.run/" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <link rel="stylesheet" href="/css/main.css" />
        {/* The FAQ is a JS accordion: answers are collapsed by CSS and opened by
            main.js. Without JS nothing can open them, so show every answer and
            drop the +/- affordance. */}
        <noscript>
          <style>{`.faq-content{visibility:visible!important;grid-template-rows:1fr!important}.faq-icon{display:none!important}`}</style>
        </noscript>
        <script type="importmap" dangerouslySetInnerHTML={{ __html: IMPORTMAP }} />
        {/* error capture must precede module scripts; powers the ?debug overlay */}
        <script dangerouslySetInnerHTML={{ __html: "window.__diag={errors:[],scene:'pending'};window.addEventListener('error',e=>{window.__diag.errors.push(String(e.message||e.type))},true);window.addEventListener('unhandledrejection',e=>{window.__diag.errors.push('promise: '+String(e.reason))});" }} />
        {/* scene.js is lazy-imported from main.js after first paint (idle callback) */}
        <script type="module" src="/js/main.js"></script>
      </head>
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <canvas aria-hidden="true" id="particle-canvas"></canvas>
        <canvas aria-hidden="true" id="three-canvas" className="three-canvas"></canvas>
        <div aria-hidden="true" id="mesh-blob"></div>
        {children}
      </body>
    </html>
  )
}
