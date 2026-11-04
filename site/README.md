# SIGA landing page

This Cloudflare Worker serves the server-rendered landing page at `siga.c1.run`.
The production Worker uses the `SIGA_STATS` and `WAITLIST` KV namespaces and
serves files from `public/` before routing unmatched requests to Hono.

Deploy from this directory with `npm install` followed by `npm run deploy`.
The SEO endpoints live in `public/robots.txt` and `public/sitemap.xml`.
