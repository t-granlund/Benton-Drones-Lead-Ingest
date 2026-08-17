# Changelog

All notable changes to the Benton Drones Lead Ingest system are documented here.
This project follows a build-phase history plus a running release log. Newest
entries appear at the top within each release section.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] — 2026-08-17 launch-readiness snapshot

### Added
- **Cloudflare Access JWT verification** (`lead_ingest/access_jwt.py`) — JWKS fetch
  + iss/aud/exp verification on admin routes, env-gated by `CF_ACCESS_TEAM_DOMAIN`
  and `CF_ACCESS_AUD`, optional `CF_ACCESS_STRICT=1`. Dormant until Cloudflare
  Zero Trust exists (post-cutover). Part of ADR-001.
- **JSON admin API + CORS** (`lead_ingest/admin_api.py`) —
  `/admin/api/summary|leads|lead/<id>|audit`, OPTIONS 204 preflight, origin gate
  via `CORS_ADMIN_ORIGIN`, 403 for unauthenticated API access (verified live).
- **Admin audit trail** — `admin_audit` table records password logins and,
  post-cutover, Cloudflare Access JWT auths.
- **Static Pages admin dashboard** (`pages-admin/`) — self-contained bundle
  (index.html, config.js, dashboard.js, vendored Leaflet, `robots.txt`,
  `_headers` with noindex) ready to deploy as a Cloudflare Pages project at
  `admin.bentondrones.com` once the Cloudflare zone exists. Deploy steps in
  `pages-admin/README.md`.
- **noindex headers** — `X-Robots-Tag: noindex, nofollow, nosniff` + `DENY` +
  `no-referrer` + `no-store` on all admin/export/API routes (verified live).
- **Anderson kickoff** — launch email sent 2026-08-17 with live links, the
  5-item Anderson action list, and offline copies of the briefing + nameserver
  cutover walkthrough attached.

### Fixed
- **`RETURNING *` Postgres insert bug** — signup 502 on the Neon path; audit
  insert now uses `RETURNING *`.
- **Postgres init DDL translation** — deploy crash on first boot fixed in
  `scripts/init_db.py` / `db.py` (SQLite-flavored DDL is translated for Postgres).
- **`is_admin_authenticated` JWT raise** — a missing Access JWT previously raised
  inside the request handler; now uses `verify_or_none`.
- **Briefing walkthrough link** — pointed the launch briefing at the rendered
  GitHub blob view of the markdown walkthrough instead of raw `.md`.

### Changed
- Test posture recounted: **402 unit/integration + 57 HTTP E2E = 459 verified
  green locally** (+12 Playwright browser E2E = 471 with browser).

---

## Earlier additions (pre-2026-08-17)

### Added
- **Real geocoder chain** (`lead_ingest/geocoding.py`) — US Census Geocoder primary
  + Nominatim fallback, results cached in a new `geocode_cache` table, gated by
  `GEOCODER_MODE` (`mock` default for offline/dev, `live` for real lookups).
  `scripts/backfill_geocode.py` backfills existing signups (dry-run by default).
  Judge JUDGE-GEO-001 PASS.
- **Persistent rate limiting** (`lead_ingest/request_security.py`) —
  token-bucket-in-DB (`rate_limit_buckets` table) with atomic compare-and-set,
  per-route-class limits (signup 5/min, admin-login 30/min, public 60/min, all
  env-overridable), 429 responses now send `Retry-After`, and storage failures
  fall back to a loud conservative in-memory limiter. Judge JUDGE-RATELIMIT-001 PASS.
- **JIRA queue replay worker** (`lead_ingest/jira_replay.py`) — on-read sweep
  (signup path + admin dashboard) plus an optional daemon, exponential backoff
  with jitter, dead-letter after 5 attempts, and idempotency keys that prevent
  duplicate tickets after ambiguous timeouts. `scripts/replay_jira_queue.py` for
  manual sweeps. Judge JUDGE-JIRA-002 PASS.
- **Email notifications** (`lead_ingest/notify.py`) — stdlib `smtplib` sender,
  DB-backed `email_queue` with backoff + dead-letter, customer confirmation and
  internal alert templates, enqueued inside the signup transaction so a signup
  never partially fails. Live-send activates with `SMTP_USER` + `SMTP_PASSWORD`
  (Google Workspace app password); degrades gracefully without them.
- **Backup & monitoring tooling** — DB-aware `/healthz` (bare `SELECT 1`, no DDL
  on the health path), strictly read-only `scripts/verify_backup.py` (SQLite
  `mode=ro`, Postgres read-only session), and `docs/backup-recovery-playbook.md`
  with restore procedures and human placeholders for Neon/monitor evidence.
- **Visual before & after architecture page** (`docs/architecture-before-after.html`) —
  fully visual, hand-rolled SVG panels comparing the old manual workflow
  (Google Forms → PDFfiller → Sheets → manual Google Earth) against the new
  self-owned Render + Neon pipeline. No code, no markdown, no ASCII.
- **Anderson's plain-language guide** (`docs/friend-guide.html`, rewritten) — a
  no-code walkthrough written for a technical-but-non-programmer owner, with
  workshop analogies, a visual three-box system diagram, a 5-minute live-app
  tryout, and an optional local run.
- This `CHANGELOG.md`.

### Changed
- All status surfaces synced to the post-wiggum-loop state: in-app pages
  (`/changelog`, `/roadmap`, `/goals`, `/judges`, `/current-state`, `/prd`,
  `/completion-guide`, `/overview`) and static docs (training guide, explainer,
  architecture diagram, friend guide, completion/PRD twins) now show the real
  geocoder, persistent rate limiting, JIRA replay, email queue, and backup
  tooling as built, with 429 test counts.
- `index.html` — links to the live app's roadmap and completion guide pages.
- `docs/training-guide.html` — new email-notifications and backups sections,
  JIRA replay worker docs, new data-model tables, updated geocoder FAQ.
- `docs/explainer-guide.html` — replaced the ASCII architecture diagram with a
  fully visual SVG; updated test counts.
- `docs/architecture-diagram.html` — cross-linked the before/after page and the
  Anderson guide in the diagram intro and footer.
- `index.html` — surfaced the before/after page and relabeled the friend guide
  as Anderson's guide.

---

## Build & release history

### Feature — Playwright browser-automation E2E suite
- 12 real-Chromium E2E tests (`tests/e2e/browser_test_e2e_journey.py`) covering
  public pages, signup form rendering/validation/honeypot, admin login,
  dashboard, lead detail, print view, and CSV/GeoJSON/KML export reachability.
- Shared `tests/e2e/browser_base.py` with local ephemeral server (default) or
  live-URL targeting via `E2E_BASE_URL` / `E2E_ADMIN_PASSWORD`.
- New Makefile targets `test-e2e-browser` (local) and `test-e2e-live` (remote).
- CI installs Chromium and gates the browser suite on a count of ≥12, shown in
  the GitHub Actions summary alongside the unit (281) and HTTP E2E (55) gates.

### Feature — CI with test-count gates
- `.github/workflows/ci.yml`: setup-python 3.11, pip cache keyed on
  `requirements.txt`, then `make test`, `make test-e2e`, and
  `make test-e2e-browser` — each with a count gate so a deleted test fails CI.

### Fix — Postgres compatibility
- Auto-migrate older `signups` tables by adding missing columns on startup.
- Cast text `created_at` to `timestamptz` in the Postgres weekly-analytics query.

### Feature — Hosted deployment (Render + Neon)
- `Dockerfile`, `render.yaml` blueprint, and `railway.json` for hosting.
- Neon PostgreSQL via `DATABASE_URL` with automatic SQLite fallback locally.
- Live app at https://benton-drones-lead-ingest.onrender.com

### Feature — Waiver, signature, and audit trail
- Real aerial-services waiver text extracted from the provided PDF.
- Typed-name signature capture with a full consent/signature audit trail.

### Feature — Production hardening
- Security headers, weak-secret rejection in production, POST body-size limits,
  and a documented production-readiness review.

---

## Test posture

**471 tests, all passing** — 402 unit/integration, 57 HTTP end-to-end, and 12
real-browser (Playwright) end-to-end (459 non-browser verified locally on
2026-08-17).

Run them with:

```bash
make test              # 402 unit/integration
make test-e2e          # 57 HTTP E2E
make test-e2e-browser  # 12 browser E2E (needs Playwright Chromium)
```
