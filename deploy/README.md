# Deployment — Reverse Proxy Examples

The Benton Drones lead ingest app is a Python stdlib HTTP server bound to
`127.0.0.1:8000` by default.  It is **not** designed to face the public
internet directly.  Put it behind a reverse proxy that terminates TLS.

## Why a reverse proxy?

- **TLS / HTTPS** — the app is HTTP-only; the proxy provides certificates.
- **HSTS** — the proxy sets `Strict-Transport-Security`.
- **Secure cookies** — the proxy forwards `X-Forwarded-Proto: https`, which
  the app uses to automatically set the `Secure` flag on session cookies.
- **Request limits** — `limit_req` (nginx) or built-in rate limiting (Caddy)
  provide shared, off-box protection.
- **Static caching** — the proxy can serve and cache `/static/` directly.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `8000` | Listen port |
| `ENV` | (unset = dev) | Set to `production` to enforce strict secret checks |
| `ADMIN_PASSWORD` | — | Admin login password (required) |
| `ADMIN_SESSION_SECRET` | derived from password | Session token signing secret (≥32 chars in prod) |
| `CSRF_SECRET` | derived from password | CSRF token signing secret (≥32 chars in prod) |
| `COOKIE_SECURE` | `0` | Set to `1` to force Secure flag on cookies |
| `JIRA_BASE_URL` | — | JIRA integration (all 4 or none) |
| `JIRA_USER_EMAIL` | — | JIRA integration |
| `JIRA_API_TOKEN` | — | JIRA integration |
| `JIRA_PROJECT_KEY` | — | JIRA integration |

In production, set at minimum:

```bash
ENV=production
ADMIN_PASSWORD=<strong-password>
ADMIN_SESSION_SECRET=<32+ random chars>
CSRF_SECRET=<32+ random chars>
```

The app will **refuse to start** in `ENV=production` if secrets are missing
or shorter than 32 characters.

## Caddy (recommended — auto HTTPS)

```bash
# Install Caddy, then:
caddy run --config deploy/Caddyfile
```

Caddy automatically obtains and renews Let's Encrypt certificates.  Edit
`deploy/Caddyfile` and replace `leads.bentondrones.com` with your domain.

## nginx + certbot

```bash
# Install nginx and certbot
sudo cp deploy/nginx.conf /etc/nginx/sites-available/lead-ingest
sudo ln -s /etc/nginx/sites-available/lead-ingest /etc/nginx/sites-enabled/
# Edit the file to set your domain and uncomment the SSL cert paths
sudo certbot --nginx -d leads.bentondrones.com
sudo nginx -t && sudo systemctl reload nginx
```

## Process management

Use systemd or Docker with a restart policy:

```ini
# /etc/systemd/system/lead-ingest.service
[Unit]
Description=Benton Drones Lead Ingest
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/lead-ingest
EnvironmentFile=/opt/lead-ingest/.env
ExecStart=/opt/lead-ingest/.venv/bin/python -m lead_ingest.server
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## Health check

Once running, verify:

```bash
curl https://leads.bentondrones.com/healthz
# {"status": "ok", "version": "0.2.0", "tests_passed": true}
```

Use this endpoint for load-balancer / container probes.

## Backups

SQLite is a single file at `data/lead_ingest.sqlite3`.  Use online backup:

```bash
sqlite3 data/lead_ingest.sqlite3 ".backup '/backups/lead_ingest-$(date +%F).sqlite3'"
```

Run this via cron.  For continuous replication, consider
[Litestream](https://litestream.io/).
