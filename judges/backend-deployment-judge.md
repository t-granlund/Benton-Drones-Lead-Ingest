# Judge: Backend Deployment

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Current status

The backend IS live on Render at `https://benton-drones-lead-ingest.onrender.com` (healthz 200, signup/admin/exports verified, 429 tests green). The custom domain `leads.bentondrones.com` is not yet configured. This judge remains BLOCKED until the custom domain is live and the ADR-001 architecture changes are verified.

## Pass criteria

PASS if:

- `https://leads.bentondrones.com` resolves.
- HTTPS certificate is valid.
- Signup page loads.
- Signup submission persists data.
- Admin login works (via Cloudflare Access per ADR-001, or legacy password until then).
- Admin/export routes are protected.
- Required env vars are configured.
- Logs avoid unnecessary PII.
- Database persistence is confirmed.
- Backup/export recovery path exists.
- Rollback instructions exist.
- `onrender.com` subdomain is disabled after custom domain verification (per ADR-001).
- SSL/TLS mode is Full (strict) at Cloudflare (per ADR-001).

## Fail criteria

FAIL if:

- Site runs only over HTTP.
- Admin/export routes are public.
- Signup fails in production.
- Secrets are committed to repo.
- Production data is stored only ephemerally without documented risk acceptance.
- The `onrender.com` subdomain remains reachable for admin routes after the custom domain is verified.

## Blocked criteria

BLOCKED on the custom domain `leads.bentondrones.com` being configured in Render + DNS CNAME added. The backend is live on the onrender.com subdomain in the meantime.
