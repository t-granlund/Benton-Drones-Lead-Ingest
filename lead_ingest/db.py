from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from lead_ingest.geocoding import MockGeocoder
from lead_ingest.models import (
    CONSENT_TEXT,
    CONSENT_VERSION,
    SIGNATURE_DISCLAIMER,
    WAIVER_TEXT,
    WAIVER_VERSION,
    LeadPoint,
    SignupInput,
    utc_now_iso,
)
from lead_ingest.validation import validate_signup
from lead_ingest.db_compat import IS_POSTGRES, pg_connect

DEFAULT_DB_PATH = Path(os.environ.get("DEFAULT_DB_PATH", "data/lead_ingest.sqlite3"))

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT DEFAULT '',
    address_line1 TEXT NOT NULL,
    address_line2 TEXT DEFAULT '',
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    full_address TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    geocode_status TEXT NOT NULL DEFAULT 'pending',
    geocode_provider TEXT DEFAULT '',
    geocode_display_name TEXT DEFAULT '',
    campaign TEXT DEFAULT '',
    source TEXT DEFAULT '',
    variant_slug TEXT DEFAULT 'default',
    shopify_shop_domain TEXT DEFAULT '',
    shopify_customer_id TEXT DEFAULT '',
    shopify_page_url TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS consent_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signup_id INTEGER NOT NULL UNIQUE,
    consent_version TEXT NOT NULL,
    consent_text TEXT NOT NULL,
    accepted INTEGER NOT NULL,
    ip_address TEXT DEFAULT '',
    user_agent TEXT DEFAULT '',
    accepted_at TEXT NOT NULL,
    FOREIGN KEY (signup_id) REFERENCES signups(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS signatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signup_id INTEGER NOT NULL UNIQUE,
    full_name_typed TEXT NOT NULL,
    signature_disclaimer_text TEXT NOT NULL,
    waiver_version TEXT NOT NULL,
    waiver_text TEXT NOT NULL,
    ip_address TEXT DEFAULT '',
    user_agent TEXT DEFAULT '',
    signed_at TEXT NOT NULL,
    FOREIGN KEY (signup_id) REFERENCES signups(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS landing_page_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    subtitle TEXT DEFAULT '',
    cta_text TEXT NOT NULL,
    campaign TEXT DEFAULT '',
    source TEXT DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    center_lat REAL,
    center_lng REAL,
    radius_miles REAL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cluster_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER NOT NULL,
    signup_id INTEGER NOT NULL,
    distance_from_center_miles REAL,
    UNIQUE(cluster_id, signup_id),
    FOREIGN KEY (cluster_id) REFERENCES clusters(id) ON DELETE CASCADE,
    FOREIGN KEY (signup_id) REFERENCES signups(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS jira_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signup_id INTEGER NOT NULL,
    ticket_key TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    attempted_at TEXT,
    error_message TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (signup_id) REFERENCES signups(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS jira_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signup_id INTEGER NOT NULL UNIQUE,
    ticket_key TEXT NOT NULL,
    jira_issue_url TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (signup_id) REFERENCES signups(id) ON DELETE CASCADE
);
"""


def _pg_schema() -> str:
    """Derive PostgreSQL DDL from the SQLite SCHEMA.

    Replaces AUTOINCREMENT with SERIAL and strips PRAGMA directives so the
    same schema definition serves both backends (DRY).
    """
    schema = SCHEMA.replace(
        "INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY"
    )
    lines = [
        line
        for line in schema.splitlines()
        if not line.strip().upper().startswith("PRAGMA")
    ]
    return "\n".join(lines)


_DEFAULT_VARIANT_VALUES = (
    "default",
    "Join Benton Drones Delivery Simulations",
    "Help us plan safe, local drone delivery simulation routes.",
    "Sign up for updates",
    "default",
    "local",
)


def _seed_default_variant(conn) -> None:
    """Insert the default landing-page variant idempotently."""
    if IS_POSTGRES:
        conn.execute(
            """
            INSERT INTO landing_page_variants
            (slug, title, subtitle, cta_text, campaign, source, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT (slug) DO NOTHING
            """,
            _DEFAULT_VARIANT_VALUES,
        )
    else:
        conn.execute(
            """
            INSERT OR IGNORE INTO landing_page_variants
            (slug, title, subtitle, cta_text, campaign, source, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            _DEFAULT_VARIANT_VALUES,
        )


def connect(path: Path | str = DEFAULT_DB_PATH):
    """Return a database connection.

    Uses PostgreSQL (via psycopg2) when ``DATABASE_URL`` is set, otherwise
    falls back to SQLite.
    """
    if IS_POSTGRES:
        return pg_connect()
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db(conn) -> None:
    conn.executescript(_pg_schema() if IS_POSTGRES else SCHEMA)
    ensure_signup_columns(conn)
    _seed_default_variant(conn)
    conn.commit()


def _existing_signup_columns(conn) -> set[str]:
    if IS_POSTGRES:
        rows = conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'signups'"
        ).fetchall()
        return {row["column_name"] for row in rows}
    return {row["name"] for row in conn.execute("PRAGMA table_info(signups)")}


def ensure_signup_columns(conn) -> None:
    """Add any signups columns introduced after the initial schema deploy.

    Lets the app start against older SQLite/Postgres databases without losing
    existing data. Columns are added with safe defaults.
    """
    desired = {
        "address_line2": "TEXT DEFAULT ''",
        "full_address": "TEXT NOT NULL DEFAULT ''",
        "latitude": "REAL",
        "longitude": "REAL",
        "geocode_status": "TEXT NOT NULL DEFAULT 'pending'",
        "geocode_provider": "TEXT DEFAULT ''",
        "geocode_display_name": "TEXT DEFAULT ''",
        "campaign": "TEXT DEFAULT ''",
        "source": "TEXT DEFAULT ''",
        "variant_slug": "TEXT DEFAULT 'default'",
        "shopify_shop_domain": "TEXT DEFAULT ''",
        "shopify_customer_id": "TEXT DEFAULT ''",
        "shopify_page_url": "TEXT DEFAULT ''",
        "notes": "TEXT DEFAULT ''",
    }
    existing = _existing_signup_columns(conn)
    for column, definition in desired.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE signups ADD COLUMN {column} {definition}")


def create_signup(
    conn,
    data: SignupInput,
    ip_address: str = "",
    user_agent: str = "",
    geocode: bool = True,
) -> int:
    validate_signup(data)
    now = utc_now_iso()
    result = MockGeocoder().geocode(data.full_address) if geocode else None

    with conn:
        cursor = conn.execute(
            """
            INSERT INTO signups (
                first_name, last_name, email, phone, address_line1, address_line2,
                city, state, postal_code, full_address, latitude, longitude,
                geocode_status, geocode_provider, geocode_display_name,
                campaign, source, variant_slug, shopify_shop_domain,
                shopify_customer_id, shopify_page_url, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.first_name.strip(),
                data.last_name.strip(),
                data.email.strip().lower(),
                data.phone.strip(),
                data.address_line1.strip(),
                data.address_line2.strip(),
                data.city.strip(),
                data.state.strip().upper(),
                data.postal_code.strip(),
                data.full_address,
                result.latitude if result else None,
                result.longitude if result else None,
                "success" if result else "pending",
                result.provider if result else "",
                result.display_name if result else "",
                data.campaign.strip(),
                data.source.strip(),
                data.variant_slug.strip() or "default",
                data.shopify_shop_domain.strip(),
                data.shopify_customer_id.strip(),
                data.shopify_page_url.strip(),
                data.notes.strip(),
                now,
                now,
            ),
        )
        signup_id = int(cursor.lastrowid)
        conn.execute(
            """
            INSERT INTO consent_records (
                signup_id, consent_version, consent_text, accepted,
                ip_address, user_agent, accepted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (signup_id, CONSENT_VERSION, CONSENT_TEXT, 1, ip_address, user_agent, now),
        )
        conn.execute(
            """
            INSERT INTO signatures (
                signup_id, full_name_typed, signature_disclaimer_text,
                waiver_version, waiver_text, ip_address, user_agent, signed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signup_id,
                data.typed_name.strip(),
                SIGNATURE_DISCLAIMER,
                WAIVER_VERSION,
                WAIVER_TEXT,
                ip_address,
                user_agent,
                now,
            ),
        )
    return signup_id


def list_signups(conn) -> list:
    return list(conn.execute("SELECT * FROM signups ORDER BY created_at DESC, id DESC"))


def get_variant(conn, slug: str):
    return conn.execute(
        "SELECT * FROM landing_page_variants WHERE slug = ? AND is_active = 1",
        (slug,),
    ).fetchone()


def get_signup(conn, signup_id: int):
    return conn.execute("SELECT * FROM signups WHERE id = ?", (signup_id,)).fetchone()


def get_consent_record(conn, signup_id: int):
    return conn.execute(
        "SELECT * FROM consent_records WHERE signup_id = ?", (signup_id,)
    ).fetchone()


def get_signature_record(conn, signup_id: int):
    return conn.execute(
        "SELECT * FROM signatures WHERE signup_id = ?", (signup_id,)
    ).fetchone()


def analytics_summary(conn) -> dict:
    total = conn.execute("SELECT COUNT(*) AS count FROM signups").fetchone()["count"]
    if IS_POSTGRES:
        today = conn.execute(
            "SELECT COUNT(*) AS count FROM signups WHERE created_at::date = CURRENT_DATE"
        ).fetchone()["count"]
        week = conn.execute(
            "SELECT COUNT(*) AS count FROM signups WHERE created_at::timestamptz >= NOW() - INTERVAL '7 days'"
        ).fetchone()["count"]
    else:
        today = conn.execute(
            "SELECT COUNT(*) AS count FROM signups WHERE DATE(created_at) = DATE('now', 'localtime')"
        ).fetchone()["count"]
        week = conn.execute(
            "SELECT COUNT(*) AS count FROM signups WHERE created_at >= datetime('now', '-7 days', 'localtime')"
        ).fetchone()["count"]
    pending_geocodes = conn.execute(
        "SELECT COUNT(*) AS count FROM signups WHERE geocode_status = 'pending'"
    ).fetchone()["count"]
    by_source = {
        row["source"]: row["count"]
        for row in conn.execute(
            "SELECT source, COUNT(*) AS count FROM signups GROUP BY source ORDER BY count DESC"
        )
    }
    by_campaign = {
        row["campaign"]: row["count"]
        for row in conn.execute(
            "SELECT campaign, COUNT(*) AS count FROM signups GROUP BY campaign ORDER BY count DESC"
        )
    }
    by_variant = {
        row["variant_slug"]: row["count"]
        for row in conn.execute(
            "SELECT variant_slug, COUNT(*) AS count FROM signups GROUP BY variant_slug ORDER BY count DESC"
        )
    }
    return {
        "total": total,
        "today": today,
        "this_week": week,
        "pending_geocodes": pending_geocodes,
        "by_source": by_source,
        "by_campaign": by_campaign,
        "by_variant": by_variant,
    }


def recent_leads(conn, limit: int = 50) -> list:
    return list(
        conn.execute(
            "SELECT * FROM signups ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        )
    )


def get_export_rows(conn) -> list:
    return list(
        conn.execute(
            """
            SELECT
                s.*,
                cr.consent_version AS consent_version,
                cr.accepted_at AS consent_accepted_at,
                sig.full_name_typed AS signed_name,
                sig.signed_at AS signed_at,
                sig.waiver_version AS waiver_version,
                sig.signature_disclaimer_text AS signature_disclaimer
            FROM signups s
            LEFT JOIN consent_records cr ON cr.signup_id = s.id
            LEFT JOIN signatures sig ON sig.signup_id = s.id
            ORDER BY s.created_at DESC, s.id DESC
            """
        )
    )


def queue_jira_ticket(conn, signup_id: int, error_message: str = "") -> int:
    """Queue a signup for later JIRA ticket creation.

    Called when JIRA config is missing or a creation attempt fails.
    Returns the queue row id.
    """
    now = utc_now_iso()
    cursor = conn.execute(
        """
        INSERT INTO jira_queue (signup_id, ticket_key, status, attempted_at, error_message, created_at)
        VALUES (?, '', 'pending', ?, ?, ?)
        """,
        (signup_id, now, error_message, now),
    )
    conn.commit()
    return int(cursor.lastrowid)


def mark_jira_ticket_created(
    conn,
    signup_id: int,
    ticket_key: str,
    jira_issue_url: str = "",
) -> None:
    """Record that a JIRA ticket was successfully created for a signup."""
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO jira_tickets (signup_id, ticket_key, jira_issue_url, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (signup_id) DO UPDATE SET ticket_key = ?, jira_issue_url = ?, created_at = ?
        """,
        (signup_id, ticket_key, jira_issue_url, now, ticket_key, jira_issue_url, now),
    )
    conn.execute(
        """
        UPDATE jira_queue SET status = 'created', ticket_key = ?, attempted_at = ?, error_message = ''
        WHERE signup_id = ? AND status = 'pending'
        """,
        (ticket_key, now, signup_id),
    )
    conn.commit()


def get_jira_ticket(conn, signup_id: int):
    """Return the jira_tickets row for a signup, or None."""
    return conn.execute(
        "SELECT * FROM jira_tickets WHERE signup_id = ?", (signup_id,)
    ).fetchone()


def get_jira_queue_entry(conn, signup_id: int):
    """Return the most recent jira_queue row for a signup, or None."""
    return conn.execute(
        "SELECT * FROM jira_queue WHERE signup_id = ? ORDER BY id DESC LIMIT 1",
        (signup_id,),
    ).fetchone()


def list_lead_points(conn) -> list[LeadPoint]:
    rows = conn.execute(
        """
        SELECT id, first_name, last_name, latitude, longitude
        FROM signups
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY id
        """
    ).fetchall()
    return [
        LeadPoint(row["id"], f"{row['first_name']} {row['last_name']}", row["latitude"], row["longitude"])
        for row in rows
    ]
