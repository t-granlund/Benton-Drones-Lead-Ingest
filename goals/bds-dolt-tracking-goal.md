# Goal: BDS/Dolt-Style Tracking

## Objective

Track implementation, decisions, verification evidence, and status changes in a structured, auditable way compatible with Dolt/versioned data workflows.

## Required outcomes

- Each requirement has a stable ID.
- Each goal has a stable file.
- Each judge has a stable ID and file.
- Each task has status, owner, evidence, and next action.
- Changes are auditable in git and importable into Dolt later.
- Decision history is preserved.
- Test/QA runs are recorded with commands and results.
- DNS/platform snapshots are tracked before and after changes.
- No secrets are stored in tracking files.

## Tracking files

```txt
tracking/requirements.csv
tracking/tasks.csv
tracking/judges.csv
tracking/evidence.csv
tracking/decisions.csv
tracking/platform_snapshots.csv
tracking/status_log.csv
```

## Non-goals

- Replacing git
- Storing API tokens or passwords
- Overbuilding a project management system
