# Wiggum Loop Report

## Iteration 1

### What was inspected

- `/goals/lead-ingest-local-mvp.md`
- `/judges/local-mvp-judge.md`
- `/docs/workflow-modernization-plan.md`
- `/docs/shopify-integration-plan.md`
- `/README.md`
- Current repo structure
- Existing local Python/SQLite implementation
- Existing tests

### Gaps found

The local MVP already supported signup, consent, SQLite persistence, admin dashboard, exports, clustering, and Shopify context capture. The highest-value gap was Shopify app proxy signature/HMAC validation. The judge explicitly fails production trust of Shopify context without validation.

### Changes made

Added `lead_ingest/shopify_security.py` with:

- canonical Shopify-style query message generation
- HMAC-SHA256 calculation
- constant-time HMAC/signature verification
- Shopify context extraction
- signed Shopify context token creation
- signed context token verification

Updated `lead_ingest/server.py` so:

- local unsigned Shopify-style demo URLs still work when `SHOPIFY_APP_SECRET` is not set
- production-style mode can set `SHOPIFY_APP_SECRET`
- when a secret is set, Shopify context query params require valid HMAC/signature before being carried into the form
- verified Shopify context is handed from GET to POST using a signed hidden context token
- tampered Shopify context token submissions are rejected

Updated docs:

- `README.md`
- `docs/shopify-integration-plan.md`
- `goals/lead-ingest-local-mvp.md`

### Tests added or changed

Added `tests/test_shopify_security.py` covering:

- canonical message generation
- valid HMAC verification
- invalid HMAC rejection
- missing secret rejection
- Shopify context extraction
- signed context token round trip
- tampered context token rejection

### Test run results

Command run three consecutive times:

```bash
python -m unittest discover -s tests
```

Results:

```txt
Ran 21 tests in 0.003s
OK

Ran 21 tests in 0.003s
OK

Ran 21 tests in 0.003s
OK
```

Database initialization verified:

```bash
python scripts/init_db.py
```

Result:

```txt
Initialized database at data\lead_ingest.sqlite3
```

Server startup verified with bounded process check:

```powershell
$p = Start-Process -FilePath python -ArgumentList '-m','lead_ingest.server' -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2
Stop-Process -Id $p.Id
```

Result:

```txt
server started and stopped cleanly
```

### Judge status

PASS for the current local Shopify-aware MVP judge.

### Remaining gaps

These are production hardening gaps, not local MVP blockers:

- Admin authentication is not implemented.
- Export route protection is not implemented.
- HTTPS deployment is not configured.
- Rate limiting and bot protection are not implemented.
- Real geocoding provider integration is not implemented.
- Shopify app installation/app proxy configuration is not completed.
- Exact Shopify app proxy canonicalization should be verified against current Shopify docs before launch.

### Recommended next iteration task

Implement local admin/export protection using a simple environment-based admin password and signed session cookie, then add tests for unauthorized and authorized access.

## Iteration 2

### What was inspected

- `lead_ingest/server.py`
- `tests/test_server.py`
- `README.md`
- Prior Wiggum loop report

### Gaps found

Admin and export routes were publicly accessible. This exposed sensitive lead data and exports in local/prototype mode and was a production-readiness blocker.

### Changes made

Added `lead_ingest/auth.py` with:

- environment-password authentication helper
- signed admin session token creation
- signed admin session token verification
- session expiration checks
- cookie parsing
- login cookie generation
- logout cookie expiration

Updated `lead_ingest/server.py` so:

- `/admin-login` renders an admin password form
- `POST /admin-login` authenticates against `ADMIN_PASSWORD`
- successful login sets a signed `bd_admin_session` cookie
- `/admin` redirects unauthenticated requests to `/admin-login`
- `/export/csv`, `/export/geojson`, and `/export/kml` return `403` unless authenticated
- `/admin-logout` clears the admin cookie
- HTTP logs can be silenced in tests with `QUIET_HTTP_LOGS=1`

Updated `README.md` with required admin environment variables:

```bash
ADMIN_PASSWORD=change-me
ADMIN_SESSION_SECRET=change-me-too
```

### Tests added or changed

Added `tests/test_auth.py` covering:

- password authentication requires configured password
- matching password succeeds
- signed session token round trip
- tampered session token rejection
- expired session token rejection
- cookie parsing
- expired cookie generation

Added `tests/test_protected_routes.py` covering actual HTTP behavior:

- unauthenticated `/admin` is blocked
- authenticated `/admin` is allowed
- unauthenticated exports are blocked for CSV, GeoJSON, and KML
- authenticated exports are allowed for CSV, GeoJSON, and KML
- tampered session cookie is rejected for admin and exports

### Test run results

Command run three consecutive times:

```bash
python -m unittest discover -s tests
```

Results:

```txt
Ran 33 tests in 0.595s
OK

Ran 33 tests in 0.700s
OK

Ran 33 tests in 0.677s
OK
```

Database initialization verified:

```bash
python scripts/init_db.py
```

Result:

```txt
Initialized database at data\\lead_ingest.sqlite3
```

Server startup verified with admin auth environment variables:

```powershell
$env:ADMIN_PASSWORD='test-password'
$env:ADMIN_SESSION_SECRET='test-secret'
$p = Start-Process -FilePath python -ArgumentList '-m','lead_ingest.server' -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2
Stop-Process -Id $p.Id
```

Result:

```txt
server started and stopped cleanly with admin auth env
```

### Judge status

PASS for the requested admin/export protection increment.

### Remaining gaps

- HTTPS deployment is not configured.
- Rate limiting and bot protection are not implemented.
- CSRF protection for admin login should be added before production.
- Secure cookie flag should be enabled behind HTTPS in production.
- Real geocoding provider integration is not implemented.
- Shopify app installation/app proxy configuration is not completed.

### Recommended next iteration task

Add lightweight CSRF protection for admin login and signup POSTs, plus a basic honeypot/rate-limit strategy for public signup spam resistance.

## Iteration 3

### What was inspected

- `lead_ingest/server.py`
- `lead_ingest/auth.py`
- `tests/test_protected_routes.py`
- `README.md`
- Prior Wiggum loop report
- Current repo structure

### Gaps found

The app had admin/export protection but still lacked CSRF protection for POST routes and public signup spam resistance. The project also needed a local HTML overview that clearly explains what has been built and what remains on the roadmap for a technology-proficient non-developer audience.

### Changes made

Added `lead_ingest/request_security.py` with:

- stateless signed CSRF token creation
- CSRF token verification
- token action binding
- token expiration checks
- a small in-memory rate limiter

Updated `lead_ingest/server.py` so:

- `/signup` POST requires a valid CSRF token
- `/admin-login` POST requires a valid CSRF token
- public signup includes a hidden honeypot field named `website_url`
- signup submissions with the honeypot filled are rejected
- `/signup` and `/admin-login` POSTs are rate-limited per client/path
- `/overview` serves a local HTML overview app

Added `lead_ingest/overview.py` with a detailed local HTML overview page explaining:

- executive summary
- system flow
- local routes
- what is built
- Shopify fit
- security model
- current local setup
- roadmap
- production risks
- plain-English bottom line

Updated `README.md` with:

- `/overview` route
- `CSRF_SECRET` environment variable
- CSRF/honeypot/rate-limit notes

### Tests added or changed

Added `tests/test_request_security.py` covering:

- CSRF token round trip
- wrong-action rejection
- tampered token rejection
- expired token rejection
- rate limiter allow/deny behavior
- rate limiter window reset

Updated `tests/test_protected_routes.py` so route tests now:

- fetch CSRF tokens from forms before POSTing
- verify missing admin-login CSRF is rejected
- verify missing signup CSRF is rejected
- verify signup honeypot submission is rejected
- verify `/overview` is available
- continue verifying admin/export protection

### Test run results

Command run three consecutive times:

```bash
python -m unittest discover -s tests
```

Results:

```txt
Ran 43 tests in 0.774s
OK

Ran 43 tests in 0.912s
OK

Ran 43 tests in 0.842s
OK
```

Database initialization verified:

```bash
python scripts/init_db.py
```

Result:

```txt
Initialized database at data\\lead_ingest.sqlite3
```

Server smoke check verified:

```txt
/overview
/signup
/admin-login
```

Result:

```txt
server smoke check passed: /overview /signup /admin-login
```

File line-count check verified all `lead_ingest/*.py` files are under 600 lines. Largest file is `server.py` at 329 lines.

### Judge status

PASS for the CSRF, honeypot, rate-limit, and local overview MVP increment.

### Remaining gaps

- HTTPS deployment is not configured.
- Secure cookie flag should be enabled behind HTTPS in production.
- Real geocoding provider integration is not implemented.
- Shopify app installation/app proxy configuration is not completed.
- Exact Shopify app proxy canonicalization should be verified against current Shopify docs before launch.
- Rate limiting is in-memory and should be replaced with shared storage for multi-process/cloud deployments.
- A richer map UI is still planned.

### Recommended next iteration task

Choose the production integration path: Shopify app proxy vs hosted signup link vs embedded theme section. Then implement the selected deployment adapter and production environment checklist.

## Iteration 4

### What was inspected

- `lead_ingest/server.py`
- `lead_ingest/overview.py`
- `README.md`
- Current routes and test suite
- Available QA agents

### Goal

Build around the easiest path to success: a Shopify landing page that links to an owned hosted signup experience. Add local MVP review pages for changelog and roadmap, test end-to-end, and open the local app in the browser.

### Changes made

Added `lead_ingest/project_pages.py` with:

- `/shopify-preview` page showing the recommended Shopify landing page + CTA flow
- `/changelog` page summarizing MVP build history
- `/roadmap` page explaining remaining implementation phases

Updated `lead_ingest/server.py` with routes:

- `/shopify-preview`
- `/changelog`
- `/roadmap`

Updated `lead_ingest/overview.py` to link to the new review pages.

Updated `README.md` with the new review URLs.

### Tests added or changed

Updated `tests/test_protected_routes.py` to verify:

- `/overview` loads
- `/shopify-preview` loads
- `/changelog` loads
- `/roadmap` loads
- the Shopify preview CTA points to the signup flow
- E2E flow: Shopify preview -> signup -> valid submission -> admin login -> admin sees signup -> authenticated CSV export contains signup

### Test run results

Command run three consecutive times:

```bash
python -m unittest discover -s tests
```

Results:

```txt
Ran 44 tests in 1.084s
OK

Ran 44 tests in 1.183s
OK

Ran 44 tests in 1.063s
OK
```

Database initialization verified:

```bash
python scripts/init_db.py
```

Result:

```txt
Initialized database at data\\lead_ingest.sqlite3
```

HTTP E2E page smoke check verified:

- `/overview`
- `/shopify-preview`
- `/changelog`
- `/roadmap`
- `/signup`
- `/admin-login`

Result:

```txt
local HTTP E2E page smoke check passed
```

### Browser status

Started the local server in the background with:

```txt
ADMIN_PASSWORD=local-admin
ADMIN_SESSION_SECRET=local-session-secret
CSRF_SECRET=local-csrf-secret
```

Opened:

```txt
http://127.0.0.1:8000/overview
```

QA Kitten browser automation was attempted but blocked because Playwright browser binaries were not installed locally.

### Judge status

PASS for the easiest-path local MVP review build.

### Remaining gaps

- Deploy to HTTPS host such as `leads.bentondrones.com`.
- Create the real Shopify landing page in Shopify admin.
- Style the signup page to fully match the Benton Drones Shopify theme.
- Add real geocoding provider and caching policy.
- Decide when/if to prototype Shopify App Proxy.
- Install Playwright browser binaries if browser automation QA is required.

## Iteration 5

### What was inspected

- Current repo assets and docs
- Existing local review pages
- Domain/DNS requirements from user context
- Available agents/tools

### Goal

Plan the domain/DNS setup for `bentondrones.com` using Namecheap, Cloudflare, Google Workspace, Shopify, and the new `leads.bentondrones.com` backend subdomain. Add local/documented preflight checks and make the plan viewable in the MVP.

### Changes made

Added `docs/domain-dns-cloudflare-preflight.md` covering:

- recommended DNS ownership model
- Namecheap as registrar
- Cloudflare as authoritative DNS
- Google Workspace email preservation
- Shopify storefront records
- `leads.bentondrones.com` setup
- optional future subdomains
- DNS record templates
- MX/SPF/DKIM/DMARC checklist
- Cloudflare cutover steps
- rollback plan
- verification commands
- Shopify/backend alignment

Added `docs/design-system-preflight.md` documenting the need to collect current Shopify visual assets:

- logo
- favicon
- colors
- fonts
- buttons/forms
- header/footer screenshots
- copy/tone examples

Updated `lead_ingest/project_pages.py` with `/domain-setup` local page explaining the domain plan in plain English.

Updated `lead_ingest/server.py` with `/domain-setup` route.

Updated `lead_ingest/overview.py`, `README.md`, and tests to include the new page.

### Tests

Command run three consecutive times:

```bash
python -m unittest discover -s tests
```

Results:

```txt
Ran 44 tests in 1.011s
OK

Ran 44 tests in 1.080s
OK

Ran 44 tests in 1.086s
OK
```

### Local browser/server status

Stopped stale local server processes, restarted one clean server, verified:

```txt
/overview -> 200
/domain-setup -> 200
/shopify-preview -> 200
/roadmap -> 200
```

Opened:

```txt
http://127.0.0.1:8000/domain-setup
```

### Judge status

PASS for the DNS/domain/design-preflight planning increment.

### Remaining gaps

- Need actual Cloudflare account UI access to add/verify zone records.
- Need screenshots/exports of current Namecheap DNS and nameservers.
- Need Google Workspace MX/DKIM/SPF confirmation from Google Admin.
- Need Shopify Admin domain requirements and theme/design assets.
- Need production hosting target for `leads.bentondrones.com` before final DNS record can be created.

## Iteration 6

### Goal

Fix browser automation readiness and add safe backend command-line preflight scripts so the platform setup can move from manual checks toward CLI/API validation.

### Changes made

Installed Python Playwright Chromium browser binaries:

```bash
python -m playwright install chromium
```

Added read-only setup scripts:

- `scripts/check_dns.py`
- `scripts/check_cloudflare_zone.py`
- `scripts/preflight_report.py`
- `scripts/__init__.py`

Added tests:

- `tests/test_scripts.py`

Updated `README.md` with script usage.

### Script verification

Ran:

```bash
python scripts/check_dns.py
```

Result summary:

```txt
[PASS] bentondrones.com: 23.227.38.65
[PASS] www.bentondrones.com: 23.227.38.74, 2620:127:f00f:e::
[WARN] leads.bentondrones.com: not resolving yet
```

Ran:

```bash
python scripts/preflight_report.py
```

Result summary:

```txt
bentondrones.com resolves
www.bentondrones.com resolves
leads.bentondrones.com is not resolving yet
Cloudflare/API/env secrets are not set yet
```

Ran:

```bash
python scripts/check_cloudflare_zone.py
```

Result:

```txt
[WARN] CLOUDFLARE_API_TOKEN is not set. Create a read-only token first.
```

### Test run results

Command run three consecutive times:

```bash
python -m unittest discover -s tests
```

Results:

```txt
Ran 48 tests in 1.154s
OK

Ran 48 tests in 1.073s
OK

Ran 48 tests in 1.053s
OK
```

### Browser QA

After installing Chromium, QA Kitten browser automation was rerun successfully.

Browser QA result:

```txt
PASS
```

QA verified:

- `/overview`
- `/shopify-preview`
- `/changelog`
- `/roadmap`
- `/domain-setup`
- `/api-preflight`
- `/signup`
- `/admin-login`
- Shopify preview CTA links to signup
- Admin login works with `local-admin`

### Current known live DNS observation

Read-only DNS checks currently show:

```txt
bentondrones.com -> 23.227.38.65
www.bentondrones.com -> 23.227.38.74 / IPv6 Shopify edge
leads.bentondrones.com -> not resolving yet
```

This strongly suggests the current root/www setup is Shopify-related, but Shopify Admin should still be used as source of truth before DNS migration.

### Judge status

PASS for browser automation readiness and CLI/API preflight foundation.

### Remaining next steps

- Create Cloudflare read-only API token.
- Capture Cloudflare Zone ID.
- Run `python scripts/check_cloudflare_zone.py` with token.
- Capture Namecheap DNS/nameserver screenshots.
- Confirm Google Workspace MX/SPF/DKIM/DMARC.
- Confirm Shopify domain requirements.
- Choose production backend host for `leads.bentondrones.com`.

## Iteration 7

### Goal

Establish a durable `/goals` and `/judges` requirements system and BDS/Dolt-ready tracking layer so agents can coordinate end-to-end implementation with clear status, evidence, and acceptance criteria.

### Agent coordination

Planning Agent was invoked to design the goal/judge/tracking structure. Its recommendations were implemented into the repo.

QA Kitten was invoked after implementation to browser-smoke the new local cockpit routes.

### Dolt status

Dolt CLI is not installed on this machine:

```txt
'dolt' is not recognized as an internal or external command
```

So the implementation uses Dolt-ready CSV tables under `tracking/`. These can be imported into Dolt later.

### Files added

Goals:

- `goals/README.md`
- `goals/domain-dns-cloudflare-goal.md`
- `goals/namecheap-preflight-goal.md`
- `goals/google-workspace-email-auth-goal.md`
- `goals/shopify-landing-page-goal.md`
- `goals/shopify-app-proxy-future-goal.md`
- `goals/backend-deployment-goal.md`
- `goals/design-system-capture-goal.md`
- `goals/production-hardening-goal.md`
- `goals/browser-qa-goal.md`
- `goals/readonly-preflight-scripts-goal.md`
- `goals/bds-dolt-tracking-goal.md`

Judges:

- `judges/README.md`
- `judges/domain-dns-cloudflare-judge.md`
- `judges/namecheap-preflight-judge.md`
- `judges/google-workspace-email-auth-judge.md`
- `judges/shopify-landing-page-judge.md`
- `judges/shopify-app-proxy-future-judge.md`
- `judges/backend-deployment-judge.md`
- `judges/design-system-capture-judge.md`
- `judges/production-hardening-judge.md`
- `judges/browser-qa-judge.md`
- `judges/readonly-preflight-scripts-judge.md`
- `judges/bds-dolt-tracking-judge.md`

Tracking:

- `tracking/README.md`
- `tracking/requirements.csv`
- `tracking/tasks.csv`
- `tracking/judges.csv`
- `tracking/evidence.csv`
- `tracking/decisions.csv`
- `tracking/platform_snapshots.csv`
- `tracking/status_log.csv`

Tests:

- `tests/test_goals_judges_tracking.py`

### Local cockpit routes added

- `/goals`
- `/judges`

### Validation

Unit tests:

```txt
Ran 52 tests in 1.167s - OK
Ran 52 tests in 1.135s - OK
Ran 52 tests in 1.127s - OK
```

Routes verified locally:

```txt
/goals -> 200
/judges -> 200
```

QA Kitten result:

```txt
PASS
```

QA verified:

- `/overview` includes Goals and Judges links
- `/goals` loads and shows goal stack
- `/judges` loads and shows judge stack/evidence guidance
- `/goals` to `/judges` navigation works
- `/judges` to `/goals` navigation works
- `/api-preflight` still loads

### Judge status

PASS for requirements/tracking implementation.

### Remaining next steps

- Install Dolt if true Dolt DB tracking is required locally.
- Import `tracking/*.csv` into Dolt once installed.
- Continue filling platform snapshots for Namecheap, Google Workspace, Shopify, and Cloudflare.
- Select production backend host.

## Iteration 8

### Goal

Use agents to complete true local Dolt-backed BDS tracking instead of only Dolt-ready CSVs.

### Agent coordination

Planning Agent was invoked before installation to identify Dolt/Windows gotchas and after implementation to review the final BDS/Dolt setup.

### Dolt installation

Initial Winget install was attempted:

```powershell
winget install --id DoltHub.Dolt -e --accept-package-agreements --accept-source-agreements
```

It was cancelled by the Windows installer flow:

```txt
Installer failed with exit code: 1602
```

Fallback used a portable Dolt release from GitHub:

```txt
Dolt version: 2.1.10
Platform: windows-amd64
Install path: .tools/dolt/dolt-windows-amd64/bin/dolt.exe
```

Added gitignore entries:

```txt
.tools/
.dolt/
```

### Scripts added

- `scripts/dolt.ps1` wraps the repo-local Dolt binary.
- `scripts/sync_tracking_to_dolt.ps1` re-imports CSV tracking tables into Dolt.
- `scripts/check_dolt_tracking.ps1` checks Dolt table existence, row-count drift, primary key presence, and clean Dolt status.

### Dolt initialization and imports

Initialized Dolt and imported tracking CSVs with primary keys:

- `requirements` from `tracking/requirements.csv`
- `tasks` from `tracking/tasks.csv`
- `judges` from `tracking/judges.csv`
- `evidence` from `tracking/evidence.csv`
- `decisions` from `tracking/decisions.csv`
- `platform_snapshots` from `tracking/platform_snapshots.csv`
- `status_log` from `tracking/status_log.csv`

Dolt commits created:

```txt
6c6mrqtreba2b3o5i6qm7k974i1b8mk2 Initialize Benton Drones lead ingest tracking tables
ef2rbj486r8tonrcrvscehssg1806ns9 Record Dolt tracking activation evidence
```

### Dolt verification

Dolt status:

```txt
On branch main
nothing to commit, working tree clean
```

Dolt table counts:

```txt
requirements: 12
tasks: 9
judges: 12
evidence: 7
decisions: 5
platform_snapshots: 7
status_log: 6
```

Drift check:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_dolt_tracking.ps1
```

Result:

```txt
[PASS] requirements: 12 rows match CSV
[PASS] tasks: 9 rows match CSV
[PASS] judges: 12 rows match CSV
[PASS] evidence: 7 rows match CSV
[PASS] decisions: 5 rows match CSV
[PASS] platform_snapshots: 7 rows match CSV
[PASS] status_log: 6 rows match CSV
[PASS] Dolt tracking check complete
```

### Test hardening

Expanded `tests/test_goals_judges_tracking.py` to validate:

- primary key presence
- primary key uniqueness
- requirement references from tasks/judges
- evidence references from judges/status log
- allowed status/result enums
- CSV parseability
- no obvious committed secrets

### Test results

Command run three consecutive times:

```bash
python -m unittest discover -s tests
```

Results:

```txt
Ran 56 tests in 1.184s
OK

Ran 56 tests in 0.837s
OK

Ran 56 tests in 0.967s
OK
```

### Source-of-truth decision

For now:

```txt
tracking/*.csv = canonical human-reviewable source/export layer
.dolt/ = local query/audit mirror generated from CSV
```

### Judge status

PASS for local Dolt-backed BDS tracking.

### Remaining next steps

- Add timestamps to tracking rows for stronger audit quality.
- Optionally add SHA256 checksum for the downloaded Dolt zip.
- Decide later whether a Dolt remote is needed.
- Continue platform snapshots for Namecheap, Google Workspace, Shopify, and Cloudflare.

## Iteration 9

### Goal

Clean up documentation and local cockpit so it is immediately clear what is built, what is next, and what is blocked.

### Changes made

Created:

```txt
docs/current-state-and-next-steps.md
```

Added local cockpit route:

```txt
/current-state
```

Updated:

```txt
README.md
lead_ingest/overview.py
lead_ingest/project_pages.py
lead_ingest/server.py
tracking/README.md
tracking/requirements.csv
tracking/tasks.csv
tracking/evidence.csv
tracking/status_log.csv
tests/test_protected_routes.py
```

`/overview` now links prominently to `/current-state`.

`/current-state` page shows:

- Built
- Ready to go
- Blocked / waiting
- Not built yet
- Recommended next steps

Added BDS tracking for the documentation work:

```txt
REQ-DOC-001
TASK-DOC-001
EVID-DOC-001
LOG-007
```

### Verification

Browser QA:

```txt
PASS
```

QA Kitten verified:

- `/current-state` loads
- `/overview` has a prominent link to `/current-state`
- `/goals` still loads
- `/judges` still loads
- `/current-state` shows all four status sections

Tests:

```txt
Ran 56 tests in 0.899s OK
Ran 56 tests in 1.053s OK
Ran 56 tests in 0.758s OK
```

Dolt drift check:

```txt
[PASS] requirements: 13 rows match CSV
[PASS] tasks: 10 rows match CSV
[PASS] judges: 12 rows match CSV
[PASS] evidence: 8 rows match CSV
[PASS] decisions: 5 rows match CSV
[PASS] platform_snapshots: 7 rows match CSV
[PASS] status_log: 7 rows match CSV
[PASS] Dolt tracking check complete
```

### Dolt commit

```txt
commit gtangdjb9i4r59e3qmar3s22seo50sad
Add REQ-DOC-001 and TASK-DOC-001 for current-state documentation
```

### Remaining next steps

Same as before, but now clearly documented in:

```txt
docs/current-state-and-next-steps.md
http://127.0.0.1:8000/current-state
```
