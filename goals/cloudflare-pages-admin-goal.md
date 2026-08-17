# Goal: Cloudflare Pages Admin Dashboard behind Cloudflare Access

> **Architectural decision:** `research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md` (Option B, Proposed)
> **Updated by:** planning-agent-083bcd on 2026-08-17

## Objective

Host the admin dashboard as static assets on Cloudflare Pages at `admin.bentondrones.com`, gated by Cloudflare Access, with the dynamic Python API on Render at `leads.bentondrones.com` validating the Access JWT server-side. Replace the shared password login with identity-based access (Google OAuth / one-time PIN) and make the admin surface non-indexable.

## Autonomy

CODE AUTONOMOUS + HUMAN CONFIGURATION. An agent builds the static admin UI assets, adds JWT verification middleware, CORS, and CSRF protection to the Python API, and writes architecture fitness tests. A human configures Cloudflare Pages, Cloudflare Zero Trust / Access applications, and the identity provider, since those live behind authenticated dashboards.

## Required outcomes (per ADR-001 Option B)

1. **Static admin UI on Cloudflare Pages** at `admin.bentondrones.com` — HTML/CSS/JS shell built from the existing admin dashboard markup; served from Cloudflare's edge with no cold start. Includes `robots.txt` (`User-agent: *` / `Disallow: /`) and a `_headers` file setting `X-Robots-Tag: noindex, nofollow`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`.
2. **Render API backend** at `leads.bentondrones.com` — CNAME to the Render service (orange-cloud proxied). The public signup flow stays on Render unchanged; only the admin UI moves to Pages.
3. **Cloudflare Access gate** — Zero Trust (Free) enabled with a team domain; identity provider is Google OAuth and/or one-time PIN email for Anderson (1–2 admins). Two Access applications: one for `admin.bentondrones.com` (Pages UI), one for `leads.bentondrones.com` (API); same allow-policy; copy each app's AUD tag.
4. **Server-side JWT verification** — the Render Python API fetches the JWKS from the Access certs endpoint, verifies the `Cf-Access-Jwt-Assertion` header signature (RS256) via PyJWT, matches the JWT `kid` to `public_certs[]`, checks `iss`, `aud` (app AUD tag), and `exp`. JWKS refreshed on a short TTL (key rotates ~6 weeks; previous key valid 7 days). Applied to all `/admin/*` API routes; public signup routes remain open.
5. **CORS** — API returns `Access-Control-Allow-Origin: https://admin.bentondrones.com` (never `*`), `Access-Control-Allow-Credentials: true`, and handles OPTIONS preflight.
6. **CSRF protection** — prefer a stateless bearer model (Access JWT or short-lived HMAC token as a bearer header); if a session cookie is required, pair it with a CSRF token + Origin/Referer check on every state-changing request.
7. **Disable the `onrender.com` subdomain** in Render settings so the origin is reachable only via the Cloudflare-fronted custom domain.
8. **Remove the legacy password login** from `/admin-login` once Access + JWT verification are verified end-to-end; keep the public signup flow unchanged.
9. **Audit logging** — rely on Zero Trust Access authentication logs; additionally write an audit row in Neon for every mutating admin action keyed to the JWT `sub`/email claim.
10. **SSL/TLS mode Full (strict)** — Cloudflare zone SSL set to Full (strict); Render presents a valid cert so strict validation passes.

## Non-goals

- Moving the public signup form off Render (it stays on Render).
- Self-hosting the admin UI on Render (defeats the cold-start benefit).
- Hardcoding Access public keys (must fetch JWKS with refresh).
- Wildcard CORS (`*`).
- Keeping the shared password login as the primary auth mechanism after Access is verified.
- SAML/SCIM (paid Access tier; not needed for 1–2 admins).

## Fallback

If the team prefers to avoid CORS/cookie complexity entirely, **Option D** (documented in ADR-001) keeps the monolith on Render with Access in front of the proxied origin and JWT verification server-side — no UI/API split, but the admin shell still cold-starts.
