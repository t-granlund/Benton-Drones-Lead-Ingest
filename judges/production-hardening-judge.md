# Judge: Production Hardening

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Pass criteria

PASS if:

- HTTPS is enforced.
- Secure cookies are enabled in production.
- CSRF is enabled for forms.
- Signup spam protection exists.
- Rate limiting or abuse throttling exists.
- Admin/export routes require auth.
- Consent text/version/timestamp are stored.
- Server-side validation rejects invalid data.
- Shopify HMAC/signature validation is enabled before App Proxy production use.
- PII is not unnecessarily logged.
- Backup/recovery path is documented.
- Secrets are environment-managed.

## ADR-001 additional criteria (per `research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md`)

- Admin authentication uses Cloudflare Access (not shared password) after verification.
- Render API validates the `Cf-Access-Jwt-Assertion` JWT server-side (PyJWT + JWKS, `iss`/`aud`/`exp`).
- Admin surface is non-indexable (`X-Robots-Tag: noindex` + `robots.txt` Disallow).
- CORS is scoped to `https://admin.bentondrones.com` (never `*`).
- The `onrender.com` subdomain is disabled.
- Legacy password login is removed after Access + JWT verification are confirmed.
- Audit rows are written for mutating admin actions keyed to the JWT `sub`/email.

## Fail criteria

FAIL if:

- Public exports expose PII.
- Consent can be bypassed.
- Invalid signups are accepted.
- Production trusts unsigned Shopify context.
- HTTPS is missing.
- Secrets are committed.
- CORS allows wildcard origins.
- The admin surface is indexable.
- Public signup is broken by JWT middleware.
