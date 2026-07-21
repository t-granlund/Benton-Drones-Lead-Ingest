# Judge: Read-Only Preflight Scripts

## Pass criteria

PASS if:

- `scripts/check_dns.py` runs.
- `scripts/preflight_report.py` runs.
- `scripts/check_cloudflare_zone.py` runs without write actions.
- Missing env vars produce WARN/INFO, not crashes.
- DNS checks report root, `www`, and `leads`.
- Cloudflare check uses read-only token when available.
- Output uses clear PASS/WARN/FAIL statuses.
- Tests cover script behavior where practical.

## Fail criteria

FAIL if:

- Scripts modify DNS.
- Scripts require secrets for basic local checks.
- Missing env vars crash the tool.
- Output is ambiguous.
- Scripts expose tokens/secrets.
