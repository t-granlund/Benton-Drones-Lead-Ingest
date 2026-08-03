"""Email notification queue for Benton Lead-Ingest (G3).

Transactional email via stdlib ``smtplib`` (SMTP + STARTTLS) with a
DB-backed send queue modeled on the G6 JIRA replay worker: exponential
backoff + jitter, dead-letter past max attempts, deterministic
idempotency keys, and all state in the existing database -- no Redis,
no third-party email SDK, no new services.

- :func:`smtp_config_from_env` -- config from env; ``None`` when the
  Google Workspace app password isn't set (graceful degradation: the
  app runs normally, messages queue as pending, one loud warning).
- :func:`send_email` -- plain-text send over TLS; raises NotifyError.
- :func:`enqueue_notification` -- build + queue a message INSIDE the
  caller's transaction (callers must ``commit``); idempotent per event.
- :func:`process_queue` -- send due pending items (sweep shape shared
  with the JIRA replay worker).
- :func:`queue_counts` -- pending/sent/dead for admin/status display.

Credentials come ONLY from environment variables and are never required
at import or app-start time.
"""
from __future__ import annotations

import logging
import os
import random
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

logger = logging.getLogger("lead_ingest.notify")

MAX_ATTEMPTS = 5
BASE_DELAY_SECONDS = 30.0
MAX_DELAY_SECONDS = 3600.0  # 1 hour cap, documented & testable

EMAIL_QUEUE_DDL = """
CREATE TABLE IF NOT EXISTS email_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    template TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT,
    last_error TEXT DEFAULT '',
    idempotency_key TEXT NOT NULL,
    signup_id INTEGER,
    created_at TEXT NOT NULL
)
"""


class NotifyError(Exception):
    """Raised when an email send fails."""


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

def smtp_config_from_env() -> dict | None:
    """SMTP config from env vars, or None when credentials are absent.

    Only SMTP_USER and SMTP_PASSWORD (the Google Workspace app password)
    are required; host/port/identities have production-sane defaults.
    """
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    if not user or not password:
        return None
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
        "port": int(os.environ.get("SMTP_PORT", "587").strip() or "587"),
        "user": user,
        "password": password,
        "from": os.environ.get("NOTIFY_FROM", user).strip() or user,
        "internal_to": os.environ.get("NOTIFY_INTERNAL_TO", user).strip() or user,
    }


# --------------------------------------------------------------------------
# Templates (plain text only -- no HTML email)
# --------------------------------------------------------------------------

def _lead_fields(signup_row) -> dict:
    row = dict(signup_row) if not isinstance(signup_row, dict) else signup_row
    name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
    return {
        "name": name or "there",
        "email": row.get("email", ""),
        "address": row.get("full_address", ""),
        "campaign": row.get("campaign", "") or "-",
        "source": row.get("source", "") or "-",
        "signup_id": row.get("id", "-"),
        "created_at": row.get("created_at", ""),
    }


def render_template(template: str, signup_row, internal_to: str = "") -> tuple[str, str, str]:
    """Render (recipient, subject, body) for a template + signup row."""
    fields = _lead_fields(signup_row)
    if template == "customer_confirmation":
        return (
            fields["email"],
            "Thanks for signing up with Benton Drones",
            "\n".join([
                f"Hi {fields['name']},",
                "",
                "Thanks for joining the Benton Drones delivery simulation program.",
                "We received your signup and will be in touch as local routes",
                "are planned.",
                "",
                f"Address on file: {fields['address']}",
                "",
                "- Benton Drones",
            ]),
        )
    if template == "internal_alert":
        return (
            internal_to,
            f"New lead signup: {fields['name']} <{fields['email']}>",
            "\n".join([
                "New lead captured:",
                "",
                f"Name:     {fields['name']}",
                f"Email:    {fields['email']}",
                f"Address:  {fields['address']}",
                f"Campaign: {fields['campaign']}",
                f"Source:   {fields['source']}",
                f"Signup:   #{fields['signup_id']}",
                f"Created:  {fields['created_at']}",
            ]),
        )
    raise NotifyError(f"Unknown email template: {template}")


# --------------------------------------------------------------------------
# Sending
# --------------------------------------------------------------------------

def send_email(config: dict, recipient: str, subject: str, body: str) -> None:
    """Send a plain-text email via SMTP + STARTTLS. Raises NotifyError."""
    if not config:
        raise NotifyError("SMTP config is missing — cannot send email")
    message = EmailMessage()
    message["From"] = config["from"]
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=15) as smtp:
            smtp.starttls()
            smtp.login(config["user"], config["password"])
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise NotifyError(f"SMTP send failed: {exc}") from exc


# --------------------------------------------------------------------------
# Queue
# --------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def notification_idempotency_key(template: str, signup_id: int) -> str:
    """Stable per-event key: retrying the trigger never double-queues."""
    return f"{template}-signup-{signup_id}"


def enqueue_notification(conn, signup_row, template: str, internal_to: str = "") -> int:
    """Queue a notification inside the CALLER's transaction (no commit here
    -- the caller commits so the signup + its notifications are atomic).

    Idempotent: re-enqueueing the same (template, signup) event returns
    the existing row instead of inserting a duplicate.
    """
    signup = dict(signup_row) if not isinstance(signup_row, dict) else signup_row
    signup_id = int(signup["id"])
    key = notification_idempotency_key(template, signup_id)
    existing = conn.execute(
        "SELECT id FROM email_queue WHERE idempotency_key = ?", (key,)
    ).fetchone()
    if existing is not None:
        return int(existing["id"])

    recipient, subject, body = render_template(template, signup, internal_to)
    cursor = conn.execute(
        """
        INSERT INTO email_queue
        (recipient, subject, body, template, status, attempts, next_attempt_at,
         last_error, idempotency_key, signup_id, created_at)
        VALUES (?, ?, ?, ?, 'pending', 0, NULL, '', ?, ?, ?)
        """,
        (recipient, subject, body, template, key, signup_id, _iso(_utc_now())),
    )
    return int(cursor.lastrowid)


def next_delay_seconds(
    attempts: int,
    base: float = BASE_DELAY_SECONDS,
    cap: float = MAX_DELAY_SECONDS,
    rand=random.random,
) -> float:
    """Exponential backoff with full jitter, capped (same shape as G6)."""
    ceiling = min(cap, base * (2 ** max(0, attempts)))
    return ceiling * (0.5 + 0.5 * rand())


def due_items(conn, now: datetime | None = None) -> list:
    """Pending queue rows whose next send time has arrived."""
    now = now or _utc_now()
    rows = conn.execute(
        "SELECT * FROM email_queue WHERE status = 'pending' ORDER BY id"
    ).fetchall()
    return [
        row for row in rows
        if not row["next_attempt_at"] or _parse(row["next_attempt_at"]) <= now
    ]


def _fail_item(conn, row_id: int, attempts: int, error: str, now: datetime) -> None:
    if attempts >= MAX_ATTEMPTS:
        conn.execute(
            "UPDATE email_queue SET status = 'dead', attempts = ?, last_error = ?, "
            "next_attempt_at = NULL WHERE id = ?",
            (attempts, error, row_id),
        )
        logger.error("Email queue item %s dead-lettered after %d attempts: %s",
                     row_id, attempts, error)
    else:
        delay = next_delay_seconds(attempts)
        conn.execute(
            "UPDATE email_queue SET attempts = ?, last_error = ?, next_attempt_at = ? "
            "WHERE id = ?",
            (attempts, error, _iso(now + timedelta(seconds=delay)), row_id),
        )


def process_queue(conn, config: dict | None, now: datetime | None = None) -> dict:
    """Send every due pending email. Returns an outcome summary.

    ``config`` from :func:`smtp_config_from_env`; when falsy the sweep
    short-circuits (graceful degradation) and logs one loud warning.
    """
    now = now or _utc_now()
    outcome = {"attempted": 0, "sent": 0, "failed": 0, "dead": 0, "skipped": 0}
    items = due_items(conn, now)
    if not config:
        if items:
            logger.warning(
                "EMAIL DEGRADED: SMTP credentials not set — %d queued message(s) "
                "stay pending. Set SMTP_USER/SMTP_PASSWORD to enable delivery.",
                len(items),
            )
        outcome["skipped"] = len(items)
        return outcome

    for item in items:
        outcome["attempted"] += 1
        try:
            send_email(config, item["recipient"], item["subject"], item["body"])
            conn.execute(
                "UPDATE email_queue SET status = 'sent', attempts = ?, last_error = '' "
                "WHERE id = ?",
                (int(item["attempts"] or 0) + 1, item["id"]),
            )
            outcome["sent"] += 1
        except Exception as exc:  # one bad message must not kill the sweep
            attempts = int(item["attempts"] or 0) + 1
            _fail_item(conn, item["id"], attempts, str(exc), now)
            outcome["failed"] += 1
            if attempts >= MAX_ATTEMPTS:
                outcome["dead"] += 1
    return outcome


def queue_counts(conn) -> dict:
    """Pending/sent/dead counts for admin/status display."""
    rows = conn.execute(
        "SELECT status, COUNT(*) AS count FROM email_queue GROUP BY status"
    ).fetchall()
    counts = {row["status"]: row["count"] for row in rows}
    return {
        "pending": counts.get("pending", 0),
        "sent": counts.get("sent", 0),
        "dead": counts.get("dead", 0),
    }
