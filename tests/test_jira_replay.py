"""Tests for the JIRA queue replay worker (G6).

All JIRA HTTP is mocked by patching create_jira_ticket -- no network.
"""
from __future__ import annotations

import sqlite3
import threading
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from lead_ingest import db
from lead_ingest.jira import JiraApiError
from lead_ingest.jira_replay import (
    BASE_DELAY_SECONDS,
    MAX_ATTEMPTS,
    MAX_DELAY_SECONDS,
    due_items,
    next_delay_seconds,
    queue_stats,
    run_daemon,
    sweep,
)
from lead_ingest.models import SignupInput

CONFIG = {
    "base_url": "https://example.atlassian.net",
    "user_email": "bot@example.com",
    "api_token": "token",
    "project_key": "BDS",
    "issue_type": "Task",
}
NOW = datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)


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


class ReplayTestBase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        db.init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def add_queued_signup(self, email="pilot@example.com", error="boom"):
        signup_id = db.create_signup(self.conn, _signup_input(email), geocode=False)
        queue_id = db.queue_jira_ticket(self.conn, signup_id, error)
        return signup_id, queue_id


class BackoffTests(unittest.TestCase):
    def test_schedule_grows_exponentially_and_caps(self):
        # Deterministic jitter: rand() == 0.5 -> delay = ceiling * 0.75
        self.assertEqual(next_delay_seconds(0, rand=lambda: 0.5), BASE_DELAY_SECONDS * 0.75)
        self.assertEqual(next_delay_seconds(1, rand=lambda: 0.5), BASE_DELAY_SECONDS * 2 * 0.75)
        self.assertEqual(next_delay_seconds(5, rand=lambda: 0.5), BASE_DELAY_SECONDS * 32 * 0.75)
        # attempts=100 would be astronomically past the cap -> exactly cap * 0.75
        self.assertEqual(next_delay_seconds(100, rand=lambda: 0.5), MAX_DELAY_SECONDS * 0.75)

    def test_jitter_bounds(self):
        for attempt in range(8):
            delay = next_delay_seconds(attempt)
            ceiling = min(MAX_DELAY_SECONDS, BASE_DELAY_SECONDS * 2**attempt)
            self.assertGreaterEqual(delay, ceiling * 0.5)
            self.assertLessEqual(delay, ceiling)

    def test_cap_is_documented_max(self):
        self.assertEqual(MAX_DELAY_SECONDS, 3600.0)


class DueSelectionTests(ReplayTestBase):
    def test_due_items_selects_pending_only_when_time_arrived(self):
        _, q1 = self.add_queued_signup("a@example.com")  # next_attempt_at NULL -> due
        _, q2 = self.add_queued_signup("b@example.com")
        self.conn.execute(
            "UPDATE jira_queue SET next_attempt_at = ? WHERE id = ?",
            ((NOW + timedelta(hours=1)).isoformat(timespec="seconds"), q2),
        )
        self.conn.commit()
        due = due_items(self.conn, NOW)
        self.assertEqual([row["id"] for row in due], [q1])

    def test_created_and_dead_rows_never_due(self):
        signup_id, queue_id = self.add_queued_signup()
        db.mark_jira_ticket_created(self.conn, signup_id, "BDS-1", "http://x")
        _, q2 = self.add_queued_signup("c@example.com")
        self.conn.execute("UPDATE jira_queue SET status = 'dead' WHERE id = ?", (q2,))
        self.conn.commit()
        self.assertEqual(due_items(self.conn, NOW), [])


class SweepTests(ReplayTestBase):
    @patch("lead_ingest.jira_replay.create_jira_ticket", return_value="BDS-42")
    def test_sweep_success_marks_created_and_upserts_ticket(self, mock_create):
        signup_id, _ = self.add_queued_signup()
        outcome = sweep(self.conn, CONFIG, now=NOW)
        self.assertEqual(outcome["created"], 1)
        self.assertEqual(outcome["attempted"], 1)
        ticket = db.get_jira_ticket(self.conn, signup_id)
        self.assertEqual(ticket["ticket_key"], "BDS-42")
        self.assertEqual(ticket["jira_issue_url"], "https://example.atlassian.net/browse/BDS-42")
        entry = db.get_jira_queue_entry(self.conn, signup_id)
        self.assertEqual(entry["status"], "created")

    @patch("lead_ingest.jira_replay.create_jira_ticket")
    def test_sweep_without_config_skips_everything(self, mock_create):
        self.add_queued_signup()
        outcome = sweep(self.conn, None, now=NOW)
        self.assertEqual(outcome, {"attempted": 0, "created": 0, "failed": 0, "dead": 0, "skipped": 1})
        mock_create.assert_not_called()

    @patch("lead_ingest.jira_replay.create_jira_ticket",
           side_effect=JiraApiError("500 boom"))
    def test_failure_backs_off_and_persists_error(self, mock_create):
        _, queue_id = self.add_queued_signup()
        outcome = sweep(self.conn, CONFIG, now=NOW)
        self.assertEqual(outcome["failed"], 1)
        row = self.conn.execute("SELECT * FROM jira_queue WHERE id = ?", (queue_id,)).fetchone()
        self.assertEqual(row["attempts"], 1)
        self.assertEqual(row["error_message"], "500 boom")
        self.assertEqual(row["status"], "pending")
        self.assertIsNotNone(row["next_attempt_at"])
        # Not due immediately after failing.
        self.assertEqual(due_items(self.conn, NOW), [])
        # But due again after the backoff window.
        later = NOW + timedelta(seconds=MAX_DELAY_SECONDS * 2)
        self.assertEqual(len(due_items(self.conn, later)), 1)

    @patch("lead_ingest.jira_replay.create_jira_ticket",
           side_effect=JiraApiError("permanent failure"))
    def test_dead_letter_after_max_attempts(self, mock_create):
        _, queue_id = self.add_queued_signup()
        now = NOW
        for expected_attempt in range(1, MAX_ATTEMPTS + 1):
            outcome = sweep(self.conn, CONFIG, now=now)
            self.assertEqual(outcome["attempted"], 1)
            now += timedelta(hours=2)  # always past any backoff
        row = self.conn.execute("SELECT * FROM jira_queue WHERE id = ?", (queue_id,)).fetchone()
        self.assertEqual(row["status"], "dead")
        self.assertEqual(row["attempts"], MAX_ATTEMPTS)
        self.assertEqual(row["error_message"], "permanent failure")
        # Dead rows are excluded from all future sweeps.
        outcome = sweep(self.conn, CONFIG, now=now + timedelta(days=365))
        self.assertEqual(outcome["attempted"], 0)
        self.assertEqual(mock_create.call_count, MAX_ATTEMPTS)

    @patch("lead_ingest.jira_replay.create_jira_ticket")
    def test_idempotency_after_ambiguous_failure(self, mock_create):
        """Ticket created remotely but response lost -> replay must NOT
        create a duplicate; the existing jira_tickets row short-circuits."""
        signup_id, _ = self.add_queued_signup()

        # First attempt: create succeeds remotely, then we "time out"
        # before recording -> simulate by recording the ticket row but
        # leaving the queue row pending (the ambiguous state).
        self.conn.execute(
            "INSERT INTO jira_tickets (signup_id, ticket_key, jira_issue_url, created_at) "
            "VALUES (?, 'BDS-99', 'https://x/browse/BDS-99', '2026-07-31T11:00:00+00:00')",
            (signup_id,),
        )
        self.conn.commit()

        outcome = sweep(self.conn, CONFIG, now=NOW)
        self.assertEqual(outcome["created"], 1)
        mock_create.assert_not_called()  # NO duplicate API call
        entry = db.get_jira_queue_entry(self.conn, signup_id)
        self.assertEqual(entry["status"], "created")
        self.assertEqual(entry["ticket_key"], "BDS-99")

    def test_queue_item_carries_stable_idempotency_key(self):
        signup_id, queue_id = self.add_queued_signup()
        row = self.conn.execute("SELECT * FROM jira_queue WHERE id = ?", (queue_id,)).fetchone()
        self.assertEqual(row["idempotency_key"], f"signup-{signup_id}")
        # Re-enqueueing the same signup updates, never duplicates.
        again = db.queue_jira_ticket(self.conn, signup_id, "again")
        self.assertEqual(again, queue_id)
        count = self.conn.execute(
            "SELECT COUNT(*) AS c FROM jira_queue WHERE signup_id = ?", (signup_id,)
        ).fetchone()["c"]
        self.assertEqual(count, 1)


class StatsTests(ReplayTestBase):
    @patch("lead_ingest.jira_replay.create_jira_ticket", return_value="BDS-7")
    def test_queue_stats_counts(self, mock_create):
        s1, _ = self.add_queued_signup("one@example.com")
        self.add_queued_signup("two@example.com", error="dead soon")
        self.conn.execute(
            "UPDATE jira_queue SET status = 'dead' WHERE error_message = 'dead soon'"
        )
        self.conn.commit()
        stats = queue_stats(self.conn)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["dead"], 1)
        self.assertEqual(stats["created"], 0)

        outcome = sweep(self.conn, CONFIG, now=NOW)
        stats = queue_stats(self.conn, outcome)
        self.assertEqual(stats["created"], 1)
        self.assertEqual(stats["pending"], 0)
        self.assertEqual(stats["last_outcome"]["created"], 1)


class DaemonTests(ReplayTestBase):
    @patch("lead_ingest.jira_replay.create_jira_ticket", return_value="BDS-1")
    def test_daemon_ticks_and_exits_cleanly(self, mock_create):
        self.add_queued_signup()
        stop = threading.Event()
        sweeps_done = []

        real_sweep = sweep

        def counting_sweep(conn, config, now=None):
            outcome = real_sweep(conn, config, now)
            sweeps_done.append(outcome)
            if len(sweeps_done) >= 2:
                stop.set()
            return outcome

        with patch("lead_ingest.jira_replay.sweep", counting_sweep):
            run_daemon(lambda: self._fresh_conn(), CONFIG,
                       interval_seconds=0.01, stop_event=stop)
        self.assertGreaterEqual(len(sweeps_done), 2)
        self.assertEqual(sweeps_done[0]["created"], 1)

    def _fresh_conn(self):
        # Daemon opens a fresh conn per sweep; share the in-memory DB.
        return _SharedConn(self.conn)


class _SharedConn:
    """sqlite3 connections are thread-bound; tests share one in-memory DB
    via this shim so the daemon's 'fresh connection' is the same DB."""

    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        pass


if __name__ == "__main__":
    unittest.main()
