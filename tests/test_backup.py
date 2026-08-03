"""Tests for backups + monitoring scaffolding (G4).

Covers the DB-aware /healthz, the read-only verify_backup script, and
the recovery playbook's existence/content. No network; temp SQLite only.
"""
from __future__ import annotations

import io
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lead_ingest import db
from lead_ingest.models import SignupInput
from lead_ingest.server import Handler
from scripts.verify_backup import main as verify_main, verify

PLAYBOOK = Path(__file__).resolve().parent.parent / "docs" / "backup-recovery-playbook.md"


def _signup_input():
    return SignupInput(
        first_name="Test", last_name="Pilot", email="pilot@example.com", phone="",
        address_line1="1 Drone Way", city="Bentonville", state="AR",
        postal_code="72712", consent_accepted=True, waiver_accepted=True,
        typed_name="Test Pilot",
    )


class HealthzTests(unittest.TestCase):
    """Handler-level tests of handle_healthz (DB-aware, unauthenticated)."""

    def _handler(self):
        handler = Handler.__new__(Handler)
        handler.respond_text = MagicMock()
        return handler

    def test_healthz_200_when_app_and_db_healthy(self):
        handler = self._handler()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "ok.sqlite3")
            conn = db.connect(db_path)
            db.init_db(conn)
            conn.close()
            with patch("lead_ingest.server.DEFAULT_DB_PATH", db_path):
                handler.handle_healthz()
        args, _ = handler.respond_text.call_args
        payload, content_type, status = args
        self.assertEqual(status, 200)
        self.assertIn('"db": "ok"', payload)
        self.assertEqual(content_type, "application/json")

    def test_healthz_503_when_db_unreachable(self):
        handler = self._handler()
        with patch("lead_ingest.server.connect", side_effect=RuntimeError("db down")):
            handler.handle_healthz()
        args, _ = handler.respond_text.call_args
        payload, _, status = args
        self.assertEqual(status, 503)
        self.assertIn('"db": "unreachable"', payload)
        self.assertIn('"status": "error"', payload)

    def test_healthz_is_read_only_no_init_db(self):
        """A health check must NOT run migrations/DDL (init_db)."""
        handler = self._handler()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "ok.sqlite3")
            conn = db.connect(db_path)
            db.init_db(conn)
            conn.close()
            with patch("lead_ingest.server.DEFAULT_DB_PATH", db_path), \
                 patch("lead_ingest.server.init_db") as mock_init:
                handler.handle_healthz()
        mock_init.assert_not_called()


class VerifyBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = os.path.join(self.tmp.name, "backup.sqlite3")
        conn = db.connect(self.db_path)
        db.init_db(conn)
        db.create_signup(conn, _signup_input(), geocode=False)
        conn.close()

    def test_verify_reports_counts_readonly(self):
        out = io.StringIO()
        code = verify(self.db_path, out=out)
        report = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("REACHABLE", report)
        self.assertIn("signups", report)
        for table in ("signatures", "consent_records", "jira_queue",
                      "email_queue", "geocode_cache", "rate_limit_buckets"):
            self.assertIn(table, report)
        self.assertIn("1 rows", report)  # the one signup
        self.assertIn("VERIFIED read-only", report)

    def test_verify_sqlite_opened_read_only(self):
        """The file must be opened mode=ro -- a write must be impossible."""
        import scripts.verify_backup as vb

        real_connect = sqlite3.connect
        seen = {}

        def spy_connect(*args, **kwargs):
            seen["args"] = args
            seen["kwargs"] = kwargs
            return real_connect(*args, **kwargs)

        with patch.object(vb.sqlite3, "connect", spy_connect):
            verify(self.db_path, out=io.StringIO())
        self.assertTrue(seen["kwargs"].get("uri"))
        self.assertIn("mode=ro", seen["args"][0])

    def test_verify_missing_file_exits_nonzero(self):
        out = io.StringIO()
        code = verify(os.path.join(self.tmp.name, "nope.sqlite3"), out=out)
        self.assertEqual(code, 1)
        self.assertIn("not found", out.getvalue().lower())

    def test_verify_unreachable_db_exits_nonzero(self):
        out = io.StringIO()
        with patch("scripts.verify_backup.sqlite3.connect",
                   side_effect=sqlite3.OperationalError("unable to open")):
            code = verify(self.db_path, out=out)
        self.assertEqual(code, 1)
        self.assertIn("UNREACHABLE", out.getvalue())

    def test_verify_no_target_exits_nonzero(self):
        with patch.dict(os.environ, {}, clear=True):
            out = io.StringIO()
            code = verify(None, out=out)
        self.assertEqual(code, 1)

    def test_main_entrypoint(self):
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            out_code = verify_main(["--db", self.db_path])
        self.assertEqual(out_code, 0)


class PlaybookTests(unittest.TestCase):
    def test_playbook_exists_with_restore_steps(self):
        self.assertTrue(PLAYBOOK.exists(), "docs/backup-recovery-playbook.md missing")
        text = PLAYBOOK.read_text().lower()
        for phrase in (
            "point-in-time",
            "branch restore",
            "database_url",
            "uptime",
            "/healthz",
            "alert",
            "render",
            "neon",
        ):
            self.assertIn(phrase, text, f"playbook missing key phrase: {phrase}")

    def test_playbook_has_human_placeholders(self):
        text = PLAYBOOK.read_text()
        self.assertIn("<<HUMAN:", text)
        # Placeholders for the console-specific bits the human must fill in.
        self.assertGreaterEqual(text.count("<<HUMAN:"), 5)


if __name__ == "__main__":
    unittest.main()
