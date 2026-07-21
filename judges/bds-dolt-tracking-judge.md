# Judge: BDS/Dolt-Style Tracking

## Pass criteria

PASS if:

- Requirements are tracked with stable IDs.
- Tasks are tracked with owner/status/priority.
- Judges are mapped to goals.
- Evidence is recorded for tests, QA, DNS checks, and deployments.
- Status changes are append-only or auditable.
- Decisions are recorded with rationale.
- Platform snapshots are stored without secrets.
- Tracking files can be reviewed in git diffs and imported into Dolt later.

## Fail criteria

FAIL if:

- Work status is only in chat history.
- Evidence is missing for PASS claims.
- Decisions are not traceable.
- Secrets appear in tracking files.
- Goal/judge/task relationships are unclear.
