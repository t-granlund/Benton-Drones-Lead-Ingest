"""Tests for JIRA integration: config, payload building, and DB queue logic."""
import os
import sqlite3
import unittest
from unittest.mock import patch

from lead_ingest.db import (
    create_signup,
    get_jira_queue_entry,
    get_jira_ticket,
    init_db,
    mark_jira_ticket_created,
    queue_jira_ticket,
)
from lead_ingest.jira import (
    JiraApiError,
    JiraConfigError,
    build_jira_payload,
    jira_config_from_env,
    jira_issue_url,
)
from lead_ingest.models import SignupInput


class JiraConfigTests(unittest.TestCase):
    def test_config_returns_none_when_missing(self):
        env = {
            "JIRA_BASE_URL": "",
            "JIRA_USER_EMAIL": "",
            "JIRA_API_TOKEN": "",
            "JIRA_PROJECT_KEY": "",
        }
        with patch.dict(os.environ, env, clear=False):
            self.assertIsNone(jira_config_from_env())

    def test_config_returns_none_when_partial(self):
        env = {
            "JIRA_BASE_URL": "https://test.atlassian.net",
            "JIRA_USER_EMAIL": "",
            "JIRA_API_TOKEN": "token",
            "JIRA_PROJECT_KEY": "BDS",
        }
        with patch.dict(os.environ, env, clear=False):
            self.assertIsNone(jira_config_from_env())

    def test_config_returns_dict_when_complete(self):
        env = {
            "JIRA_BASE_URL": "https://test.atlassian.net",
            "JIRA_USER_EMAIL": "user@test.com",
            "JIRA_API_TOKEN": "token123",
            "JIRA_PROJECT_KEY": "BDS",
            "JIRA_ISSUE_TYPE": "Story",
        }
        with patch.dict(os.environ, env, clear=False):
            config = jira_config_from_env()
        self.assertIsNotNone(config)
        self.assertEqual(config["base_url"], "https://test.atlassian.net")
        self.assertEqual(config["user_email"], "user@test.com")
        self.assertEqual(config["api_token"], "token123")
        self.assertEqual(config["project_key"], "BDS")
        self.assertEqual(config["issue_type"], "Story")

    def test_config_defaults_issue_type_to_task(self):
        env = {
            "JIRA_BASE_URL": "https://test.atlassian.net",
            "JIRA_USER_EMAIL": "user@test.com",
            "JIRA_API_TOKEN": "token123",
            "JIRA_PROJECT_KEY": "BDS",
        }
        with patch.dict(os.environ, env, clear=False):
            config = jira_config_from_env()
        self.assertEqual(config["issue_type"], "Task")

    def test_config_strips_trailing_slash(self):
        env = {
            "JIRA_BASE_URL": "https://test.atlassian.net/",
            "JIRA_USER_EMAIL": "user@test.com",
            "JIRA_API_TOKEN": "token123",
            "JIRA_PROJECT_KEY": "BDS",
        }
        with patch.dict(os.environ, env, clear=False):
            config = jira_config_from_env()
        self.assertEqual(config["base_url"], "https://test.atlassian.net")


class JiraPayloadTests(unittest.TestCase):
    def _signup_row(self):
        return {
            "id": 42,
            "first_name": "Jane",
            "last_name": "Pilot",
            "email": "jane@example.com",
            "phone": "555-1234",
            "full_address": "100 Flight Path, Bentonville, AR, 72712",
            "campaign": "spring",
            "source": "local",
            "variant_slug": "default",
            "created_at": "2026-07-15T12:00:00+00:00",
            "notes": "Needs roof inspection",
        }

    def _signature_row(self):
        return {
            "full_name_typed": "Jane Pilot",
            "signed_at": "2026-07-15T12:01:00+00:00",
            "waiver_version": "2026-07-15.placeholder.v1",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
        }

    def _consent_row(self):
        return {
            "consent_version": "2026-07-06.v1",
            "accepted_at": "2026-07-15T12:00:30+00:00",
            "ip_address": "192.168.1.1",
        }

    def test_payload_has_required_fields(self):
        payload = build_jira_payload(
            self._signup_row(), self._signature_row(), self._consent_row(),
            {"project_key": "BDS", "issue_type": "Task"},
        )
        fields = payload["fields"]
        self.assertEqual(fields["project"]["key"], "BDS")
        self.assertEqual(fields["issuetype"]["name"], "Task")
        self.assertIn("Jane Pilot", fields["summary"])
        self.assertIn("jane@example.com", fields["description"])
        self.assertIn("100 Flight Path", fields["description"])
        self.assertIn("Jane Pilot", fields["description"])
        self.assertIn("Needs roof inspection", fields["description"])

    def test_payload_defaults_project_key(self):
        payload = build_jira_payload(self._signup_row())
        self.assertEqual(payload["fields"]["project"]["key"], "BDS")

    def test_payload_handles_none_rows(self):
        payload = build_jira_payload(self._signup_row(), None, None)
        self.assertIn("Lead:", payload["fields"]["description"])
        self.assertIn("-", payload["fields"]["description"])

    def test_jira_issue_url(self):
        url = jira_issue_url(
            {"base_url": "https://test.atlassian.net"}, "BDS-42"
        )
        self.assertEqual(url, "https://test.atlassian.net/browse/BDS-42")


class JiraDbQueueTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def _create_signup(self):
        return create_signup(self.conn, SignupInput(
            first_name="Queue", last_name="Test",
            email="queue@example.com", phone="555-0000",
            address_line1="1 Drone Way", city="Bentonville",
            state="AR", postal_code="72712",
            consent_accepted=True, waiver_accepted=True,
            typed_name="Queue Test",
        ))

    def test_queue_jira_ticket_creates_pending_entry(self):
        signup_id = self._create_signup()
        queue_id = queue_jira_ticket(self.conn, signup_id, "config not set")
        self.assertGreater(queue_id, 0)
        entry = get_jira_queue_entry(self.conn, signup_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["signup_id"], signup_id)
        self.assertEqual(entry["status"], "pending")
        self.assertEqual(entry["error_message"], "config not set")
        self.assertEqual(entry["ticket_key"], "")

    def test_mark_jira_ticket_created_records_ticket(self):
        signup_id = self._create_signup()
        queue_jira_ticket(self.conn, signup_id, "config not set")
        mark_jira_ticket_created(
            self.conn, signup_id, "BDS-42", "https://test.atlassian.net/browse/BDS-42"
        )
        ticket = get_jira_ticket(self.conn, signup_id)
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket["ticket_key"], "BDS-42")
        self.assertEqual(ticket["jira_issue_url"], "https://test.atlassian.net/browse/BDS-42")

        # Queue entry should be updated to 'created'
        entry = get_jira_queue_entry(self.conn, signup_id)
        self.assertEqual(entry["status"], "created")
        self.assertEqual(entry["ticket_key"], "BDS-42")

    def test_mark_jira_ticket_created_is_idempotent(self):
        signup_id = self._create_signup()
        mark_jira_ticket_created(self.conn, signup_id, "BDS-1")
        mark_jira_ticket_created(self.conn, signup_id, "BDS-2")
        ticket = get_jira_ticket(self.conn, signup_id)
        self.assertEqual(ticket["ticket_key"], "BDS-2")

    def test_get_jira_ticket_returns_none_for_missing(self):
        self.assertIsNone(get_jira_ticket(self.conn, 99999))

    def test_get_jira_queue_entry_returns_none_for_missing(self):
        self.assertIsNone(get_jira_queue_entry(self.conn, 99999))


if __name__ == "__main__":
    unittest.main()
