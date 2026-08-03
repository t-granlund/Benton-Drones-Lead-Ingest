"""Read-only backup/restore verification for Benton Lead-Ingest (G4).

Confirms a target database is reachable and reports row counts for the
key tables -- spot a broken or EMPTY restore target before it matters.
Run it against a Neon branch/PITR restore (via DATABASE_URL) or a local
SQLite file BEFORE pointing the app at it.

STRICTLY READ-ONLY: only SELECTs. No DDL, no DML, no migrations, no
init_db. On SQLite it even opens the file with ``mode=ro`` so a write
is impossible; if that ever fails, the script errors out rather than
risk a write.

Usage::

    python -m scripts.verify_backup --db path/to/backup.sqlite3
    DATABASE_URL=postgres://... python -m scripts.verify_backup

Exit code: 0 = reachable (report printed), 1 = unreachable / unreadable.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

# Canonical application tables a healthy restore must contain.
# (consent_records is the app's real table name; the goal doc says
# "consents" -- we check the actual schema.)
TABLES = (
    "signups",
    "signatures",
    "consent_records",
    "jira_queue",
    "email_queue",
    "geocode_cache",
    "rate_limit_buckets",
)


def _existing_tables(conn) -> set[str]:
    """Table names present in the target DB (read-only catalog query)."""
    if os.environ.get("DATABASE_URL", "").strip():
        rows = conn.execute(
            "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
        ).fetchall()
        return {row["tablename"] for row in rows}
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    return {row["name"] for row in rows}


def verify(target: str | None = None, out=sys.stdout) -> int:
    """Connect read-only and report reachability + table counts.

    Returns process exit code: 0 reachable, 1 unreachable/unreadable.
    """
    database_url = os.environ.get("DATABASE_URL", "").strip()
    conn = None
    try:
        if database_url:
            # Postgres path (Neon). Read-only TRANSACTION so even a buggy
            # statement cannot persist anything.
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            conn.set_session(readonly=True, autocommit=True)
            source = f"Postgres (DATABASE_URL host={database_url.split('@')[-1]})"
        else:
            if not target:
                print("ERROR: no target. Pass --db <sqlite path> or set DATABASE_URL.",
                      file=out)
                return 1
            if not os.path.exists(target):
                print(f"ERROR: SQLite file not found: {target}", file=out)
                return 1
            # Open the file READ-ONLY at the VFS level -- a write is impossible.
            uri = f"file:{os.path.abspath(target)}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            conn.row_factory = sqlite3.Row
            source = f"SQLite file {target} (opened mode=ro)"

        conn.execute("SELECT 1").fetchone()
        print(f"REACHABLE: {source}", file=out)

        existing = _existing_tables(conn)
        missing = [t for t in TABLES if t not in existing]
        print("\nTable counts:", file=out)
        for table in TABLES:
            if table in existing:
                count = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
                print(f"  {table:20s} {count:>6} rows", file=out)
            else:
                print(f"  {table:20s} MISSING", file=out)

        if missing:
            print(f"\nWARNING: missing tables: {', '.join(missing)} "
                  "(restore target predates these features or is damaged)", file=out)
        if "signups" in existing and not missing:
            total = conn.execute("SELECT COUNT(*) AS c FROM signups").fetchone()["c"]
            if total == 0:
                print("\nWARNING: signups table is EMPTY -- this looks like a blank "
                      "or pre-data restore target.", file=out)
        print("\nVERIFIED read-only (no writes performed).", file=out)
        return 0
    except Exception as exc:
        print(f"UNREACHABLE: {exc}", file=out)
        return 1
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only backup/restore verification (reachability + table counts)."
    )
    parser.add_argument("--db", default=None,
                        help="SQLite file path (ignored when DATABASE_URL is set).")
    args = parser.parse_args(argv)
    return verify(args.db)


if __name__ == "__main__":
    sys.exit(main())
