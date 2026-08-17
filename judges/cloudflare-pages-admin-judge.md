# Judge: Cloudflare Pages Admin Dashboard behind Cloudflare Access

> **Architectural decision:** `research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md` (Option B)
> **Updated by:** planning-agent-083bcd on 2026-08-17
>
> **Readiness update (2026-08-17, post-ship):** all agent-buildable prerequisites
> are DONE and live-verified: `pages-admin/` static bundle (7/7 assets serve),
> Access JWT verification code (`lead_ingest/access_jwt.py`, env-gated), JSON
> admin API + CORS (`/admin/api/*`, 403 unauthenticated, OPTIONS 204),
> `admin_audit` table, and `X-Robots-Tag: noindex` on all admin/export/API routes
> (verified in production). What remains is the Cloudflare-side setup: Pages
> project, Zero Trust + Access applications, and the custom domains — all gated
> on Anderson's nameserver cutover. Evidence: `EVID-API-001`, `EVID-QA-005`.

## Pass criteria

PASS if, with evidence attached in `tracking/evidence.csv`:

1. `admin.bentondrones.com` serves the static admin UI from Cloudflare Pages with HTTP 200.
2. `admin.bentondrones.com` responses include `X-Robots-Tag: noindex, nofollow`.
3. `admin.bentondrones.com/robots.txt` returns 200 with `Disallow: /`.
4. An unauthenticated request to `admin.bentondrones.com` is redirected to Cloudflare Access login (302 to `cloudflareaccess.com`) or returns 403.
5. The Render API at `leads.bentondrones.com` rejects requests to `/admin/*` routes that lack a valid `Cf-Access-Jwt-Assertion` header (401/403).
6. The Render API rejects requests with a tampered/invalid JWT (401/403).
7. CORS on the API returns `Access-Control-Allow-Origin: https://admin.bentondrones.com` (never `*`) and `Access-Control-Allow-Credentials: true` on preflight.
8. The `onrender.com` subdomain is disabled (direct requests to `https://benton-drones-lead-ingest.onrender.com/admin` return 404).
9. The legacy `/admin-login` password flow no longer grants access (returns 401/403/404).
10. Cloudflare zone SSL/TLS mode is set to Full (strict).
11. JWT verification checks `iss`, `aud` (app AUD tag), and `exp`; JWKS is fetched (not hardcoded) with refresh on key rotation.
12. Public signup routes (`/signup`, `/healthz`) remain open and functional without a JWT.

## Fail criteria

FAIL if:

- The admin UI is reachable without Cloudflare Access authentication.
- The API returns PII on `/admin/*` without a valid Access JWT.
- CORS allows wildcard origins (`*`).
- The `onrender.com` subdomain is still reachable for admin routes after verification.
- The legacy password login still grants admin access after Access is verified.
- JWT public keys are hardcoded instead of fetched from the JWKS endpoint.
- The admin surface is indexable (no `X-Robots-Tag` or `robots.txt`).
- Public signup is broken by the JWT middleware.

## Blocked criteria

BLOCKED if the human has not yet configured Cloudflare Zero Trust / Access applications and the identity provider. The static admin UI assets, JWT verification code, CORS, and CSRF can be built and unit-tested autonomously before that; the end-to-end verification is human-gated.

## Evidence

- Architecture fitness test results (tests/architecture/test_admin_architecture.py per ADR-001)
- Cloudflare Access application configuration screenshots (no secrets)
- Cloudflare Pages deployment URL and headers verification
- Render API JWT rejection test output
- DNS resolution of `admin.bentondrones.com` and `leads.bentondrones.com`
