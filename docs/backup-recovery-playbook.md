# Backup & Recovery Playbook — Benton Lead-Ingest

Audience: **anyone** holding the incident, not just the author. Follow the
steps top to bottom. Everything here is either executable today or marked
`<<HUMAN: ... >>` where a human must supply console-specific detail that
lives behind an authenticated dashboard.

The production database is **Neon Postgres**; the app runs on **Render** and
connects via the `DATABASE_URL` environment variable. The app is stdlib-only
and auto-creates its schema on startup — so a **restore is only ever about
the DATA**, never about rebuilding tables by hand.

---

## 1. What protects us (current state)

| Layer | What | Where |
|---|---|---|
| Neon native backups | Point-in-time recovery + branch restore | Neon console |
| Uptime monitor | External ping of `/healthz` | `<<HUMAN: monitor account >>` |
| Verification script | Read-only reachability + table counts | `scripts/verify_backup.py` |
| Health endpoint | Unauthenticated, DB-aware | `GET /healthz` |

Neon keeps a continuous write-ahead log, which is what makes
**point-in-time recovery (PITR)** possible: you can restore the database to
any second inside the retention window without having taken a manual snapshot.

- Retention window observed in our project:
  `<<HUMAN: Neon project name, branch id, and the PITR retention window shown
  in the console (default is 24h on free tier, up to 7/30 days on paid) —
  attach a screenshot of the Settings → Storage/Backup page >>`

---

## 2. Health endpoint (monitor target)

`GET /healthz` — **unauthenticated**, lightweight, DB-aware.

- Returns **HTTP 200** `{"status":"ok","db":"ok"}` only when the app process
  is up **and** a `SELECT 1` against the database succeeds.
- Returns **HTTP 503** `{"status":"error","db":"unreachable"}` when the
  database cannot be reached.
- Read-only and fast: it opens a bare connection and runs one trivial query
  (it does NOT run migrations or touch the schema).

Production URL: `https://<<HUMAN: public domain, e.g. leads.bentondrones.com>>/healthz`

This is the URL the external uptime monitor hits (section 5).

---

## 3. Verify a backup / restore target (run this FIRST)

Before trusting any restored database, verify it is reachable and actually
contains data:

```bash
# Postgres / Neon branch or PITR restore:
DATABASE_URL="postgres://<user>:<password>@<restored-host>/<db>" \
  python -m scripts.verify_backup

# Local SQLite file:
python -m scripts.verify_backup --db path/to/backup.sqlite3
```

The script is **strictly read-only** (SQLite is even opened `mode=ro`;
Postgres uses a read-only session). It prints:

- `REACHABLE:` / `UNREACHABLE:` the target,
- a row count for each key table (`signups`, `signatures`,
  `consent_records`, `jira_queue`, `email_queue`, `geocode_cache`,
  `rate_limit_buckets`),
- a **WARNING** if any table is missing or `signups` is empty (the classic
  "restored successfully… to an empty branch" trap).

Exit code is `0` when reachable, non-zero otherwise — safe to wire into a
cron/alert if you want automated restore-drill checks.

---

## 4. Restore procedure

### 4a. Point-in-time recovery (PITR) — "rewind to before the bad thing"

1. Neon console → your project → **Branches**.
   `<<HUMAN: exact console path for our Neon version — screenshot the
   Branches page >>`
2. Choose **Restore / Create branch from history** (Neon labels it
   "Point in time restore" on the branch menu).
3. Pick the timestamp **just before** the data loss. Neon creates a new
   branch holding the database as of that second.
4. Verify the new branch BEFORE switching the app to it:
   ```bash
   DATABASE_URL="<the new branch's connection string>" \
     python -m scripts.verify_backup
   ```
   Confirm `signups` count matches what you expect (check the admin
   dashboard total from before the incident if unsure).
5. Re-point the app (section 4c).

### 4b. Branch restore — "promote a good branch over a bad one"

1. Neon console → **Branches** → select the known-good branch (e.g. a PITR
   branch from 4a, or a nightly branch).
2. Use **Set as primary / Restore to primary** so the good branch becomes
   the branch the app's connection string points at.
   `<<HUMAN: confirm the exact button label in our Neon console >>`
3. Verify with `scripts/verify_backup` against the primary connection string.
4. Re-point the app (4c) if the connection string changed.

### 4c. Point the app at the restored database (Render)

1. Render dashboard → the Lead-Ingest service → **Environment**.
2. Update `DATABASE_URL` to the restored branch's connection string.
   `<<HUMAN: paste the Render service name and which env group/var holds
   DATABASE_URL >>`
3. Save → Render redeploys automatically.
4. Confirm recovery:
   - `curl -i https://<domain>/healthz` → expect **200** and `"db":"ok"`.
   - Open `/admin` and confirm the lead count matches the pre-incident total.
   - Re-run `scripts/verify_backup` against the live `DATABASE_URL`.

### 4d. Post-restore housekeeping

- The JIRA queue (`jira_queue`) and email queue (`email_queue`) resume
  replaying automatically on the next on-read sweep or daemon tick — pending
  items from before the incident are NOT lost; they retry with backoff.
- If signups arrived DURING the outage window on the old (bad) branch, they
  live only on that branch — decide whether to export/replay them before
  decommissioning it.

---

## 5. Uptime monitor (external)

Free-tier external monitor (UptimeRobot / BetterStack free tier both work —
no new infra, just an account):

| Setting | Value |
|---|---|
| Monitor type | HTTP(s) keyword/status check |
| Target URL | `https://<<HUMAN: public domain>>/healthz` |
| Expected status | 200 (optionally keyword `"db":"ok"`) |
| Check interval | `<<HUMAN: 60s on paid, 5 min on UptimeRobot free tier >>` |
| Alert when | 2 consecutive failures (avoid blip fatigue) |
| Alert destination | `<<HUMAN: operator Google Workspace mailbox, e.g. ops@bentondrones.com >>` |
| Account | `<<HUMAN: create the monitor account; attach a screenshot of the configured monitor >>` |

The monitor target is deliberately **unauthenticated** — external monitors
cannot log in, and `/healthz` exposes nothing beyond up/down + DB reachability.

---

## 6. Alert routing

Downtime alerts go to the operator's **Google Workspace mailbox** (the same
mailbox family that sends lead notifications). Destination address:
`<<HUMAN: exact alert mailbox, e.g. ops@bentondrones.com >>`.

On a downtime alert:
1. Check `curl -i https://<domain>/healthz` — `503`/`"db":"unreachable"`
   points at the database; a connection timeout points at Render/DNS.
2. DB unreachable → jump to section 4 (restore) after confirming in the Neon
   console whether the branch is healthy.
3. Render issue → check the Render service logs; the app is stateless apart
   from the DB, so a redeploy is safe.

---

## 7. Restore drill (do this once, before you need it)

1. Create a PITR branch from ~1 hour ago (section 4a, stop before 4c).
2. Run `scripts/verify_backup` against it; confirm non-zero `signups`.
3. Delete the drill branch.
4. Record the date + outcome here:
   `<<HUMAN: drill date, who ran it, observed restore time >>`
