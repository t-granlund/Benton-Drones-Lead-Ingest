# BDS / Dolt-Ready Tracking

This directory contains repo-local tracking tables for Benton Drones Lead-Ingest.

Dolt was installed as a repo-local portable tool under `.tools/` because the Winget installer was cancelled by the Windows installer flow. The `.tools/` and `.dolt/` directories are intentionally ignored by git.

## Source of truth

The `tracking/*.csv` files are canonical because they are human-reviewable and portable. Dolt is the local query/audit mirror generated from those CSVs.

> **Note (corrected 2026-08-17):** The PowerShell helper `scripts/dolt.ps1` is hardcoded to the Windows binary in `.tools/`, but homebrew `dolt` works fine on macOS. The ADR-001 tracking update was synced on macOS by running the `dolt table import -r --continue` commands directly (see below) and committed to Dolt (commit `eh6kjb07g62dqqnfcg20fu1qd64dskkj`). The CSVs remain the canonical source of truth; Dolt is the local query/audit mirror. On Windows, the documented `sync_tracking_to_dolt.ps1` / `check_dolt_tracking.ps1` flow still applies.

Canonical workflow:

1. Edit `tracking/*.csv`.
2. Run `./scripts/sync_tracking_to_dolt.ps1 -CommitMessage "..."`.
3. Run `./scripts/check_dolt_tracking.ps1`.
4. Commit the CSV/doc/script changes in git when a git repo exists.

The Dolt database contains imported committed copies of these tables.

## Tables

| Table | Purpose |
|---|---|
| `requirements.csv` | Stable requirements mapped to goals and judges |
| `tasks.csv` | Work items, owners, blockers, next actions |
| `judges.csv` | Acceptance checks and current judge status |
| `evidence.csv` | Test, QA, DNS, platform, and deployment evidence |
| `decisions.csv` | Architectural and operational decisions |
| `platform_snapshots.csv` | Required/captured external platform state |
| `status_log.csv` | Auditable status transitions |

## Status values

Use these consistently:

```txt
not_started
ready
in_progress
blocked
needs_review
passed
failed
deferred
accepted
proposed
superseded
needed
captured
csv_only
dolt_backed
```

## Dolt helper

Use the repo-local PowerShell helper:

```powershell
./scripts/dolt.ps1 status
./scripts/dolt.ps1 ls
./scripts/dolt.ps1 sql -q "select count(*) from requirements;"
```

## Sync/refresh the Dolt mirror

The canonical workflow is:

1. Edit `tracking/*.csv` files.
2. Run the sync script.
3. Run the drift check.

```powershell
./scripts/sync_tracking_to_dolt.ps1 -CommitMessage "Describe changes"
./scripts/check_dolt_tracking.ps1
```

## Current Dolt initialization

Dolt has been initialized and committed locally with:

```powershell
./scripts/dolt.ps1 table import -c --pk=requirement_id requirements tracking/requirements.csv
./scripts/dolt.ps1 table import -c --pk=task_id tasks tracking/tasks.csv
./scripts/dolt.ps1 table import -c --pk=judge_id judges tracking/judges.csv
./scripts/dolt.ps1 table import -c --pk=evidence_id evidence tracking/evidence.csv
./scripts/dolt.ps1 table import -c --pk=decision_id decisions tracking/decisions.csv
./scripts/dolt.ps1 table import -c --pk=snapshot_id platform_snapshots tracking/platform_snapshots.csv
./scripts/dolt.ps1 table import -c --pk=log_id status_log tracking/status_log.csv
./scripts/dolt.ps1 add .
./scripts/dolt.ps1 commit -m "Initialize Benton Drones lead ingest tracking tables"
```

Committed Dolt tables (current counts):

```txt
requirements: 16 rows (13 original + 3 ADR-001)
tasks: 22 rows (10 original + 12 ADR-001)
judges: 15 rows (12 original + 3 ADR-001)
evidence: 36 rows (35 original + 1 ADR-001)
decisions: 10 rows (9 original + 1 ADR-001)
platform_snapshots: 10 rows (7 original + 3 ADR-001)
status_log: 18 rows (9 original + 9 ADR-001)
```

## Rules

- Do not store API tokens, passwords, OAuth secrets, session cookies, or private keys.
- Every PASS should link to evidence.
- Platform screenshots/exports should be referenced from docs or artifact paths, not pasted with secrets.
- DNS and email changes require before/after evidence.
