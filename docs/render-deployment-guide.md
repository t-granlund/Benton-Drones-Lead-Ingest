# Benton Drones Lead Ingest -- Render Deployment Guide

This guide covers deploying the Benton Drones Lead Ingest app to Render and
connecting it to a Neon PostgreSQL database.

---

## Architecture overview

The project uses three hosting layers, each serving a different purpose:

| Layer | Host | What it serves |
|---|---|---|
| Static docs | GitHub Pages | Training guide, architecture diagram, explainer guide, landing page |
| Python app | Render | Signup form, admin dashboard, exports, maps, JIRA, API routes |
| Database | Neon | PostgreSQL (leads, consent, signatures, audit trail) |

GitHub Pages cannot run Python, so the interactive routes (`/signup`,
`/admin`, `/export/*`) only work on Render (or locally). Neon is the database
-- it stores data but does not run the app.

---

## Prerequisites

1. A GitHub account with push access to
   `t-granlund/Benton-Drones-Lead-Ingest`.
2. A Render account (sign up at <https://render.com> using GitHub).
3. A Neon PostgreSQL project with a connection string ready (see
   [Neon setup](#neon-postgresql-setup) below).
4. Strong secrets generated and ready to paste (see
   [Generating secrets](#generating-secrets)).

---

## Step 1: Deploy from GitHub

The repo already contains a `render.yaml` Blueprint at the root, so the
fastest path is to let Render read it.

1. Go to <https://render.com> and sign in with GitHub.
2. Click **New** > **Blueprint**.
3. Select the `t-granlund/Benton-Drones-Lead-Ingest` repo.
4. Render reads `render.yaml` and shows a web service named
   `benton-drones-lead-ingest`.
5. Click **Apply**. Render starts building the Docker image.

If you already created the service manually (deployed from the GitHub repo
without a Blueprint), the same environment variables apply -- just set them
in the dashboard as described in Step 2.

> **Note:** The Dockerfile sets `HOST=0.0.0.0` so the server binds to all
> interfaces inside the container. Render injects `PORT` automatically at
> runtime. The start command is `python -m lead_ingest.server`.

---

## Step 2: Set environment variables

Go to the Render dashboard and open your service, then click the
**Environment** tab. Add each variable below.

| Variable | Value | Required |
|---|---|---|
| `ADMIN_PASSWORD` | A strong, unique password for admin login | Yes |
| `ADMIN_SESSION_SECRET` | 32+ random characters (signs session cookies) | Yes |
| `CSRF_SECRET` | 32+ random characters (signs CSRF tokens) | Yes |
| `COOKIE_SECURE` | `1` | Yes |
| `ENV` | `production` | Yes |
| `DATABASE_URL` | Neon connection string with `?sslmode=require` | Yes |

Click **Save Changes** when done. Render redeploys automatically.

### What each variable does

- **ADMIN_PASSWORD** -- the password you type at `/admin-login`. Pick
  something strong and unique; do not reuse a personal password.
- **ADMIN_SESSION_SECRET** -- a random string used to sign the admin
  session cookie. Must be at least 32 characters when `ENV=production`.
- **CSRF_SECRET** -- a random string used to sign CSRF tokens. Must be at
  least 32 characters when `ENV=production`.
- **COOKIE_SECURE** -- set to `1` so cookies carry the `Secure` flag.
  Render serves HTTPS, so this should always be `1`.
- **ENV** -- set to `production` to enforce strict secret checks on boot.
  The app refuses to start if `ADMIN_SESSION_SECRET` or `CSRF_SECRET` are
  shorter than 32 characters.
- **DATABASE_URL** -- the Neon PostgreSQL connection string. The app
  switches from SQLite to PostgreSQL automatically when this is set.

> **Important:** The Neon connection string must include `?sslmode=require`
> (or `?sslmode=verify-full` for stricter validation). The app does not add
> this automatically. Example:
>
> ```
> postgresql://neondb:AbCdEfGh@ep-cool-db-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
> ```

### Generating secrets

Generate `ADMIN_SESSION_SECRET` and `CSRF_SECRET` with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run it twice -- once for each secret. Each produces a 43-character
URL-safe string. Paste the results into the Render Environment tab.

For `ADMIN_PASSWORD`, choose a strong password (12+ characters, mixed
case, numbers, symbols) or generate one:

```bash
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

---

## Neon PostgreSQL setup

### Create a Neon project

1. Go to <https://neon.tech> and sign up (free tier includes 0.5 GB).
2. Create a new project and select a region close to your Render service
   (Oregon is the default in `render.yaml`).
3. Neon shows a connection string. Copy it.
4. Make sure it ends with `?sslmode=require`.

### Paste DATABASE_URL into Render

1. In the Render dashboard, go to your service **Environment** tab.
2. Add (or edit) `DATABASE_URL` and paste the Neon connection string.
3. Click **Save Changes**. Render redeploys.

When `DATABASE_URL` is set, the app:

- Connects to PostgreSQL via `psycopg2` instead of `sqlite3`.
- Creates all tables with `SERIAL` primary keys.
- Normalises `?` placeholders to `%s` automatically.
- Handles `lastrowid` via `RETURNING id`.

When `DATABASE_URL` is **not** set, the app falls back to SQLite. For
local development, simply do not set it.

---

## Step 3: Verify the deployment

After the deploy finishes and the health check passes, verify each piece:

### Health check

```bash
curl https://benton-drones-lead-ingest.onrender.com/healthz
```

Expected response (HTTP 200):

```json
{"status": "ok"}
```

### Test signup

Open `https://benton-drones-lead-ingest.onrender.com/signup` in a browser
and submit a test signup with consent and a typed-name signature.

Or via curl (adjust field values as needed):

```bash
curl -i -X POST https://benton-drones-lead-ingest.onrender.com/signup \
  -d "full_name=Test User" \
  -d "email=test@example.com" \
  -d "phone=555-123-4567" \
  -d "address=123 Main St, Benton, AR 72015" \
  -d "service_type=aerial_inspection" \
  -d "consent=on" \
  -d "typed_signature=Test User"
```

### Admin login and dashboard

1. Open `https://benton-drones-lead-ingest.onrender.com/admin-login`.
2. Enter your `ADMIN_PASSWORD`.
3. The dashboard at `/admin` should show the test lead on the map and table.

### Exports

```bash
curl -b cookies.txt -c cookies.txt -X POST \
  https://benton-drones-lead-ingest.onrender.com/admin-login \
  -d "password=YOUR_ADMIN_PASSWORD"

curl -b cookies.txt https://benton-drones-lead-ingest.onrender.com/export/csv
curl -b cookies.txt https://benton-drones-lead-ingest.onrender.com/export/geojson
curl -b cookies.txt https://benton-drones-lead-ingest.onrender.com/export/kml
```

---

## Important notes

1. **Free tier spin-down:** Render's free plan spins down the web service
   after ~15 minutes of inactivity. The next request triggers a cold start
   that takes roughly 50 seconds. Upgrade to the **Starter** plan
   ($7/month) in `render.yaml` (`plan: starter`) for always-on service with
   no spin-down.

2. **No persistent disk needed:** The database lives in Neon, not on the
   container filesystem. You do not need to mount a disk. If you ever
   switch back to SQLite, you would need a persistent disk at `/app/data`,
   but that is not the case with Neon.

3. **DATABASE_URL is the only place the Neon password should live.** Never
   commit the connection string to the repo. Set it in the Render
   Environment tab. The `.gitignore` excludes `.env` and `data/`.

4. **Waiver text needs legal review.** The waiver in `lead_ingest/models.py`
   is adapted from a provided consent form and must be reviewed by legal
   counsel before production use. The `[PRIVACY POLICY URL -- REPLACE BEFORE
   USE]` and `[VISION POLICY URL -- REPLACE BEFORE USE]` placeholders must
   be replaced with real URLs before going live.

5. **HTTPS is automatic.** Render provides TLS on the default
   `*.onrender.com` domain. Set `COOKIE_SECURE=1` so session cookies carry
   the Secure flag.

---

## Quick reference

| What | Value |
|---|---|
| App host | Render |
| Build method | Dockerfile (auto-detected via `render.yaml`) |
| Internal port | 8000 (Render injects PORT at runtime) |
| Health check | `GET /healthz` |
| Database | Neon PostgreSQL (`DATABASE_URL`) |
| Start command | `python -m lead_ingest.server` |
| GitHub repo | `https://github.com/t-granlund/Benton-Drones-Lead-Ingest` |
| Render dashboard | <https://render.com> |
| Render Blueprint spec | <https://render.com/docs/blueprint-spec> |

---

## Local Docker testing

Test the Docker image locally before or after deploying to Render:

```bash
docker build -t benton-drones .

docker run -p 8000:8000 \
  -e ADMIN_PASSWORD=your-strong-password \
  -e ADMIN_SESSION_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  -e CSRF_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  -e COOKIE_SECURE=0 \
  -e ENV=production \
  benton-drones
```

Then open:

- `http://localhost:8000/healthz`
- `http://localhost:8000/signup`
- `http://localhost:8000/admin-login`

Use `COOKIE_SECURE=0` for local HTTP testing. Set it to `1` for any HTTPS
deployment (including Render).

To test with Neon locally, add `-e DATABASE_URL="postgresql://...?sslmode=require"`
to the `docker run` command.
