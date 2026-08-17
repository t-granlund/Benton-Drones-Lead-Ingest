# Goal: Production Hardening

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Objective

Make the system safe for real lead capture and operations.

## Required outcomes

- HTTPS enforced.
- Secure cookies in production.
- Admin/export routes protected.
- CSRF protection enabled.
- Signup spam protection enabled.
- Rate limiting or abuse throttling enabled.
- Consent text/version stored immutably.
- PII not logged unnecessarily.
- Server-side validation enforced.
- Backups documented.
- Recovery process documented.
- Security-sensitive env vars not committed.
- Shopify HMAC/signature validation enabled before trusting App Proxy context.
- Geocoding provider abstracted and cached.
- Production monitoring/log review path documented.

## ADR-001 hardening additions (per `research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md`)

- Admin authentication transitions from shared password to Cloudflare Access (Google OAuth / one-time PIN, MFA-capable).
- Render API verifies the `Cf-Access-Jwt-Assertion` JWT server-side (PyJWT + JWKS fetch, `iss`/`aud`/`exp` checks, key rotation refresh).
- Admin surface is non-indexable: `X-Robots-Tag: noindex` via Pages `_headers` + `robots.txt` Disallow.
- CORS is scoped to `https://admin.bentondrones.com` (never `*`), `Allow-Credentials: true`.
- CSRF protection on state-changing API requests (bearer model or token + Origin/Referer check).
- The `onrender.com` subdomain is disabled (origin reachable only via the Cloudflare-fronted custom domain).
- Legacy password login removed after Access + JWT verification are confirmed end-to-end.
- Audit row written in Neon for every mutating admin action keyed to the JWT `sub`/email claim.

## Non-goals

- Claiming production readiness while major security gaps remain
- Keeping the shared password login as the primary auth mechanism after Access is verified
- Hardcoding Access public keys (must fetch JWKS with refresh)
- Wildcard CORS
