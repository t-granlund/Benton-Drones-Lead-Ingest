# Benton Drones Lead Ingest — Railway Deployment Guide

This guide covers deploying the Benton Drones Lead Ingest app to Railway, with
alternatives (Fly.io) and a future path to Neon Postgres.

The app is pure Python stdlib + SQLite.  No Node, no npm, no external services.
The only pip dependency is the optional `fpdf2` for true PDF export.

---

## Hosting comparison and recommendation

| Option | Best for | Notes |
|---|---|---|
| **Railway** | Recommended for this MVP | Simplest deploy from GitHub, free trial tier, persistent volume for SQLite, automatic HTTPS, health checks |
| **Fly.io** | More control / global edge | Good free tier, requires `fly.toml`, slightly more ops complexity, native volumes |
| **Neon** | Database only | Serverless PostgreSQL. Use with Railway/Fly/Render if you outgrow SQLite. Not an app host by itself. |
| **Render** | Simple alternative | Free tier, easy web service + disk, but slower cold starts and fewer regions |

**Recommendation:** Railway for the app host because it is the fastest path from a
GitHub repo to a public URL with the least configuration.  Add Neon later if you
need PostgreSQL instead of SQLite (see the [Neon section](#neon-integration-future)
below).

---

## Prerequisites

1. A GitHub account with push access to
   `t-granlund/Benton-Drones-Lead-Ingest`.
2. A Railway account (sign up at <https://railway.com> using GitHub).
3. Strong secrets ready (see [Environment variables](#environment-variables)).

---

## Step-by-step Railway deployment

### 1. Sign up and create a project

1. Go to <https://railway.com> and sign in with GitHub.
2. Click **New Project**.
3. Choose **Deploy from GitHub repo**.
4. Select `t-granlund/Benton-Drones-Lead-Ingest`.
5. Railway detects the `Dockerfile` automatically and begins building.

### 2. Add environment variables

In the Railway dashboard, go to your service **Variables** tab and add:

| Variable | Value | Required |
|---|---|---|
| `ADMIN_PASSWORD` | A strong, unique password | Yes |
| `ADMIN_SESSION_SECRET` | 32+ random characters | Yes (production) |
| `CSRF_SECRET` | 32+ random characters | Yes (production) |
| `COOKIE_SECURE` | `1` | Yes (Railway uses HTTPS) |
| `ENV` | `production` | Yes |
| `HOST` | `0.0.0.0` | Already set in Dockerfile |
| `JIRA_BASE_URL` | e.g. `https://your-domain.atlassian.net` | No |
| `JIRA_USER_EMAIL` | Your JIRA email | No |
| `JIRA_API_TOKEN` | JIRA API token | No |
| `JIRA_PROJECT_KEY` | e.g. `BDS` | No |
| `JIRA_ISSUE_TYPE` | e.g. `Task` | No |
| `SHOPIFY_APP_SECRET` | Shopify app secret | No |

When `ENV=production` the app refuses to start unless `ADMIN_SESSION_SECRET`
and `CSRF_SECRET` are each at least 32 characters.  Generate them with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run that twice — once for each secret.

### 3. Add a persistent volume for SQLite

Without a volume, the SQLite database is lost every time Railway redeploys.

1. In the Railway dashboard, go to your service **Settings** tab.
2. Click **Volumes** and add a new volume.
3. Set the mount path to `/app/data`.
4. Railway persists everything written to that path across deploys and restarts.

The app stores its database at `/app/data/lead_ingest.sqlite3` and auto-creates
the schema on first boot.

### 4. Deploy

1. Click **Deploy** (Railway may have already started building).
2. Wait for the build to finish and the health check to pass.
3. Railway assigns a public URL like
   `https://benton-drones-lead-ingest-production.up.railway.app`.

### 5. Verify the deployment

Open the public URL in a browser and check:

- `https://<your-app>.up.railway.app/healthz` returns JSON with
  `"status": "ok"`.
- `https://<your-app>.up.railway.app/signup` loads the signup form.
- `https://<your-app>.up.railway.app/admin-login` loads the login page.

### 6. Add a custom domain (optional)

1. In the Railway dashboard, go to **Settings** > **Networking**.
2. Click **Generate Domain** for the Railway-managed domain, or
3. Click **Custom Domain** and enter your domain (e.g.
   `leads.bentondrones.com`).
4. Railway shows the CNAME target. Add it in your DNS provider (Cloudflare,
   Namecheap, etc.).
5. Railway provisions and renews the TLS certificate automatically.

For Cloudflare DNS, set the record to **DNS-only** (grey cloud) so Railway
handles TLS.  Using Cloudflare proxy (orange cloud) can also work but requires
matching the SSL/TLS mode to Full.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ADMIN_PASSWORD` | Yes | Password for admin login. Must not be a weak default. |
| `ADMIN_SESSION_SECRET` | Yes (prod) | Secret for signing session cookies. 32+ chars. |
| `CSRF_SECRET` | Yes (prod) | Secret for CSRF tokens. 32+ chars. |
| `COOKIE_SECURE` | Recommended | Set to `1` to add the Secure flag to cookies. Railway uses HTTPS so this should always be `1`. |
| `ENV` | Recommended | Set to `production` to enforce strict secret checks. |
| `HOST` | Set in Dockerfile | Bind address. `0.0.0.0` is required inside a container. |
| `PORT` | Set by Railway | Listen port. Railway injects this automatically. |
| `JIRA_BASE_URL` | No | JIRA Cloud base URL. |
| `JIRA_USER_EMAIL` | No | JIRA user email for API auth. |
| `JIRA_API_TOKEN` | No | JIRA API token. |
| `JIRA_PROJECT_KEY` | No | JIRA project key (e.g. `BDS`). |
| `JIRA_ISSUE_TYPE` | No | Issue type name (default: `Task`). |
| `SHOPIFY_APP_SECRET` | No | Shopify app secret for HMAC validation. |

---

## Post-deployment checklist

- [ ] `GET /healthz` returns `{"status": "ok", ...}` with HTTP 200.
- [ ] Submit a test signup at `/signup` with consent and typed-name signature.
- [ ] Log in at `/admin-login` with `ADMIN_PASSWORD`.
- [ ] Admin dashboard at `/admin` shows the test lead on the map and table.
- [ ] Lead detail page at `/admin/lead/<id>` shows consent and signature records.
- [ ] CSV export at `/export/csv` downloads successfully.
- [ ] GeoJSON export at `/export/geojson` downloads successfully.
- [ ] KML export at `/export/kml` downloads successfully.
- [ ] PDF export at `/admin/lead/<id>/pdf` downloads a real PDF (fpdf2 installed).
- [ ] Print view at `/admin/lead/<id>/print` renders the consent form.
- [ ] Volume is mounted at `/app/data` and the database persists across redeploys.
- [ ] Custom domain DNS is configured (if using one).
- [ ] Set up regular SQLite backups (see below).

---

## Backing up SQLite

The database is a single file at `/app/data/lead_ingest.sqlite3` inside the
container.  Because WAL mode is enabled, you may also see `-wal` and `-shm`
sidecar files.

To back up:

1. Use Railway's volume snapshot feature (if available on your plan).
2. Or shell into the container and copy the file:

```bash
railway shell
cp /app/data/lead_ingest.sqlite3 /app/data/backup-$(date +%Y%m%d).sqlite3
```

3. Or use the SQLite CLI hot backup command from a shell:

```bash
sqlite3 /app/data/lead_ingest.sqlite3 ".backup /app/data/backup.sqlite3"
```

---

## Local Docker testing

Test the Dockerfile locally before deploying to Railway:

```bash
# Build the image
docker build -t benton-drones .

# Run on port 8000 with a local data volume
docker run -p 8000:8000 \
  -v benton-drones-data:/app/data \
  -e ADMIN_PASSWORD=your-strong-password \
  -e ADMIN_SESSION_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  -e CSRF_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  -e COOKIE_SECURE=0 \
  benton-drones
```

Then open:

- `http://localhost:8000/healthz`
- `http://localhost:8000/signup`
- `http://localhost:8000/admin-login`

Note: `COOKIE_SECURE=0` for local HTTP testing. Set it to `1` for any HTTPS
deployment (including Railway).

---

## Fly.io alternative

Fly.io is a good alternative if you want more control over regions, native
volumes, or a global edge presence.

### Minimal fly.toml

Create a `fly.toml` at the repo root:

```toml
app = "benton-drones-lead-ingest"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

  [http_service.concurrency]
    type = "requests"
    hard_limit = 25
    soft_limit = 20

  [[http_service.checks]]
    interval = "30s"
    timeout = "5s"
    grace_period = "10s"
    method = "GET"
    path = "/healthz"

[[volume]]
  source = "benton_drones_data"
  destination = "/app/data"
```

### Deploy with Fly.io

```bash
# Install the Fly CLI (if needed)
brew install flyctl

# Log in
fly auth login

# Launch the app (first time only, creates the app and volume)
fly launch --no-deploy

# Set secrets
fly secrets set ADMIN_PASSWORD="your-strong-password"
fly secrets set ADMIN_SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
fly secrets set CSRF_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
fly secrets set COOKIE_SECURE="1"
fly secrets set ENV="production"

# Create the persistent volume
fly volumes create benton_drones_data --size 1

# Deploy
fly deploy

# Open the app
fly open
```

Fly.io handles TLS termination and provides a `*.fly.dev` domain automatically.

---

## Neon integration (future)

Neon is a serverless PostgreSQL provider. The app currently uses SQLite, which
is perfect for a single-instance MVP. You do not need Neon right now.

### When to move from SQLite to Neon Postgres

- You are running **multiple app instances** and need a shared database.
- You need **high-concurrency writes** that exceed SQLite's WAL throughput.
- You want **managed backups and point-in-time recovery** without manual scripts.
- You need **team access to the database** (multiple humans querying the same DB).
- You want **branching** for preview/staging databases (Neon's key feature).

### How to migrate

Migrating from SQLite to Postgres is an application-level change, not a hosting
change. Here is the outline:

1. Create a Neon project at <https://neon.tech> and get the connection string.
2. Add the connection string as a Railway/Fly environment variable (e.g.
   `DATABASE_URL`).
3. Replace the `sqlite3` connection layer in `lead_ingest/db.py` with
   `psycopg2` or `psycopg` (async).
4. Update SQL syntax differences (e.g. `AUTOINCREMENT` to `SERIAL`,
   `?` placeholders to `%s`).
5. Run a one-time data migration from the SQLite file to Postgres.
6. Test thoroughly before switching traffic.

This is a meaningful code change. Do not attempt it until you have a concrete
reason from the list above. SQLite is fast, reliable, and operationally simple
for a single-instance app.

### Using Neon with Railway

You can host the app on Railway and the database on Neon simultaneously:

1. Deploy the app on Railway (as described above).
2. Create a Neon Postgres database.
3. Add the `DATABASE_URL` from Neon as a Railway environment variable.
4. Update the app's database layer to use Postgres.
5. Redeploy.

Neon's free tier includes 0.5 GB of storage and a single compute endpoint, which
is enough for early production.

---

## Security notes

1. **Waiver text:** The current waiver is a placeholder. Have it reviewed by
   legal counsel before accepting real signups. The audit trail mechanism
   (typed name, timestamp, IP, user agent, versioned text) is sound, but the
   words are not.
2. **Secrets:** Never commit secrets to the repo. Use Railway's Variables tab
   or `fly secrets`. The `.gitignore` excludes `.env` and `data/`.
3. **HTTPS:** Railway and Fly both provide automatic HTTPS. Set
   `COOKIE_SECURE=1` so session cookies carry the Secure flag.
4. **Rate limiting:** The app has a built-in rate limiter (20 requests per
   minute per IP per path). For higher traffic, add a CDN or proxy-level rate
   limiting.
5. **Backups:** SQLite on a volume is durable but not replicated. Set up
   regular backups or move to Neon Postgres for managed backups.

---

## Quick reference

| What | Value |
|---|---|
| App host | Railway (recommended) |
| Build method | Dockerfile (auto-detected) |
| Internal port | 8000 (Railway injects PORT at runtime) |
| Health check | `GET /healthz` |
| Volume mount path | `/app/data` |
| Database file | `/app/data/lead_ingest.sqlite3` |
| Start command | `python -m lead_ingest.server` |
| GitHub repo | `https://github.com/t-granlund/Benton-Drones-Lead-Ingest` |
| Railway dashboard | <https://railway.com> |
