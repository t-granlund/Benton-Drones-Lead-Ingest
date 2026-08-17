# Cloudflare Pages Admin Dashboard (ADR-001)

Static admin UI served from Cloudflare Pages at `admin.bentondrones.com`,
gated by **Cloudflare Access** (Google OAuth / one-time PIN — no shared
password). Talks to the Render API at `leads.bentondrones.com`.

## Layout

| File | Purpose |
|---|---|
| `index.html` | Dashboard shell (metrics, map, leads table, exports, audit log) |
| `js/dashboard.js` | Fetch logic — `credentials: "include"` so the Access cookie flows |
| `config.js` | Deploy-time API origin (`ADMIN_API_BASE`) |
| `_headers` | `X-Robots-Tag: noindex` + security headers (Pages-native) |
| `robots.txt` | `Disallow: /` for crawlers that honor it |
| `static/leaflet/` | Vendored Leaflet copies (sync from `static/leaflet/` when it updates) |

## Deploy steps (after nameserver cutover — see `docs/anderson-nameserver-cutover-walkthrough.md`)

1. **Cloudflare Pages:** Dash → Workers & Pages → Create → Pages → Connect to Git
   → repo `t-granlund/Benton-Drones-Lead-Ingest` → build settings:
   framework preset **None**, build command: *(empty)*, output directory: `pages-admin`.
2. **Custom domain:** Pages project → Custom domains → add `admin.bentondrones.com`
   (same-zone, so DNS + cert are automatic). Keep proxied (orange).
3. **Access (Zero Trust Free):** create applications:
   - `admin.bentondrones.com` (and `*.pages.dev` deploy host for previews)
   - `leads.bentondrones.com`
   IdP: Google or one-time PIN; policy: allow Anderson's email(s).
   In each app's **CORS settings**: allow origin `https://admin.bentondrones.com`,
   allow credentials, allow headers `Cf-Access-Jwt-Assertion, Content-Type`.
4. **Render env vars** (the API backend):
   ```
   CF_ACCESS_TEAM_DOMAIN=<yourteam>          # e.g. bentondrones
   CF_ACCESS_AUD=<aud tag of leads.bentondrones.com Access app>
   CORS_ADMIN_ORIGIN=https://admin.bentondrones.com
   # later, once verified end-to-end:
   CF_ACCESS_STRICT=1
   ```
5. **config.js:** already points at `https://leads.bentondrones.com`.
   For pre-cutover testing point it (and `CORS_ADMIN_ORIGIN`) at matching
   temporary origins; never mix origins.
6. **Verify (per `judges/cloudflare-pages-admin-judge.md`):**
   - Unauthenticated visit → Access login (302) or 403
   - `X-Robots-Tag: noindex` on responses; `robots.txt` Disallow: /
   - API rejects requests without valid JWT (401/403)
   - Dashboard loads metrics/map/leads; exports open in new tab
   - Access log shows `access_jwt_auth` rows keyed to the admin's email

## Auth flow summary

Browser → Pages (Access checks cookie, else login) → JS fetch with
`credentials: "include"` → leads.bentondrones.com (Access edge validates
cookie via its own app; injects `Cf-Access-Jwt-Assertion`) → Render backend
verifies the JWT cryptographically (`lead_ingest/access_jwt.py`) → JSON.

Defense in depth: even if the edge is bypassed (e.g. onrender subdomain left
enabled — disable it in Render settings), the backend still rejects requests
without a valid JWT.
