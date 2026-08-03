# Judge: JIRA Queue Replay Worker

## Pass criteria

PASS if, with evidence attached in `tracking/evidence.csv`:

1. On-read sweep: reading the queue (status/admin view or enqueue path) attempts due items, proven by test showing a due item replayed without the daemon running.
2. Daemon mode exists, runs a sweep on an interval, and exits cleanly on signal.
3. Backoff: retry delays follow exponential growth with jitter up to a documented cap, verified by a test asserting the schedule.
4. An item failing past max attempts becomes dead-lettered, is excluded from subsequent sweeps, and retains its last error.
5. Idempotency: a simulated ambiguous JIRA response (timeout after successful create) replayed later does not create a duplicate issue — the stable idempotency key / success record prevents it.
6. All queue state is in the existing database; no Redis or new service is introduced.
7. Pending/sent/dead-lettered counts and last replay outcome are visible from admin or a status endpoint.
8. Test suite passes including sweep, backoff, dead-letter, idempotency, and daemon tests.

## Fail criteria

FAIL if:

- A replay can create duplicate JIRA issues after an ambiguous failure
- Dead-lettered items keep being retried or silently vanish
- Replay requires the daemon (i.e., on-read sweep is missing)
- Queue state is in-memory or file-based outside the database

## Blocked criteria

BLOCKED: not applicable — all criteria are verifiable with mocked JIRA HTTP. Live JIRA delivery belongs to the existing JIRA integration task, not this judge.
