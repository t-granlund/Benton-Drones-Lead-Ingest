# Goal: JIRA Queue Replay Worker

## Primary goal

Guarantee that JIRA issue creation for leads is eventually reliable: any JIRA payload that could not be delivered at signup time is durably queued and replayed automatically until it succeeds or is dead-lettered for human review.

## Autonomy

FULLY AUTONOMOUS. An agent builds the sweep, daemon, backoff, dead-letter, and idempotency logic plus tests. (Creating the JIRA API credential itself remains part of the existing JIRA integration task, not this one.)

## Required capabilities

1. On-read sweep: whenever the queue is read (admin/status view or a signup enqueue), pending items whose `next_attempt_at` has passed are attempted inline — replay makes progress even with no daemon running.
2. Daemon mode: an optional long-running worker (script/management command) that loops the sweep on an interval for production use.
3. Exponential backoff: retry delay doubles per attempt (with jitter) up to a documented maximum; attempt count and next attempt time are persisted per queue item.
4. Dead-letter: items exceeding max attempts are marked dead-lettered with their last error, excluded from further replay, and visible for manual inspection/requeue.
5. Idempotency: each queue item carries a stable idempotency key (derived from the lead/event identity) so a replay after an ambiguous JIRA response does not create duplicate issues; successful sends are recorded and never re-sent.
6. Durable queue: all queue state lives in the existing database — no Redis, no new services.
7. Observability: counts of pending/sent/dead-lettered items and last replay outcome are visible from the admin area or a status endpoint.
8. Tests: unit tests for sweep selection, backoff schedule, dead-letter transition, idempotency-key dedupe on simulated ambiguous failure, daemon loop tick, and on-read sweep triggering.

## Non-goals

- A general-purpose job framework for unrelated task types
- Real-time webhook push from JIRA back into the app
- At-most-once delivery guarantees (at-least-once with idempotency is the explicit trade-off)
- Dead-letter auto-remediation without human review
