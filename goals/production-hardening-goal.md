# Goal: Production Hardening

## Objective

Make the system safe for real lead capture and operations.

## Required outcomes

- HTTPS enforced.
- Secure cookies in production.
- Admin/export routes protected.
- CSRF protection enabled.
- Signup spam protection enabled.
- Rate limiting or abuse throttling enabled.
- Consent text/version stored immutably.
- PII not logged unnecessarily.
- Server-side validation enforced.
- Backups documented.
- Recovery process documented.
- Security-sensitive env vars not committed.
- Shopify HMAC/signature validation enabled before trusting App Proxy context.
- Geocoding provider abstracted and cached.
- Production monitoring/log review path documented.

## Non-goals

- Claiming production readiness while major security gaps remain
