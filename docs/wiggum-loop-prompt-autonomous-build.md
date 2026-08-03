# Wiggum Loop Prompt — Autonomous Build Phase

Use this prompt to drive the Benton orchestrator through N wiggum loops that build the
fully-autonomous production gaps and push their judges to PASS. Replace `<N>` with the
number of loops you want (recommend **5** — one per buildable item below).

---

## The prompt (copy everything between the rules)

> You are the Benton Lead Orchestrator running a wiggum loop build phase on
> `/Users/tygranlund/dev/Lead-Ingest`. Run **`<N>` wiggum loop iterations**. Each iteration
> follows the established pattern in `docs/wiggum-loop-report.md`: inspect goals/judges →
> find the gap → make the change → add tests → run the suite **3 consecutive times green** →
> record judge status, remaining gaps, and the recommended next task. Append each iteration
> as a new `## Iteration <n>` section to `docs/wiggum-loop-report.md` and keep
> `tracking/` (tasks.csv, status_log.csv, judges.csv, evidence.csv) honest as you go.
>
> Work the autonomous backlog in this exact priority order — these need **no human
> credential** and their judges can reach PASS now:
>
> 1. **G1 / REQ-GEO-001** (`goals/geocoding-provider-goal.md`, `judges/geocoding-provider-judge.md`)
>    — Replace `MockGeocoder` with a real provider chain: US Census primary + Nominatim
>    fallback, DB-backed cache, address normalization, Nominatim User-Agent + 1 req/s limit,
>    unresolved-not-crash failure handling, backfill script. Judge: `JUDGE-GEO-001`.
> 2. **G5 / REQ-RATELIMIT-001** (`goals/persistent-rate-limiting-goal.md`,
>    `judges/persistent-rate-limiting-judge.md`) — token-bucket-in-DB rate limiter, atomic
>    cross-process updates, per-route-class limits, refill-on-read, HTTP 429 + Retry-After,
>    loud-fallback on storage error, no Redis. Judge: `JUDGE-RATELIMIT-001`.
> 3. **G6 / REQ-JIRA-002** (`goals/jira-queue-replay-goal.md`,
>    `judges/jira-queue-replay-judge.md`) — on-read sweep + optional daemon replay of the
>    `jira_queue` table, exponential backoff with jitter, dead-letter, idempotency keys, all
>    state in DB. Judge: `JUDGE-JIRA-002`.
> 4. **G3 / REQ-NOTIFY-001** (`goals/email-notifications-goal.md`,
>    `judges/email-notifications-judge.md`) — stdlib `smtplib` + Google Workspace SMTP sender,
>    DB-backed send queue, backoff + dead-letter, idempotency, customer confirmation +
>    internal alert templates, graceful degradation when creds absent. **Build all code +
>    mocked tests now** so every autonomous judge criterion passes; the ONE live-send
>    criterion stays BLOCKED on the human's SMTP app password. Judge: `JUDGE-NOTIFY-001`
>    (mark code criteria PASS, live-send BLOCKED).
> 5. **G4 / REQ-BACKUP-001** (`goals/backups-monitoring-goal.md`,
>    `judges/backups-monitoring-judge.md`) — `/healthz` DB-aware health endpoint, read-only
>    `scripts/verify_backup.py`, and `docs/backup-recovery-playbook.md` skeleton. **Build code
>    + docs now**; Neon console evidence + external monitor account stay BLOCKED on the human.
>    Judge: `JUDGE-BACKUP-001` (code criteria PASS, console-evidence BLOCKED).
>
> **Hard rules for every iteration:**
> - Delegate implementation to **code-puppy** (continue its session across iterations).
> - Do NOT touch production DNS, email, or deploy anything. Local code + tests only.
> - After each item, run `python -m unittest discover -s tests` AND
>   `python -m unittest discover -s tests/e2e -t tests/e2e` — both must be green **3×**.
> - Update the matching `judges.csv` row (status/result/evidence_id) and add an `EVID-*` row.
> - Record durable decisions in `kennel_remember` (wing=repo, room=decisions).
> - Do not break existing tests. If a count gate grows, keep it accurate.
> - If an item turns out to need a credential you don't have, mark that criterion BLOCKED
>   (not FAIL), note exactly what's needed, and move to the next item.
>
> **When the loops are done, report back to me (the human):** which judges reached PASS, which
> criteria are BLOCKED and on exactly what credential, the final test counts, and the precise
> list of credentials/access you need from me to unblock the rest (G2 domain, G3 live-send,
> G4 Neon/monitor, G7 Shopify). Format that credential list as an ordered checklist I can
> work through in one sitting.

---

## After the loops: what you'll hand back (the credential checklist)

The loops close everything buildable. What remains is human-gated. Expect this list:

| # | Credential / access | Unblocks |
|---|---|---|
| 1 | Cloudflare read-only API token (bentondrones.com) | G2 domain automation preflight |
| 2 | Namecheap — nameserver + DNS screenshots | G2 safe cutover |
| 3 | Google Workspace **SMTP app password** | **G3 live-send** (email notifications) |
| 4 | Google Admin — MX/SPF/DKIM/DMARC confirm | G2 cutover without breaking email |
| 5 | Shopify Admin — myshopify domain + landing CTA | G2 / G7 App Proxy |
| 6 | Render — add `leads.bentondrones.com` custom domain | G2 go-live |
| 7 | Neon console — backup/retention settings | **G4 backups evidence** |
| 8 | External uptime monitor account (UptimeRobot/BetterStack free) | **G4 monitoring** |

Once you provide those, the agents finish G3/G4 live-verify, then G2 (domain cutover),
then launch, then G7/G8 post-launch.
