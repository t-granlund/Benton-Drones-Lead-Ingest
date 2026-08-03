# Judge: Persistent Rate Limiting

## Pass criteria

PASS if, with evidence attached in `tracking/evidence.csv`:

1. Bucket state lives in a database table; restarting the app process does not reset a client's consumed tokens (proven by test restarting the app object between requests).
2. Two simulated concurrent processes/threads hitting the same client key cannot jointly exceed the configured limit (atomic-update test or threading test with deterministic outcome).
3. Over-limit requests receive HTTP 429 with a Retry-After header and a generic body.
4. Limits are configurable per route class with the signup POST class distinctly stricter than public GETs.
5. No background thread/sweeper is required for refills (refill-on-read verified by test with manipulated timestamps).
6. With the rate-limit table made unreadable in a test, the app logs the failure and applies the documented conservative fallback instead of silently allowing unlimited requests.
7. No Redis, message broker, or new service appears in dependencies or startup.
8. Test suite passes including bucket math, concurrency, 429/Retry-After, and fallback tests.

## Fail criteria

FAIL if:

- Limits reset on restart or differ across processes
- 429 responses leak limit values or internal state
- Failure of the limiter silently disables limiting without a logged loud warning
- Redis or any external limiting service is added

## Blocked criteria

BLOCKED: not applicable — this requirement is fully autonomous and has no external dependency. If blocked, the block reason itself is a FAIL signal.
