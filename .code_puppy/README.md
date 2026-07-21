# Code Puppy Notes

## Benton Drones Lead Ingest

A local-first lead-ingest MVP. Python stdlib + SQLite only. No Node, no npm, no external services required.

## Launch

```bash
make init-db        # create the SQLite database
make run            # start the server at http://127.0.0.1:8000
```

Then visit:

- `http://127.0.0.1:8000/signup` — public signup form
- `http://127.0.0.1:8000/admin-login` — admin login (password via `ADMIN_PASSWORD` env var)
- `http://127.0.0.1:8000/admin` — admin dashboard
- `http://127.0.0.1:8000/landing-page.html` — standalone branded landing page

## Test

```bash
make test           # python -m unittest discover -s tests
```

Tests use an in-memory or temp database — no `data/` directory needed.

## Extend

### Add a new route

Edit `lead_ingest/server.py` → `do_GET` or `do_POST`, then add a handler method.

### Add a new DB table

Edit `lead_ingest/db.py` → `SCHEMA` string and add helper functions. `init_db` runs on every request so new tables appear automatically.

### Add a new test

Drop a `test_*.py` file in `tests/` using `unittest.TestCase`.

## Optional dependencies

- `fpdf2>=2.8.0` — enables true PDF export at `/admin/lead/<id>/pdf`. Without it, the server falls back to an HTML print view.

```bash
pip install -r requirements.txt   # or: pip install fpdf2
```

## JIRA integration

Set these env vars to enable JIRA ticket creation per signup:

```bash
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=you@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=BDS
JIRA_ISSUE_TYPE=Task
```

If any are missing, signups are queued in `jira_queue` for later processing.
