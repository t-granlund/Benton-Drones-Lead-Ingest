# E2E Test Suite — Lead-Ingest

Autonomous end-to-end tests for Lead-Ingest. Two layers:

1. **HTTP E2E** — black-box HTTP tests against a real instance of the stdlib
   server on an ephemeral port. Each class gets its own isolated temp SQLite
   database (no shared state, no network, no production credentials).
2. **Browser E2E** — real Chromium automation via Playwright. Also runs against
   a local ephemeral server by default; can target a live URL with
   `E2E_BASE_URL=https://...` and `E2E_ADMIN_PASSWORD=...`.

## Run

```bash
# HTTP E2E suite (55 tests, ~6s)
make test-e2e

# Browser E2E suite (12 tests, ~15s); requires Playwright Chromium
make test-e2e-browser

# Unit/integration + HTTP E2E
make test-all        # 336 tests

# Everything including browser E2E (run after `make install`)
make test-all && make test-e2e-browser   # 348 tests
```

## What it covers

### HTTP E2E (55 tests)

| Area | Coverage | File |
|---|---|---|
| Public GET pages (15) | 15/15 | `test_e2e_public_pages.py` |
| `/healthz` | 4/4 | `test_e2e_health.py` |
| `POST /signup` (happy + validation + honeypot + CSRF) | 13/13 | `test_e2e_signup_flow.py` |
| Admin auth (`/admin-login`, `/admin`, `/admin-logout`) | 10/10 | `test_e2e_admin_auth.py` |
| Admin dashboard, lead detail, print, pdf, geojson | 7/7 | `test_e2e_admin_dashboard.py` |
| Exports (csv/geojson/kml, auth 403 vs 200) | 5/5 | `test_e2e_exports.py` |
| Security (headers, 413, 429, traversal, prod gate) | 9/9 | `test_e2e_security.py` |
| CLI `scripts/init_db.py` | 2/2 | `test_e2e_cli.py` |
| Full signup→login→admin→export journey | 1/1 | `test_e2e_signup_flow.py` |

### Browser E2E (12 tests)

| Area | Coverage | File |
|---|---|---|
| Public pages (`/`, `/healthz`, `/landing-page.html`, project pages) | 4 tests | `browser_test_e2e_journey.py` |
| Signup form rendering, validation, honeypot | 3 tests | `browser_test_e2e_journey.py` |
| Admin login, dashboard, lead detail, print/PDF | 5 tests | `browser_test_e2e_journey.py` |

## Files

- `e2e_base.py` — shared `E2ETestBase` fixture + helpers (not a test module).
- `test_e2e_*.py` — HTTP E2E test modules.
- `browser_base.py` — shared `BrowserTestBase` with local or remote target support.
- `browser_test_*.py` — browser-automation E2E test modules.

## CI

`.github/workflows/ci.yml` runs `make test`, `make test-e2e`, and
`make test-e2e-browser` with count gates (281 / 55 / 12 minimums).

## Idempotency

Re-running on an unchanged codebase produces zero changes to the test files and
the same 55/55 pass result. Features removed in future are marked `skip`, never
deleted.
