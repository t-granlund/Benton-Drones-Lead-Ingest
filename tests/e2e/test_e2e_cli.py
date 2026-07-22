"""E2E: CLI maintenance scripts.

Covers: scripts/init_db.py initialises a SQLite database (schema + tables) and
prints a confirmation.  Run as a subprocess with cwd in a temp dir so the
relative DEFAULT_DB_PATH resolves there (no real data/ touched).
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_DB = REPO_ROOT / "scripts" / "init_db.py"


class InitDbCliTests(unittest.TestCase):

    def setUp(self):
        self._cwd = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._cwd.cleanup()

    def test_init_db_creates_database_file(self):
        env = {**os.environ}
        env.pop("DATABASE_URL", None)  # force the SQLite engine
        result = subprocess.run(
            [sys.executable, str(INIT_DB)],
            cwd=self._cwd.name,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0,
                         f"init_db failed: {result.stderr}")
        self.assertIn("Initialized database", result.stdout)

        db_file = Path(self._cwd.name) / "data" / "lead_ingest.sqlite3"
        self.assertTrue(db_file.exists(), "database file was not created")

    def test_init_db_creates_required_tables(self):
        env = {**os.environ}
        env.pop("DATABASE_URL", None)
        subprocess.run(
            [sys.executable, str(INIT_DB)],
            cwd=self._cwd.name, env=env,
            capture_output=True, text=True, timeout=30,
        )
        db_file = Path(self._cwd.name) / "data" / "lead_ingest.sqlite3"
        conn = sqlite3.connect(str(db_file))
        try:
            tables = {
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        finally:
            conn.close()
        for required in ("signups", "consent_records"):
            self.assertIn(required, tables,
                          f"table {required} missing after init_db")


if __name__ == "__main__":
    unittest.main()
