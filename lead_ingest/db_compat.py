"""PostgreSQL compatibility layer for dual SQLite/Postgres support.

When the ``DATABASE_URL`` environment variable is set, the app connects to
PostgreSQL (e.g. Neon) via psycopg2.  Otherwise it falls back to the
built-in sqlite3 engine.  This module wraps a psycopg2 connection so it
mimics the :class:`sqlite3.Connection` interface used throughout ``db.py``:

- ``conn.execute(sql, params)`` returns a cursor-like object
- cursor ``lastrowid`` works (via ``RETURNING id``)
- ``fetchone`` / ``fetchall`` return dict-like rows (``RealDictCursor``)
- ``with conn:`` acts as a transaction context manager
- ``conn.executescript(sql)`` splits and runs multi-statement SQL
- ``?`` placeholders are normalised to ``%s`` automatically

psycopg2 is imported lazily so the SQLite-only path has no hard dependency.
"""
from __future__ import annotations

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
IS_POSTGRES = bool(DATABASE_URL)


class _PgCursor:
    """Thin wrapper that mimics :class:`sqlite3.Cursor`."""

    def __init__(self, cursor, lastrowid=None):
        self._cursor = cursor
        self._lastrowid = lastrowid

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=1):
        return self._cursor.fetchmany(size)

    def __iter__(self):
        return iter(self._cursor)

    def close(self):
        self._cursor.close()


class _PgConnection:
    """Wraps a psycopg2 connection to mimic :class:`sqlite3.Connection`.

    The rest of ``db.py`` calls ``conn.execute(sql, params)`` with ``?``
    placeholders and reads ``row["col"]`` just like sqlite3.Row.  This
    wrapper translates those conventions to psycopg2 equivalents so the
    same calling code works against either database.
    """

    def __init__(self, conn, cursor_factory=None):
        self._conn = conn
        self._cursor_factory = cursor_factory
        self._conn.autocommit = False

    # ------------------------------------------------------------------
    # sqlite3-compatible execute
    # ------------------------------------------------------------------

    def execute(self, sql, params=()):
        sql = sql.replace("?", "%s")
        stripped = sql.strip()
        is_insert = stripped.upper().startswith("INSERT")
        if is_insert and "RETURNING" not in sql.upper():
            sql = sql.rstrip().rstrip(";") + " RETURNING id"

        cursor = self._conn.cursor(cursor_factory=self._cursor_factory)
        cursor.execute(sql, params)

        lastrowid = None
        if is_insert:
            row = cursor.fetchone()
            if row is not None and "id" in row:
                lastrowid = row["id"]

        return _PgCursor(cursor, lastrowid)

    def executescript(self, sql):
        """Run multi-statement SQL (sqlite3.Connection.executescript equivalent).

        Splits on semicolons, skips empty fragments and PRAGMA directives
        (Postgres has no PRAGMA).
        """
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if not stmt or stmt.upper().startswith("PRAGMA"):
                continue
            self.execute(stmt)

    # ------------------------------------------------------------------
    # Transaction / lifecycle
    # ------------------------------------------------------------------

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._conn.rollback()
        else:
            self._conn.commit()
        return False


def pg_connect():
    """Create and return a :class:`_PgConnection` wrapping a psycopg2 connection."""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(DATABASE_URL)
    return _PgConnection(conn, RealDictCursor)
