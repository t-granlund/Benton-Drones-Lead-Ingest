# Benton Drones Lead Ingest — Current State and Next Steps

> **Companion doc:** for the printable, Anderson-facing version of everything below, see
> `docs/anderson-launch-briefing.html` (the live, verified level set).

Last updated: **August 17, 2026** (re-verified live against production; kickoff email sent to Anderson).

## Big picture

We are replacing the current Google Forms + PDFfiller + Google Sheets + manual Google Earth workflow
with a self-owned, Shopify-aware lead ingest backend.

The plan:

- **Shopify** handles storefront and CTA.
- **Owned backend** at `leads.bentondrones.com` handles PII, consent, geocoding, reports, exports.
- **Google Workspace** stays email provider.
- **Render + Neon** host the app and database.

## What is live and verified working (Aug 10, 2026)

| Component | URL | Status |
|---|---|---|
| Signup form | `https://benton-drones-lead-ingest.onrender.com/signup` | Live |
| Admin login / dashboard | `…/admin-login`, `…/admin` | Live |
| Landing page | `…/landing-page.html` | Live |
| Exports (CSV/GeoJSON/KML) | `…/admin/export/*` | Live |
| Health check | `…/healthz` → `{"status":"ok","db":"ok"}` | Live |
| Real geocoding | `GEOCODER_MODE=live` set | Active |
| Persistent rate limiting | built-in | Active |
| JIRA queue replay | built-in | Active (grabs on admin view) |
| Docs site | `https://t-granlund.github.io/Benton-Drones-Lead-Ingest/` | Live |

**Tests:** 402 unit/integration + 57 HTTP E2E verified green locally today (459 total, +12 browser Playwright = 471 with browser). CI gated.

## What is built but not switched on

| Feature | State | One credential needed |
|---|---|---|
| Email notifications | Code done, judge PASS | Google Workspace SMTP app password |
| External uptime monitor + backup evidence | Code+docs done, judge PASS | UptimeRobot (free) + Neon console values |
| Cloudflare Access JWT verification | Code done (`lead_ingest/access_jwt.py`), env-gated | Cloudflare Zero Trust + Access app (post-cutover) → set `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD` |
| JSON admin API + CORS (`/admin/api/*`) | Live, 403 unauthenticated verified | `CORS_ADMIN_ORIGIN=https://admin.bentondrones.com` (post-cutover) |
| pages-admin/ static dashboard | Bundle complete, 7/7 assets serve locally | Cloudflare Pages project (post-cutover) |

## What is not live yet

- Custom domain `leads.bentondrones.com` — needs Cloudflare cutover **then** Render "Add Custom Domain"
- `admin.bentondrones.com` — Cloudflare Pages + Access app (post-cutover)
- Shopify landing-page CTA link to the signup
- Waiver text is real (extracted from the actual consent PDF) but still needs legal review
- Post-launch: G7 Shopify App Proxy, G8 internal map UI

## Kickoff status (2026-08-17)

- **Launch email sent to Anderson** — all live links, the 5-item action list (~2 hrs), Tyler's handle-list, and offline copies of the briefing + nameserver walkthrough attached.
- Anderson is reviewing the **Launch Briefing** (`docs/anderson-launch-briefing.html`) now.
- Mail.app + Mail evidence path verified end-to-end; draft created and sent by Tyler.
- **Anderson's lane:** (1) read briefing, (2) nameserver walkthrough (~60 min, screenshot current DNS first), (3) Workspace SMTP app password, (4) waiver legal review, (5) ask Tyler for admin password by text/call.
- **Tyler's lane** (after cutover): Cloudflare account + Zero Trust config, `leads.bentondrones.com` custom domain on Render, Cloudflare Pages project for `admin.bentondrones.com`, uptime monitor.

## The one remaining human session (~90 min)

1. Google Workspace app password (5–20 min) → email goes live
2. Render env vars (`SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_FROM`, `NOTIFY_INTERNAL_TO`) (5 min)
3. Custom domain: Render add domain + CNAME `leads → benton-drones-lead-ingest.onrender.com` (20 min)
4. UptimeRobot free monitor on `/healthz` (10 min) — also kills free-tier cold start
5. Neon console values → fill recovery playbook placeholders (10 min)
6. Screenshot current Namecheap DNS first (10 min) — rollback safety
7. Waiver legal review (varies)

## Redirects / DNS (exact steps)

1. Render → Settings → Custom Domains → add `leads.bentondrones.com` → copy the target shown
2. DNS provider (Namecheap or Cloudflare — wherever nameservers point): add one record:
   ```
   Type: CNAME   Host: leads   Value: benton-drones-lead-ingest.onrender.com   TTL: Auto
   ```
3. **Do NOT touch existing MX/SPF/DKIM/DMARC records** (keeps email alive)
4. Back in Render: Verify → free HTTPS cert auto-issued → green lock
5. Smoke test: `https://leads.bentondrones.com/healthz` then a signup→dashboard→export run

## Cost

| Scenario | $/month | Effort |
|---|---|---|
| Right now (Free tiers) | $0 | done |
| Polished startup (Render Starter + monitor + domain) | ~$7 | redirect steps only |
| Growth (+ Neon Launch DB) | ~$26 | one env var |

## ADR-001 implementation status (2026-08-17, shipped)

Backend assets **shipped and live-verified** (commit `9937e1d` + `814b2e9`); Cloudflare-side setup remains human-gated:

- **Access JWT verification** — `lead_ingest/access_jwt.py`; activate on Render post-cutover with `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD`, optional `CF_ACCESS_STRICT=1`
- **JSON admin API + CORS** — `/admin/api/summary|leads|lead/<id>|audit` return 403 unauthenticated pre-activation; OPTIONS 204. Set `CORS_ADMIN_ORIGIN=https://admin.bentondrones.com` post-cutover
- **Admin audit trail** — `admin_audit` table recording password logins and Access JWT auths
- **Static Pages dashboard** — `pages-admin/` in repo root, all 7 assets verified locally (index.html, config.js, dashboard.js, Leaflet ×2, robots.txt, _headers); deploy steps in `pages-admin/README.md`
- **noindex headers** — `X-Robots-Tag: noindex, nofollow` live on all admin/export/API routes (verified in production)
- **Bug fix** — `is_admin_authenticated` uses `verify_or_none` (missing JWT previously raised inside the handler)

Historical note (pre-ship planning state, kept for context):

Remaining human-gated: nameserver cutover (Anderson owns it, walkthrough sent), Cloudflare Pages + Zero Trust config, Render env vars, custom `leads` CNAME.

## How to run locally / test

```bash
python scripts/init_db.py
python -m lead_ingest.server
python -m unittest discover -s tests        # 402 unit/integration
make test-e2e                                # 57 HTTP E2E (459 total without browser)
```

## Files to read for more detail

- Level set: `docs/anderson-launch-briefing.html` (companion to this file)
- Completion checklist: `docs/completion-guide.html`
- PRD/UAT: `docs/prd-uat-plan.html`
- Backup recovery: `docs/backup-recovery-playbook.md`
- Domain setup: `docs/domain-dns-cloudflare-preflight.md`
- Shopify plan: `docs/shopify-integration-plan.md`

## Architectural decision: Cloudflare Pages admin dashboard (ADR-001)

On August 17, 2026, an architectural decision was proposed (ADR-001) to host the admin dashboard as static assets on Cloudflare Pages at `admin.bentondrones.com`, gated by Cloudflare Access, with the Render API at `leads.bentondrones.com` validating the Access JWT server-side. This replaces the shared password login with identity-based access (Google OAuth / one-time PIN), makes the admin surface non-indexable, and disables the `onrender.com` subdomain. See `research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md` for the full ADR with STRIDE analysis and fitness functions.

Goals, judges, and tracking CSVs have been updated to reflect this next phase. See `docs/adr-001-tracking-update.md` for a summary of all tracking changes.

> Updated by planning-agent-083bcd on 2026-08-17.
