# Goal: Backups and Uptime Monitoring

## Primary goal

Ensure the production lead database is backed up and the production service is monitored for downtime, with a written recovery playbook so a failure is an inconvenience, not a data-loss event.

## Autonomy

CODE AUTONOMOUS + HUMAN CREDENTIAL. An agent writes the backup verification script, recovery playbook, and monitor configuration. A human performs the Neon console settings check and creates the external monitor account, since both live behind authenticated dashboards.

## Required capabilities

1. Neon native backups: documented configuration of Neon's branch/point-in-time-recovery settings for the production database, with retention expectations recorded in the playbook.
2. Recovery playbook (`docs/`): step-by-step restore procedure covering point-in-time recovery, branch restore, and how to point the app at a restored database, written so a non-author can follow it.
3. Backup verification script: a read-only check that confirms the production database is reachable and reports table counts, suitable for spotting a broken/empty restore target before it matters.
4. External uptime monitor: configuration-as-documentation for a free-tier external monitor (e.g. UptimeRobot/BetterStack free tier) hitting a public health endpoint at a defined interval with alert email to the operator.
5. Health endpoint: a lightweight unauthenticated `/healthz` (or equivalent) returning 200 only when the app and database are both reachable, suitable as the monitor target.
6. Alert routing: downtime alerts go to the operator's Google Workspace mailbox; the destination address is documented in the playbook.
7. Tests: unit test for the health endpoint's healthy/unhealthy behavior (including simulated DB failure) and a docs test asserting the playbook file exists and names the restore steps.

## Non-goals

- Self-hosted backup infrastructure or off-Neon dump shipping
- Multi-region failover or hot standby
- Status page for customers
- SLA/SLO definitions and on-call rotation
