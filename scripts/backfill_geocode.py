"""Backfill geocodes for stored signups.

Finds signups with geocode_status 'pending' or 'unresolved', geocodes
them via the live chained (Census -> Nominatim) + DB-cached geocoder,
and updates each row. Rate-limited by Nominatim's politeness throttle.

Usage::

    python -m scripts.backfill_geocode --live [--db path/to.sqlite3]

Network is ONLY touched when ``--live`` is passed (or
``GEOCODER_MODE=live`` is set). Without ``--live`` the script does a
dry run: it lists what would be geocoded and writes NOTHING (so mock
coordinates can never poison a real database). Idempotent: rows
already resolved are skipped, and cached lookups never repeat network
calls.
"""
from __future__ import annotations

import argparse
import os
import sys

from lead_ingest import db
from lead_ingest.geocoding import CachedGeocoder


def backfill(conn, geocoder=None, verbose: bool = True) -> dict:
    """Geocode every pending/unresolved signup. Returns counts.

    Defaults to the live cached chained geocoder; tests inject a fake.
    """
    if geocoder is None:
        geocoder = CachedGeocoder(conn)
    rows = db.list_geocode_pending(conn)
    counts = {"attempted": 0, "resolved": 0, "unresolved": 0}
    for row in rows:
        counts["attempted"] += 1
        result = geocoder.geocode(row["full_address"])
        db.update_signup_geocode(conn, row["id"], result)
        if result.resolved:
            counts["resolved"] += 1
        else:
            counts["unresolved"] += 1
        if verbose:
            print(
                f"  signup {row['id']}: {result.provider} "
                f"({'resolved' if result.resolved else 'unresolved'})"
            )
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--live",
        action="store_true",
        default=os.environ.get("GEOCODER_MODE", "").strip().lower() == "live",
        help="Hit the real Census/Nominatim providers (default: mock, offline).",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="SQLite path (defaults to DEFAULT_DB_PATH; Postgres via DATABASE_URL).",
    )
    args = parser.parse_args(argv)

    conn = db.connect(args.db) if args.db else db.connect()
    try:
        db.init_db(conn)
        if not args.live:
            # Dry run: never touch the network, never write mock coords to a
            # real database. Real geocoding requires --live (or GEOCODER_MODE=live).
            pending = db.list_geocode_pending(conn)
            print(
                f"DRY RUN (offline): {len(pending)} signup(s) pending/unresolved. "
                "Pass --live (or set GEOCODER_MODE=live) to geocode for real."
            )
            for row in pending:
                print(f"  signup {row['id']}: {row['full_address']}")
            return 0
        print("Backfilling geocodes LIVE (Census -> Nominatim, cached)...")
        counts = backfill(conn)
        print(
            f"Done: {counts['attempted']} attempted, "
            f"{counts['resolved']} resolved, {counts['unresolved']} unresolved."
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
