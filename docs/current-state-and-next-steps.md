# Benton Drones Lead Ingest — Current State and Next Steps

This is the single source of truth for “what is built, what is next, and what is blocked.”

Last updated: during Iteration 8.

## Big picture

We are replacing the current Google Forms + PDFfiller + Google Sheets + manual Google Earth workflow with a self-owned, Shopify-aware lead ingest backend.

The plan:

- **Shopify** handles storefront and CTA.
- **Owned backend** at `leads.bentondrones.com` handles PII, consent, geocoding, clustering, reports, exports.
- **Cloudflare** will become authoritative DNS.
- **Namecheap** stays registrar for now.
- **Google Workspace** stays email provider.

## What is built

### Local MVP (`/overview`)

- Public signup form at `/signup` and `/signup/<variant>`.
- Consent capture with version/text/timestamp/audit metadata.
- SQLite backend for leads and consent.
- Admin login and dashboard at `/admin-login` and `/admin`.
- Protected CSV, GeoJSON, and KML exports.
- Basic proximity clustering utilities.
- CSRF, honeypot, and in-memory rate limiting.
- Shopify context capture and HMAC/signature validation utilities for future App Proxy.
- Works with only Python stdlib + SQLite.

### Shopify awareness (`/shopify-preview`)

- Clear recommended launch path: Shopify page CTA → owned signup at `leads.bentondrones.com`.
- Local preview of how that page/flow feels.
- Decision documented: first launch uses CTA link, not full App Proxy.
- App Proxy is planned for later with required signature validation.

### Documentation and planning

- `/domain-setup` explains DNS migration plan.
- `/api-preflight` explains safe CLI/API automation.
- `/goals` lists implementation goals.
- `/judges` lists acceptance criteria.
- `docs/workflow-modernization-plan.md`
- `docs/shopify-integration-plan.md`
- `docs/design-system-preflight.md`
- `docs/domain-dns-cloudflare-preflight.md`
- `docs/manual-platform-setup-walkthrough.md`
- `docs/wiggum-loop-report.md`

### BDS / Dolt tracking

- CSV tracking tables in `tracking/`.
- Dolt portable install under `.tools/`.
- `.dolt/` initialized, tables imported, two commits created.
- `scripts/dolt.ps1` helper.
- `scripts/sync_tracking_to_dolt.ps1` to re-import.
- `scripts/check_dolt_tracking.ps1` drift check.
- Current policy: CSV files are canonical; Dolt is the local audit mirror.

### Preflight scripts

- `scripts/check_dns.py`
- `scripts/preflight_report.py`
- `scripts/check_cloudflare_zone.py`

These are read-only and safe to run anytime.

### Tests

- 56 tests covering validation, DB, auth, exports, clustering, security, protected routes, scripts, and BDS tracking integrity.
- Tests pass 3 consecutive times.

## What is partially built / ready to go

| Area | Status | Notes |
|---|---:|---|
| Browser automation | Ready | Playwright Chromium installed; QA Kitten can run smoke reviews. |
| Read-only DNS checks | Ready | `check_dns.py` and `preflight_report.py` run. Cloudflare check waits on token. |
| BDS tracking | Ready | CSV and Dolt are in sync. |
| Shopify landing page CTA | Ready to implement | Need access to Shopify Admin to create/edit page. |

## What is blocked or waiting on external info

| Area | Blocker | What is needed |
|---|---:|---|
| Cloudflare DNS automation | `CLOUDFLARE_API_TOKEN` | Create a read-only Cloudflare API token scoped to `bentondrones.com`. |
| Namecheap preflight | Manual login/screenshots | Current nameservers and DNS records from Namecheap. |
| Google Workspace email auth | Manual login/confirmation | MX/SPF/DKIM/DMARC records from Google Admin. |
| Shopify domain/settings | Manual login/confirmation | Required A/CNAME records and myshopify domain. |
| Shopify landing page CTA | Manual login/design | Create page in Shopify Admin and link to `leads.bentondrones.com`. |
| Backend deployment | Custom domain | Render + Neon is live; `leads.bentondrones.com` custom domain is pending. |

## What is not built yet

- Custom domain `leads.bentondrones.com`.
- Cloudflare DNS cutover for the custom domain.
- Production Postgres/PostGIS database.
- Real geocoding provider integration.
- Map UI for internal planning.
- Shopify App Proxy production integration.
- Email/SMS notifications.
- Design system applied to backend pages from Shopify storefront.
- Persistent/shared rate limiting.
- Backup/monitoring/logging playbook.

## Recommended next steps

1. **Custom domain on Render**
   - Add `leads.bentondrones.com` as a custom domain in the Render dashboard.
   - Create the DNS record in Cloudflare.
   - Preserve Google Workspace MX/SPF/DKIM/DMARC records.

2. **Capture current platform state**
   - Namecheap nameservers and DNS records.
   - Google Workspace MX/SPF/DKIM/DMARC.
   - Shopify A/CNAME requirements and myshopify domain.

3. **Create Cloudflare read-only API token**
   - Scope to `bentondrones.com`.
   - Permissions: Zone read, DNS read.
   - Run `python scripts/check_cloudflare_zone.py`.

4. **Create Shopify landing page**
   - Add CTA to `https://leads.bentondrones.com/signup/default?source=shopify&campaign=drone-delivery-page`.
   - Keep PII/consent out of Shopify metafields.

5. **Migrate DNS to Cloudflare**
   - Only after steps 1–4 are complete and verified.
   - Add `leads.bentondrones.com` record pointing to Render.
   - Preserve Google Workspace MX/SPF/DKIM/DMARC.

6. **Smoke test the custom domain**
   - Test signup, admin login, exports, and JIRA against `leads.bentondrones.com`.

7. **Capture design system**
   - Pull logo/colors/fonts/screenshots from Shopify.
   - Apply to signup/admin pages.

8. **Decide on Dolt remote**
   - For now, CSV is canonical and Dolt is local-only.
   - If multiple agents or machines start editing tracking, consider a private Dolt remote.

## How to run the local app

```bash
python scripts/init_db.py
python -m lead_ingest.server
```

Then open:

```txt
http://127.0.0.1:8000/current-state
http://127.0.0.1:8000/overview
http://127.0.0.1:8000/goals
http://127.0.0.1:8000/judges
http://127.0.0.1:8000/signup
http://127.0.0.1:8000/admin-login
```

## How to run tests

```bash
python -m unittest discover -s tests
```

## How to check Dolt tracking

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_dolt_tracking.ps1
```

## Files to read for more detail

- Project overview: `docs/workflow-modernization-plan.md`
- Wiggum loop history: `docs/wiggum-loop-report.md`
- Domain setup: `docs/domain-dns-cloudflare-preflight.md` and `docs/manual-platform-setup-walkthrough.md`
- Shopify plan: `docs/shopify-integration-plan.md`
- API/CLI preflight: `docs/api-cli-automation-preflight.md`
- Goals: `goals/README.md`
- Judges: `judges/README.md`
- Tracking: `tracking/README.md`
