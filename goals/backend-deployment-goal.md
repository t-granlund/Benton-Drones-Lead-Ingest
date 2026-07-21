# Goal: Backend Deployment at leads.bentondrones.com

## Objective

Deploy the Benton Drones Lead-Ingest backend to a secure production host at `leads.bentondrones.com`.

## Required outcomes

- HTTPS enabled.
- Custom domain configured.
- Environment variables/secrets configured.
- Admin login works.
- Signup submission works.
- Database persistence works.
- Exports are protected.
- Logs avoid unnecessary PII.
- Backups or export recovery path documented.
- Health check route or equivalent exists.
- Deployment rollback path documented.

## Required production secrets

- `ADMIN_PASSWORD`
- `ADMIN_SESSION_SECRET`
- `CSRF_SECRET`
- `SHOPIFY_APP_SECRET` when App Proxy is enabled
- `DATABASE_URL` if moving beyond SQLite
- geocoder secrets if using external provider

## Non-goals

- Public unauthenticated admin/export access
- Production deployment without HTTPS
- Production deployment without backup/recovery notes
