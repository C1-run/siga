// Self-hosted page counter: one KV namespace, two append-only key shapes, no third-party beacon.
//
//   hit:<YYYY-MM-DD>:<uuid>      one key per page view
//   visitor:<YYYY-MM-DD>:<hash>  one key per visitor per day
//
// Both are writes only. KV has no atomic increment, and a running total is the one shape that
// cannot survive without one — three requests spaced 0.3s apart across the edge read the same
// empty slot and each wrote `1`. So a view gets a fresh uuid, because two edges must not be able
// to overwrite each other, and a visitor gets a deterministic hash, because that is exactly why
// repeat visits collapse into one key.
//
// A raw IP never reaches KV: the key holds SHA-256(ip|day|SALT), truncated. The salt is there
// because the IPv4 space is small enough that an unsalted hash of one is a lookup table, not a
// digest.
//
// Read the day by counting keys — nothing here is exposed over HTTP, traffic stays private. A key
// written a moment ago can lag before it appears in a list read from elsewhere, so these are
// "so far today", not a live ticker:
//
//   P=$(date -u +%F)
//   wrangler kv key list --binding SIGA_STATS --prefix "hit:$P:"     --remote | grep -c '"name"'
//   wrangler kv key list --binding SIGA_STATS --prefix "visitor:$P:" --remote | grep -c '"name"'
//
// Both keys expire after 40 days, so any day inside that window can still be recounted.

const SALT = 'siga-landing-v1'
const DAY_SECONDS = 86_400
const KEEP_DAYS = 40

/**
 * Count one page view. A counter that breaks must not take the page down, so nothing here is
 * allowed to throw.
 */
export async function recordPageView(env, req) {
  try {
    const ip = req.headers.get('CF-Connecting-IP')
    if (!ip) {
      // Without Cloudflare's header every visitor would collapse into one bucket, which is a
      // worse lie than not counting. Only reachable outside production.
      return { counted: false, reason: 'no_client_ip' }
    }

    const day = new Date().toISOString().slice(0, 10)
    const bytes = await crypto.subtle.digest(
      'SHA-256',
      new TextEncoder().encode(`${ip}|${day}|${SALT}`),
    )
    const hash = [...new Uint8Array(bytes)]
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')
      .slice(0, 16)

    const ttl = { expirationTtl: KEEP_DAYS * DAY_SECONDS }
    await Promise.all([
      env.SIGA_STATS.put(`hit:${day}:${crypto.randomUUID()}`, '1', ttl),
      env.SIGA_STATS.put(`visitor:${day}:${hash}`, '1', ttl),
    ])
    return { counted: true, day }
  } catch (error) {
    return { counted: false, reason: `kv_error: ${error.message}` }
  }
}
