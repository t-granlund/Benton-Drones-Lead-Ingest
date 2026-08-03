# Goal: Persistent Rate Limiting

## Primary goal

Replace in-memory rate limiting with a database-backed token bucket so limits are shared across processes, survive restarts, and cannot be bypassed by running multiple app workers — without adding Redis or any new infrastructure.

## Autonomy

FULLY AUTONOMOUS. An agent designs, builds, and tests this entirely. No human action, account, or credential is required; it uses the existing database.

## Required capabilities

1. Token-bucket algorithm with state (token count, last refill timestamp) stored in a dedicated database table keyed by client identity (IP address, optionally plus route bucket).
2. Cross-process correctness: concurrent requests from separate app processes against the same client consume from the same bucket, enforced via atomic SQL update/compare-and-set semantics — no in-process cache of token counts.
3. Configurable limits per route class (at minimum: public signup POST, other public GETs, admin routes) via constants or environment variables, with sensible production defaults.
4. Refill-on-read: bucket state is lazily refilled from elapsed time on each check, so no background sweeper is required and idle clients reset naturally.
5. Rejection behavior: over-limit requests receive HTTP 429 with a Retry-After header and a short generic body that does not reveal limit internals.
6. Fail-closed on abuse surface, fail-open on storage error choice made explicit: if the rate-limit table is unreadable the app logs loudly and applies a conservative in-memory fallback rather than silently disabling limits.
7. No Redis, no new services, no external dependencies beyond the existing stdlib/database stack.
8. Tests: unit tests for bucket math (refill, consume, boundary), concurrency simulation, per-route limits, 429 + Retry-After response, and storage-error fallback.

## Non-goals

- Distributed limiting across multiple hosts/servers (single-host multi-process only)
- Per-user or per-account authenticated quotas
- CAPTCHA or bot-scoring integration
- Sliding-window or leaky-bucket variants beyond the token bucket
