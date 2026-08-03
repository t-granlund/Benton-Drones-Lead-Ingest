# Judge: Backups and Uptime Monitoring

## Pass criteria

PASS if, with evidence attached in `tracking/evidence.csv`:

1. `/healthz` (or equivalent) returns 200 when app+DB are healthy and non-200 when the DB is unreachable, covered by test.
2. The recovery playbook exists in `docs/` and contains concrete restore steps (point-in-time recovery, branch restore, app re-pointing) that name actual Neon console locations.
3. The backup verification script runs read-only against the production database and reports reachability plus table counts (script output attached as evidence).
4. The uptime monitor configuration is documented: target URL, check interval, alert destination mailbox.
5. Neon backup/retention settings are recorded in the playbook with a human-captured console screenshot or export attached as evidence.
6. Test suite passes including the health-endpoint and playbook-docs tests.

## Fail criteria

FAIL if:

- The playbook says "restore from backup" without executable steps
- The health endpoint returns 200 while the database is down
- The monitor target is an authenticated route (external monitors cannot reach it)
- Any write operation exists in the verification script

## Blocked criteria

BLOCKED (for criteria 4-5 evidence only) until the human completes the Neon console check and creates the external monitor account. Code-side criteria (1, 3, 6) must PASS autonomously first.
