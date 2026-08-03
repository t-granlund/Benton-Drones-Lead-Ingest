# Goal: Email Notifications

## Primary goal

Send transactional email — lead confirmation to the customer and internal new-lead alerts to the operator — through the existing Google Workspace mailbox, with reliable queuing so email failures never lose or block a signup.

## Autonomy

CODE AUTONOMOUS + HUMAN CREDENTIAL. An agent builds the sender, queue, templates, and tests. A human must create a Google Workspace SMTP app password and set it as an environment variable; no send happens in production until that credential exists.

## Required capabilities

1. Sending via Python stdlib `smtplib` over SMTP TLS (smtp.gmail.com:587) using a Google Workspace account plus app password supplied by environment variables — no third-party email SDK or paid email service.
2. Database-backed send queue table (recipient, subject, body, status, attempts, next_attempt_at, last_error) so emails are enqueued transactionally with the signup and sent asynchronously.
3. Retry with exponential backoff on SMTP failure; messages that exhaust max attempts are marked dead-lettered and remain inspectable in the database.
4. Two notification types at minimum: customer signup confirmation and internal new-lead alert, both as plain-text templates (no HTML email dependency).
5. Graceful degradation: if SMTP credentials are absent, the app runs normally, messages queue as pending, and startup logs a clear warning instead of crashing.
6. Idempotent send semantics: a given notification event produces at most one queued message even if the triggering request is retried.
7. Admin visibility: queued/failed/sent counts visible from the admin area or a status endpoint.
8. Tests: smtplib-mocked unit tests for queue enqueue, send success, retry backoff, dead-letter, missing-credential degradation, and template rendering.

## Non-goals

- SMS notifications (deferred)
- Marketing/bulk email or unsubscribe management
- HTML email templates with brand assets
- Inbound email processing or reply threading
