# Goal: Read-Only Preflight Scripts

## Objective

Provide safe CLI checks for DNS, Cloudflare, email auth, and production readiness without making changes.

## Required scripts

- `scripts/check_dns.py`
- `scripts/check_cloudflare_zone.py`
- `scripts/preflight_report.py`
- future: `scripts/check_email_auth.py`
- future: `scripts/check_namecheap_snapshot.py`

## Required behavior

- Read-only only.
- No DNS edits.
- No nameserver changes.
- No record deletion.
- Output clear PASS/WARN/FAIL statuses.
- Work locally without secrets where possible.
- Use Cloudflare token only for read-only inventory.

## Required env vars

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ZONE_ID`

## Non-goals

- Automated DNS writes
- Automated nameserver cutover
- Automated MX changes
