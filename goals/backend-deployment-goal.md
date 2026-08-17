# Goal: Backend Deployment at leads.bentondrones.com

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Current status

The backend IS live and verified on Render at `https://benton-drones-lead-ingest.onrender.com` (healthz 200, signup/admin/exports working, 429 tests green). The custom domain `leads.bentondrones.com` is not yet configured. Per ADR-001, the `onrender.com` subdomain will be disabled after the custom domain is verified, and the admin UI is moving to Cloudflare Pages at `admin.bentondrones.com`.

## Objective

Deploy the Benton Drones Lead-Ingest backend to a secure production host at `leads.bentondrones.com`.

## Required outcomes

- HTTPS enabled (Render auto-issues Let's Encrypt certs for custom domains).
- Custom domain `leads.bentondrones.com` configured in Render (Settings -> Custom Domains).
- CNAME `leads -> benton-drones-lead-ingest.onrender.com` added at the DNS provider.
- Environment variables/secrets configured.
- Admin login works (transitioning to Cloudflare Access per ADR-001).
- Signup submission works.
- Database persistence works (Neon PostgreSQL via DATABASE_URL).
- Exports are protected.
- Logs avoid unnecessary PII.
- Backups or export recovery path documented.
- Health check route exists (`/healthz`).
- Deployment rollback path documented.
- `onrender.com` subdomain disabled after custom domain is verified (per ADR-001).
- SSL/TLS mode Full (strict) at Cloudflare (per ADR-001).

## Required production secrets

- `ADMIN_PASSWORD`
- `ADMIN_SESSION_SECRET`
- `CSRF_SECRET`
- `SHOPIFY_APP_SECRET` when App Proxy is enabled
- `DATABASE_URL` (Neon connection string with `?sslmode=require`)
- geocoder secrets if using external provider
- `SMTP_USER` / `SMTP_PASSWORD` / `NOTIFY_FROM` / `NOTIFY_INTERNAL_TO` when email is enabled

## Architectural context

Per `research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md` (Option B):
- The admin UI is moving to Cloudflare Pages at `admin.bentondrones.com`.
- The Render API at `leads.bentondrones.com` validates the Cloudflare Access JWT server-side.
- The legacy password login is removed once Access + JWT verification are verified.
- The `onrender.com` subdomain is disabled so the origin is reachable only via the custom domain.

## Non-goals

- Public unauthenticated admin/export access
- Production deployment without HTTPS
- Production deployment without backup/recovery notes
- Keeping the shared password login as the primary auth mechanism after Access is verified
