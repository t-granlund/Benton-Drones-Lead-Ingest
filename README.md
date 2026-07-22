# Benton Drones Lead Ingest

Local-first Shopify-aware MVP for replacing Google Forms + PDFfiller + Sheets + manual Google Earth planning.

Repository: https://github.com/t-granlund/Benton-Drones-Lead-Ingest  
GitHub Pages: https://t-granlund.github.io/Benton-Drones-Lead-Ingest/  
Live app (Render + Neon): https://benton-drones-lead-ingest.onrender.com  
Friend setup guide: https://t-granlund.github.io/Benton-Drones-Lead-Ingest/docs/friend-guide.html  
Hosting options: see [`docs/hosting-guide.md`](docs/hosting-guide.md)

## What it is

A Python stdlib + SQLite lead-ingest application that captures signups, consent, and waivers for Benton Drones aerial services. No Node, no npm, no external services required — just Python 3.11+. The hosted production instance runs on Render with a Neon PostgreSQL database.

Features:

- Public signup page at `/signup` with variant support (`/signup/<variant>`)
- Standalone branded landing page at `/landing-page.html`
- Consent capture with version/text/timestamp/audit metadata
- Admin dashboard at `/admin` with analytics, lead map, and exports (CSV, GeoJSON, KML)
- PDF / print view of completed consent forms at `/admin/lead/<id>/print` and `/admin/lead/<id>/pdf`
- JIRA ticket creation per signup (or local queue if JIRA is not configured)
- Shopify context capture for future Shopify page/theme/app-proxy integration
- CSRF protection, honeypot, rate limiting, and admin session auth
- Fully stdlib Python — zero required pip dependencies

## Quick start

For the full friend-facing walkthrough (clone to a Mac, run locally, and use the hosted Render app), see [`docs/friend-guide.html`](docs/friend-guide.html).

```bash
git clone https://github.com/t-granlund/Benton-Drones-Lead-Ingest.git
cd Benton-Drones-Lead-Ingest
make init-db
ADMIN_PASSWORD=change-me make run
```

Then open:

- `http://127.0.0.1:8000/` — root redirect to training guide
- `http://127.0.0.1:8000/landing-page.html` — standalone branded landing page
- `http://127.0.0.1:8000/signup` — public signup form
- `http://127.0.0.1:8000/admin-login` — admin login
- `http://127.0.0.1:8000/admin` — admin dashboard
- `http://127.0.0.1:8000/overview` — system overview

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ADMIN_PASSWORD` | Yes (to use admin) | Password for admin login |
| `ADMIN_SESSION_SECRET` | Recommended | Secret for signing session cookies (falls back to `ADMIN_PASSWORD`) |
| `CSRF_SECRET` | Recommended | Secret for CSRF tokens (falls back to session/admin secret) |
| `SHOPIFY_APP_SECRET` | No | Shopify app secret for HMAC validation |
| `JIRA_BASE_URL` | No | JIRA Cloud base URL (e.g. `https://your-domain.atlassian.net`) |
| `JIRA_USER_EMAIL` | No | JIRA user email for API auth |
| `JIRA_API_TOKEN` | No | JIRA API token |
| `JIRA_PROJECT_KEY` | No | JIRA project key (e.g. `BDS`) |
| `JIRA_ISSUE_TYPE` | No | Issue type name (default: `Task`) |

If JIRA env vars are not set, signups are queued in `jira_queue` for later processing.

## Features

### Signup & consent
- Public form with variant support and Shopify context capture
- Consent + waiver text stored with version, timestamp, IP, and user agent
- Typed-name electronic signature with disclaimer

### Admin dashboard
- Analytics: total leads, today, this week, pending geocodes
- Lead map (Leaflet + OpenStreetMap)
- Breakdowns by source, campaign, and variant
- CSV, GeoJSON, and KML exports
- Lead detail pages with consent, signature, and geocode info

### PDF / Print export
- `/admin/lead/<id>/print` — browser-printable HTML view (no deps)
- `/admin/lead/<id>/pdf` — true PDF download if `fpdf2` is installed (falls back to print view)

### JIRA integration
- Creates a JIRA ticket per signup when config is present
- Queues signups locally in `jira_queue` when JIRA is unavailable
- Uses only Python stdlib (`urllib.request`, `json`)

### Landing page
- Standalone `static/landing-page.html` with Benton branding
- Hero, benefit cards, how-it-works, and CTA to `/signup`
- Single flat file — no build step

## Testing

```bash
make test               # python -m unittest discover -s tests (281 tests)
make test-e2e           # python -m unittest discover -s tests/e2e -t tests/e2e (55 tests)
make test-all           # both suites in sequence (336 tests)
```

Tests use in-memory or temp databases — no `data/` directory needed.

Optional dependencies for tests:

```bash
make install            # pip install -r requirements.txt (installs fpdf2)
```

## Deploy to Railway

The app ships with a `Dockerfile` and `railway.json` for one-click deployment to Railway. Railway handles HTTPS, health checks, and persistent volumes for SQLite.

Quick summary:

1. Sign up at <https://railway.com> with GitHub.
2. Deploy from the `t-granlund/Benton-Drones-Lead-Ingest` repo.
3. Add environment variables (`ADMIN_PASSWORD`, `ADMIN_SESSION_SECRET`, `CSRF_SECRET`, `COOKIE_SECURE=1`, `ENV=production`).
4. Mount a volume at `/app/data` for SQLite persistence.
5. Railway builds from the Dockerfile and gives you a public URL.

For the full step-by-step guide, environment variable reference, post-deployment checklist, Fly.io alternative, and Neon migration notes, see [`docs/railway-deployment-guide.md`](docs/railway-deployment-guide.md).

To test the Docker image locally:

```bash
docker build -t benton-drones .
docker run -p 8000:8000 -e ADMIN_PASSWORD=your-password benton-drones
```

## Deploy to Render

The repo ships with a `render.yaml` Blueprint for one-click deployment to Render. Render handles HTTPS, health checks, and Docker builds. Pair it with a Neon PostgreSQL database (set `DATABASE_URL`) -- no persistent disk is needed because the database lives in Neon.

The live instance is already running at:

```txt
https://benton-drones-lead-ingest.onrender.com
```

Quick summary for a fresh deploy:

1. Sign up at <https://render.com> with GitHub.
2. Create a new Blueprint service from the `t-granlund/Benton-Drones-Lead-Ingest` repo.
3. Render reads `render.yaml` and builds the Docker image automatically.
4. Set environment variables in the Render dashboard (`ADMIN_PASSWORD`, `ADMIN_SESSION_SECRET`, `CSRF_SECRET`, `COOKIE_SECURE=1`, `ENV=production`, `DATABASE_URL`).
5. No persistent disk needed -- the database lives in Neon.

For the full step-by-step guide, environment variable reference, Neon setup, and verification steps, see [`docs/render-deployment-guide.md`](docs/render-deployment-guide.md).

## Production path

1. Set `ADMIN_PASSWORD`, `ADMIN_SESSION_SECRET`, `CSRF_SECRET` to strong values.
2. Set `SHOPIFY_APP_SECRET` if using Shopify app proxy.
3. Set JIRA env vars if using JIRA ticket creation.
4. Install `fpdf2` for true PDF export: `pip install fpdf2`.
5. Deploy to Railway (see above) or behind HTTPS with a reverse proxy (nginx, Caddy, etc.).
6. See `docs/shopify-integration-plan.md` for Shopify integration options.
7. See `docs/current-state-and-next-steps.md` for the full roadmap.

## Contributing

1. Fork the repo.
2. Create a feature branch.
3. Run `make test-all` and ensure all 336 tests pass.
4. Keep the core app stdlib-only — no new required pip dependencies.
5. Optional deps go in `requirements.txt` and `pyproject.toml` under `[project.optional-dependencies]`.
6. Submit a pull request.

## Review pages

- `/overview` — what exists and how the system works
- `/shopify-preview` — easiest launch path: Shopify page CTA to owned signup
- `/changelog` — what has been built
- `/roadmap` — what remains before/after production launch
- `/domain-setup` — Namecheap, Cloudflare, Google Workspace, Shopify setup plan
- `/api-preflight` — API keys, CLI tools, and safe automation checks needed
- `/goals` — end-to-end implementation goal stack
- `/judges` — acceptance criteria and evidence requirements
- `/current-state` — one-page “what is built / what is next / what is blocked” summary

## Notes

This MVP intentionally uses Python stdlib + SQLite so it runs locally without Node/npm or external services. It can later be evolved into a Shopify app proxy / hosted app backend with PostgreSQL/PostGIS when the hosting/runtime environment is ready.

The existing Shopify storefront should act as the presentation layer. The owned lead ingest backend should remain the system of record for lead PII, consent, geocoding, exports, maps, and planning data. See `docs/shopify-integration-plan.md`.
