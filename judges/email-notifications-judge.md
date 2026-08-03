# Judge: Email Notifications

## Pass criteria

PASS if, with evidence attached in `tracking/evidence.csv`:

1. Sending uses stdlib `smtplib` against a configurable SMTP host/port with TLS; credentials come only from environment variables and no secret appears in the repo.
2. A signup enqueues a customer confirmation and an internal alert in the same transaction as the signup insert (proven by test: rollback on enqueue failure also rolls back nothing visible as partial state).
3. Simulated SMTP failure triggers exponential backoff retry; after max attempts the message is dead-lettered with its last error retained.
4. With SMTP env vars absent, the app starts, signups succeed, messages queue as pending, and a clear warning is logged (captured log line as evidence).
5. Retrying the triggering request does not create a duplicate queued message (idempotency test).
6. Queued/failed/sent counts are visible from admin or a status endpoint.
7. Test suite passes including queue, retry, dead-letter, degradation, and template tests.

## Fail criteria

FAIL if:

- An email send failure can lose, duplicate, or block a signup
- Credentials are hardcoded, committed, or required at import/app-start time
- Retry is unbounded (no dead-letter) or immediate (no backoff)
- A third-party email SDK or paid email service is introduced

## Blocked criteria

BLOCKED (for live-send verification only) if the human has not yet created the Google Workspace app password. All code, queue, and mocked tests must PASS autonomously before that; the live-send criterion is the only human-gated one and is verified post-credential.
