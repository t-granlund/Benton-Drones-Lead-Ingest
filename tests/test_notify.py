"""Tests for the email notification queue (G3).

smtplib is mocked everywhere -- no real network, no credentials.
"""
from __future__ import annotations

import smtplib
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from lead_ingest import db
from lead_ingest.models import SignupInput
from lead_ingest.notify import (
    BASE_DELAY_SECONDS,
    MAX_ATTEMPTS,
    MAX_DELAY_SECONDS,
    NotifyError,
    due_items,
    enqueue_notification,
    next_delay_seconds,
    notification_idempotency_key,
    process_queue,
    queue_counts,
    render_template,
    send_email,
    smtp_config_from_env,
)

NOW = datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)
CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "user": "leads@bentondrones.com",
    "password": "app-password",
    "from": "leads@bentondrones.com",
    "internal_to": "ops@bentondrones.com",
}


def _signup_input(email="pilot@example.com"):
    return SignupInput(
        first_name="Test",
        last_name="Pilot",
        email=email,
        phone="555-0000",
        address_line1="1 Drone Way",
        city="Bentonville",
        state="AR",
        postal_code="72712",
        consent_accepted=True,
        waiver_accepted=True,
        typed_name="Test Pilot",
    )


class NotifyTestBase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        db.init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def add_signup(self, email="pilot@example.com", notify=False):
        return db.create_signup(self.conn, _signup_input(email), geocode=False, notify=notify)


class ConfigTests(unittest.TestCase):
    def test_config_none_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(smtp_config_from_env())

    def test_config_reads_env_with_defaults(self):
        env = {"SMTP_USER": "u@x.com", "SMTP_PASSWORD": "pw"}
        with patch.dict("os.environ", env, clear=True):
            config = smtp_config_from_env()
        self.assertEqual(config["host"], "smtp.gmail.com")
        self.assertEqual(config["port"], 587)
        self.assertEqual(config["from"], "u@x.com")
        self.assertEqual(config["internal_to"], "u@x.com")

    def test_config_env_overrides(self):
        env = {
            "SMTP_USER": "u@x.com", "SMTP_PASSWORD": "pw",
            "SMTP_HOST": "smtp.example.com", "SMTP_PORT": "2525",
            "NOTIFY_FROM": "from@x.com", "NOTIFY_INTERNAL_TO": "ops@x.com",
        }
        with patch.dict("os.environ", env, clear=True):
            config = smtp_config_from_env()
        self.assertEqual(config["host"], "smtp.example.com")
        self.assertEqual(config["port"], 2525)
        self.assertEqual(config["from"], "from@x.com")
        self.assertEqual(config["internal_to"], "ops@x.com")


class SendTests(unittest.TestCase):
    @patch("smtplib.SMTP")
    def test_send_email_uses_starttls_and_login(self, mock_smtp_cls):
        smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_email(CONFIG, "to@example.com", "Subject", "Body")
        mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587, timeout=15)
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with("leads@bentondrones.com", "app-password")
        message = smtp.send_message.call_args[0][0]
        self.assertEqual(message["To"], "to@example.com")
        self.assertEqual(message["Subject"], "Subject")
        self.assertIn("Body", message.get_content())

    @patch("smtplib.SMTP")
    def test_smtp_failure_raises_notify_error(self, mock_smtp_cls):
        mock_smtp_cls.side_effect = smtplib.SMTPConnectError(421, "nope")
        with self.assertRaises(NotifyError):
            send_email(CONFIG, "to@example.com", "S", "B")

    def test_missing_config_raises(self):
        with self.assertRaises(NotifyError):
            send_email(None, "to@example.com", "S", "B")


class EnqueueTests(NotifyTestBase):
    def test_enqueue_creates_pending_row(self):
        signup_id = self.add_signup()
        row = db.get_signup(self.conn, signup_id)
        queue_id = enqueue_notification(self.conn, dict(row), "customer_confirmation")
        self.conn.commit()
        item = self.conn.execute(
            "SELECT * FROM email_queue WHERE id = ?", (queue_id,)
        ).fetchone()
        self.assertEqual(item["status"], "pending")
        self.assertEqual(item["recipient"], "pilot@example.com")
        self.assertEqual(item["template"], "customer_confirmation")
        self.assertEqual(item["signup_id"], signup_id)
        self.assertEqual(
            item["idempotency_key"], f"customer_confirmation-signup-{signup_id}"
        )
        self.assertIn("Test Pilot", item["body"])

    def test_enqueue_is_idempotent_per_event(self):
        signup_id = self.add_signup()
        row = db.get_signup(self.conn, signup_id)
        first = enqueue_notification(self.conn, dict(row), "customer_confirmation")
        second = enqueue_notification(self.conn, dict(row), "customer_confirmation")
        self.assertEqual(first, second)
        count = self.conn.execute(
            "SELECT COUNT(*) AS c FROM email_queue WHERE signup_id = ?", (signup_id,)
        ).fetchone()["c"]
        self.assertEqual(count, 1)

    def test_unknown_template_raises(self):
        signup_id = self.add_signup()
        row = db.get_signup(self.conn, signup_id)
        with self.assertRaises(NotifyError):
            enqueue_notification(self.conn, dict(row), "no_such_template")


class TemplateTests(NotifyTestBase):
    def test_customer_confirmation_renders_lead_data(self):
        signup_id = self.add_signup()
        row = dict(db.get_signup(self.conn, signup_id))
        recipient, subject, body = render_template("customer_confirmation", row)
        self.assertEqual(recipient, "pilot@example.com")
        self.assertIn("Test Pilot", body)
        self.assertIn("1 Drone Way", body)
        self.assertNotIn("<html", body.lower())  # plain text only

    def test_internal_alert_renders_lead_data(self):
        signup_id = self.add_signup()
        row = dict(db.get_signup(self.conn, signup_id))
        recipient, subject, body = render_template(
            "internal_alert", row, internal_to="ops@bentondrones.com"
        )
        self.assertEqual(recipient, "ops@bentondrones.com")
        self.assertIn("Test Pilot", subject)
        self.assertIn("pilot@example.com", body)
        self.assertIn(f"#{signup_id}", body)


class SignupWiringTests(NotifyTestBase):
    def test_signup_enqueues_both_notifications(self):
        signup_id = db.create_signup(
            self.conn, _signup_input(), geocode=False,
            notify_internal_to="ops@bentondrones.com",
        )
        rows = self.conn.execute(
            "SELECT * FROM email_queue WHERE signup_id = ? ORDER BY id", (signup_id,)
        ).fetchall()
        self.assertEqual(len(rows), 2)
        templates = {row["template"] for row in rows}
        self.assertEqual(templates, {"customer_confirmation", "internal_alert"})
        by_template = {row["template"]: row for row in rows}
        self.assertEqual(by_template["customer_confirmation"]["recipient"], "pilot@example.com")
        self.assertEqual(by_template["internal_alert"]["recipient"], "ops@bentondrones.com")

    def test_enqueue_failure_rolls_back_whole_signup(self):
        """A failure mid-enqueue leaves NO partial visible state."""
        with patch(
            "lead_ingest.db.enqueue_notification",
            side_effect=RuntimeError("boom on second enqueue"),
        ):
            with self.assertRaises(RuntimeError):
                db.create_signup(self.conn, _signup_input(), geocode=False)
        # Nothing visible: no signup, no consent, no signature, no email rows.
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS c FROM signups").fetchone()["c"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS c FROM consent_records").fetchone()["c"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS c FROM signatures").fetchone()["c"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS c FROM email_queue").fetchone()["c"], 0)

    def test_retried_signup_request_does_not_double_queue(self):
        signup_id = db.create_signup(self.conn, _signup_input(), geocode=False)
        row = dict(db.get_signup(self.conn, signup_id))
        # Triggering logic runs again (e.g. duplicate form submission retry).
        enqueue_notification(self.conn, row, "customer_confirmation")
        enqueue_notification(self.conn, row, "internal_alert", "ops@bentondrones.com")
        self.conn.commit()
        count = self.conn.execute(
            "SELECT COUNT(*) AS c FROM email_queue WHERE signup_id = ?", (signup_id,)
        ).fetchone()["c"]
        self.assertEqual(count, 2)  # still exactly one of each template


    def test_retry_after_rolled_back_signup_does_not_double_queue(self):
        """Pathological retry: a request queues notifications then rolls
        back its signup insert (orphaned queue rows). A retried request
        for the same logical signup must NOT pile up duplicates."""
        # Simulate the orphan: queue rows committed, signup insert aborted.
        orphan = {
            "id": 1, "first_name": "Test", "last_name": "Pilot",
            "email": "pilot@example.com", "full_address": "1 Drone Way, Bentonville, AR, 72712",
            "campaign": "", "source": "", "created_at": "2026-07-31T11:00:00+00:00",
        }
        enqueue_notification(self.conn, orphan, "customer_confirmation")
        enqueue_notification(self.conn, orphan, "internal_alert", "ops@x.com")
        self.conn.commit()  # orphaned queue rows, NO signup row

        # Retried request: fresh signup insert (gets id 1 again).
        signup_id = db.create_signup(self.conn, _signup_input(), geocode=False)
        count = self.conn.execute(
            "SELECT COUNT(*) AS c FROM email_queue WHERE signup_id = ?", (signup_id,)
        ).fetchone()["c"]
        self.assertEqual(count, 2)  # exactly one of each template


class ProcessQueueTests(NotifyTestBase):
    def _queued(self, email="pilot@example.com"):
        db.create_signup(self.conn, _signup_input(email), geocode=False)

    @patch("lead_ingest.notify.send_email")
    def test_send_success_marks_sent(self, mock_send):
        self._queued()
        outcome = process_queue(self.conn, CONFIG, now=NOW)
        self.assertEqual(outcome["sent"], 2)
        self.assertEqual(mock_send.call_count, 2)
        counts = queue_counts(self.conn)
        self.assertEqual(counts, {"pending": 0, "sent": 2, "dead": 0})

    @patch("lead_ingest.notify.send_email", side_effect=NotifyError("SMTP down"))
    def test_failure_backs_off_then_dead_letters(self, mock_send):
        self._queued()
        outcome = process_queue(self.conn, CONFIG, now=NOW)
        self.assertEqual(outcome["failed"], 2)
        rows = self.conn.execute("SELECT * FROM email_queue").fetchall()
        for row in rows:
            self.assertEqual(row["attempts"], 1)
            self.assertEqual(row["last_error"], "SMTP down")
            self.assertIsNotNone(row["next_attempt_at"])
            self.assertEqual(row["status"], "pending")
        # Not due immediately after failure.
        self.assertEqual(due_items(self.conn, NOW), [])

        # Exhaust attempts -> dead-lettered, error retained, excluded.
        now = NOW
        for _ in range(MAX_ATTEMPTS - 1):
            now += timedelta(hours=2)
            process_queue(self.conn, CONFIG, now=now)
        rows = self.conn.execute("SELECT * FROM email_queue").fetchall()
        for row in rows:
            self.assertEqual(row["status"], "dead")
            self.assertEqual(row["attempts"], MAX_ATTEMPTS)
            self.assertEqual(row["last_error"], "SMTP down")
        outcome = process_queue(self.conn, CONFIG, now=now + timedelta(days=365))
        self.assertEqual(outcome["attempted"], 0)

    @patch("lead_ingest.notify.send_email")
    def test_degradation_queues_pending_and_logs_once(self, mock_send):
        """No SMTP creds: signup succeeds, message stays pending, warning."""
        self._queued()
        with self.assertLogs("lead_ingest.notify", level="WARNING") as logs:
            outcome = process_queue(self.conn, None, now=NOW)
        self.assertTrue(any("EMAIL DEGRADED" in m for m in logs.output))
        self.assertEqual(outcome["skipped"], 2)
        mock_send.assert_not_called()
        self.assertEqual(queue_counts(self.conn)["pending"], 2)
        # Signup itself succeeded (that is the degradation contract).
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) AS c FROM signups").fetchone()["c"], 1
        )


class BackoffTests(unittest.TestCase):
    def test_schedule_grows_and_caps(self):
        self.assertEqual(next_delay_seconds(0, rand=lambda: 0.5), BASE_DELAY_SECONDS * 0.75)
        self.assertEqual(next_delay_seconds(2, rand=lambda: 0.5), BASE_DELAY_SECONDS * 4 * 0.75)
        self.assertEqual(next_delay_seconds(100, rand=lambda: 0.5), MAX_DELAY_SECONDS * 0.75)

    def test_jitter_bounds(self):
        for attempt in range(6):
            delay = next_delay_seconds(attempt)
            ceiling = min(MAX_DELAY_SECONDS, BASE_DELAY_SECONDS * 2**attempt)
            self.assertGreaterEqual(delay, ceiling * 0.5)
            self.assertLessEqual(delay, ceiling)


if __name__ == "__main__":
    unittest.main()
