import { Hono } from 'hono'
import { LandingPage } from './server/page.jsx'
import { recordPageView } from './server/counter.js'

const app = new Hono()

// Home — the whole page is rendered from JSX (hono/jsx); no static index.html.
// Static css/js still fall through to the assets binding first.
app.get('/', (c) => {
  // Counted after the response, so a slow or failing KV write is never user-visible.
  c.executionCtx.waitUntil(recordPageView(c.env, c.req.raw))
  return c.html(<LandingPage />)
})

// Health check
app.get('/api/health', (c) =>
  c.json({ ok: true, service: 'siga-landing', time: new Date().toISOString() })
)

// Waitlist signup — stores one KV key per email (natural dedupe).
// Key: email:<addr>  Value: JSON { ts }. List via: wrangler kv key list --binding WAITLIST
app.post('/api/waitlist', async (c) => {
  const body = await c.req.parseBody()
  const email = String(body.email || '').trim().toLowerCase()

  // Basic email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    return c.json({ ok: false, error: 'invalid_email' }, 400)
  }

  const key = `email:${email}`
  const existing = await c.env.WAITLIST.get(key)
  if (existing) {
    return c.json({ ok: true, message: 'Already on the list.' })
  }

  await c.env.WAITLIST.put(key, JSON.stringify({ ts: Date.now() }))
  console.log(`[waitlist] new signup: ${email}`)

  return c.json({ ok: true, message: 'You are on the list. We will only email when the paid tier ships.' })
})

// Unmatched paths fall through static assets to here
app.notFound((c) => c.text('404 — not found', 404))

export default app
