# Judge: Production Hardening

## Pass criteria

PASS if:

- HTTPS is enforced.
- Secure cookies are enabled in production.
- CSRF is enabled for forms.
- Signup spam protection exists.
- Rate limiting or abuse throttling exists.
- Admin/export routes require auth.
- Consent text/version/timestamp are stored.
- Server-side validation rejects invalid data.
- Shopify HMAC/signature validation is enabled before App Proxy production use.
- PII is not unnecessarily logged.
- Backup/recovery path is documented.
- Secrets are environment-managed.

## Fail criteria

FAIL if:

- Public exports expose PII.
- Consent can be bypassed.
- Invalid signups are accepted.
- Production trusts unsigned Shopify context.
- HTTPS is missing.
- Secrets are committed.
