// siga landing — page composition (hono/jsx, server-rendered)

import { Layout } from './layout.jsx'
import { Header } from './sections/header.jsx'
import { Hero } from './sections/hero.jsx'
import { DeathArchive } from './sections/archives.jsx'
import { PainPoints } from './sections/pain-points.jsx'
import { FiveChecks } from './sections/checks.jsx'
import { Matrix } from './sections/matrix.jsx'
import { Demo } from './sections/demo.jsx'
// Pricing section removed — open-source free CLI for now; restore after public release.
import { Faq } from './sections/faq.jsx'
import { Cta } from './sections/cta.jsx'

export function LandingPage() {
  return (
    <Layout>
      <Header />
      <main className="site-main" id="main-content" tabindex="-1">
        <Hero />
        <DeathArchive />
        <PainPoints />
        <FiveChecks />
        <Demo />
        <Matrix />
        <Faq />
        <Cta />
      </main>
    </Layout>
  )
}
