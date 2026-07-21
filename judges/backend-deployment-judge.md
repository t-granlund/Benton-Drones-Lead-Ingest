# Judge: Backend Deployment

## Pass criteria

PASS if:

- `https://leads.bentondrones.com` resolves.
- HTTPS certificate is valid.
- Signup page loads.
- Signup submission persists data.
- Admin login works.
- Admin/export routes are protected.
- Required env vars are configured.
- Logs avoid unnecessary PII.
- Database persistence is confirmed.
- Backup/export recovery path exists.
- Rollback instructions exist.

## Fail criteria

FAIL if:

- Site runs only over HTTP.
- Admin/export routes are public.
- Signup fails in production.
- Secrets are committed to repo.
- Production data is stored only ephemerally without documented risk acceptance.
