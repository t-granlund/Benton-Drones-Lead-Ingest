# Changelog

All notable changes to the Benton Drones Lead Ingest system are documented here.
This project follows a build-phase history plus a running release log. Newest
entries appear at the top within each release section.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
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
- `docs/training-guide.html` — updated test counts to 348, refreshed the closing
  checklist to be an Anderson handoff, and pointed readers at the new guides.
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

**348 tests, all passing** — 281 unit/integration, 55 HTTP end-to-end, and 12
real-browser (Playwright) end-to-end.

Run them with:

```bash
make test              # 281 unit/integration
make test-e2e          # 55 HTTP E2E
make test-e2e-browser  # 12 browser E2E (needs Playwright Chromium)
```
