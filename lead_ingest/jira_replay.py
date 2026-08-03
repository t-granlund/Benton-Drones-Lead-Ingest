"""JIRA queue replay worker (G6).

Replays queued JIRA ticket creations until they succeed or dead-letter.
All state lives in the existing ``jira_queue`` / ``jira_tickets`` tables
-- no Redis, no new services, stdlib only.

Pieces:

- :func:`next_delay_seconds` -- pure exponential backoff with jitter,
  capped at :data:`MAX_DELAY_SECONDS`.
- :func:`due_items` -- pending queue rows whose next attempt is due.
- :func:`sweep` -- the on-read sweep: attempts every due item inline.
  Runs on the enqueue path and on admin status views, so replay makes
  progress even with no daemon. Idempotent: an existing ``jira_tickets``
  row (ambiguous failure: timeout AFTER a successful create) short-
  circuits the API call and just marks the queue row created.
- :func:`run_daemon` -- optional interval loop for production; exits
  cleanly on KeyboardInterrupt/SIGTERM.
- :func:`queue_stats` -- pending/created/dead counts + last outcome for
  admin/status display.

Delivery semantics: at-least-once with idempotency (never duplicates a
ticket after an ambiguous response).
"""
from __future__ import annotations

import logging
import random
import signal
import threading
from datetime import datetime, timedelta, timezone

from lead_ingest import db
from lead_ingest.jira import create_jira_ticket, jira_issue_url

logger = logging.getLogger("lead_ingest.jira_replay")

MAX_ATTEMPTS = 5
BASE_DELAY_SECONDS = 30.0
MAX_DELAY_SECONDS = 3600.0  # 1 hour cap, documented & testable


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def next_delay_seconds(
    attempts: int,
    base: float = BASE_DELAY_SECONDS,
    cap: float = MAX_DELAY_SECONDS,
    rand=random.random,
) -> float:
    """Exponential backoff with full jitter, capped.

    delay = min(cap, base * 2**attempts) * uniform(0.5, 1.0)
    """
    growth = base * (2 ** max(0, attempts))
    ceiling = min(cap, growth)
    return ceiling * (0.5 + 0.5 * rand())


def due_items(conn, now: datetime | None = None) -> list:
    """Pending queue rows whose next attempt time has arrived."""
    now = now or _utc_now()
    rows = conn.execute(
        "SELECT * FROM jira_queue WHERE status = 'pending' ORDER BY id"
    ).fetchall()
    due = []
    for row in rows:
        nxt = row["next_attempt_at"]
        if not nxt or _parse(nxt) <= now:
            due.append(row)
    return due


def _fail_item(conn, queue_id: int, attempts: int, error: str, now: datetime) -> None:
    """Record a failed attempt: backoff, or dead-letter past max attempts."""
    if attempts >= MAX_ATTEMPTS:
        conn.execute(
            "UPDATE jira_queue SET status = 'dead', attempts = ?, attempted_at = ?, "
            "error_message = ?, next_attempt_at = NULL WHERE id = ?",
            (attempts, _iso(now), error, queue_id),
        )
        logger.error("JIRA queue item %s dead-lettered after %d attempts: %s",
                     queue_id, attempts, error)
    else:
        delay = next_delay_seconds(attempts)
        conn.execute(
            "UPDATE jira_queue SET attempts = ?, attempted_at = ?, error_message = ?, "
            "next_attempt_at = ? WHERE id = ?",
            (attempts, _iso(now), error, _iso(now + timedelta(seconds=delay)), queue_id),
        )
    conn.commit()


def sweep(conn, config: dict, now: datetime | None = None) -> dict:
    """Attempt every due queue item inline. Returns an outcome summary.

    ``config`` is the JIRA config dict (from ``jira_config_from_env()``);
    if falsy, the sweep short-circuits (nothing can succeed without it).
    """
    now = now or _utc_now()
    outcome = {"attempted": 0, "created": 0, "failed": 0, "dead": 0, "skipped": 0}
    if not config:
        outcome["skipped"] = len(due_items(conn, now))
        return outcome

    for item in due_items(conn, now):
        outcome["attempted"] += 1
        signup_id = item["signup_id"]

        # Idempotency: a prior attempt may have created the ticket but
        # timed out before we recorded it. Never create a duplicate.
        existing = db.get_jira_ticket(conn, signup_id)
        if existing is not None:
            db.mark_jira_ticket_created(
                conn, signup_id, existing["ticket_key"], existing["jira_issue_url"]
            )
            outcome["created"] += 1
            logger.info(
                "JIRA queue item %s: ticket %s already exists (idempotent skip)",
                item["id"], existing["ticket_key"],
            )
            continue

        attempts = int(item["attempts"] or 0) + 1
        try:
            signup_row = db.get_signup(conn, signup_id)
            consent_row = db.get_consent_record(conn, signup_id)
            signature_row = db.get_signature_record(conn, signup_id)
            ticket_key = create_jira_ticket(signup_row, signature_row, consent_row, config)
            url = jira_issue_url(config, ticket_key)
            db.mark_jira_ticket_created(conn, signup_id, ticket_key, url)
            outcome["created"] += 1
        except Exception as exc:  # never let one item kill the sweep
            _fail_item(conn, item["id"], attempts, str(exc), now)
            outcome["failed"] += 1
            if attempts >= MAX_ATTEMPTS:
                outcome["dead"] += 1
    return outcome


def queue_stats(conn, last_outcome: dict | None = None) -> dict:
    """Counts of pending/created/dead + last replay outcome (for admin)."""
    rows = conn.execute(
        "SELECT status, COUNT(*) AS count FROM jira_queue GROUP BY status"
    ).fetchall()
    counts = {row["status"]: row["count"] for row in rows}
    return {
        "pending": counts.get("pending", 0),
        "created": counts.get("created", 0),
        "dead": counts.get("dead", 0),
        "last_outcome": last_outcome or {},
    }


def run_daemon(
    db_connect,
    config,
    interval_seconds: float = 60.0,
    stop_event: threading.Event | None = None,
) -> None:
    """Loop the sweep on an interval until interrupted.

    ``db_connect`` is a zero-arg callable returning a fresh DB connection
    per sweep (sqlite3 connections are thread-bound). ``stop_event``
    (or SIGINT/SIGTERM) ends the loop cleanly.
    """
    stop = stop_event or threading.Event()

    def _handle_signal(signum, frame):  # pragma: no cover - signal path
        stop.set()

    old_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            old_handlers[sig] = signal.signal(sig, _handle_signal)
        except (ValueError, OSError):  # not in main thread (tests)
            pass

    logger.info("JIRA replay daemon started (interval=%ss)", interval_seconds)
    last = {}
    try:
        while not stop.is_set():
            conn = db_connect()
            try:
                db.init_db(conn)
                cfg = config() if callable(config) else config
                last = sweep(conn, cfg)
                if last.get("attempted"):
                    logger.info("JIRA replay sweep: %s", last)
            finally:
                conn.close()
            stop.wait(interval_seconds)
    except KeyboardInterrupt:
        pass
    finally:
        for sig, handler in old_handlers.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass
    logger.info("JIRA replay daemon stopped (last sweep: %s)", last)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: ``python -m lead_ingest.jira_replay [--interval N]``."""
    import argparse

    from lead_ingest.jira import jira_config_from_env

    parser = argparse.ArgumentParser(description="Replay the JIRA ticket queue.")
    parser.add_argument("--interval", type=float, default=60.0,
                        help="Seconds between sweeps (default 60).")
    parser.add_argument("--once", action="store_true",
                        help="Run a single sweep and exit (no daemon loop).")
    parser.add_argument("--db", default=None, help="SQLite path override.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    def _connect():
        return db.connect(args.db) if args.db else db.connect()

    if args.once:
        conn = _connect()
        try:
            db.init_db(conn)
            outcome = sweep(conn, jira_config_from_env())
            print(f"Sweep outcome: {outcome}")
        finally:
            conn.close()
        return 0

    run_daemon(_connect, jira_config_from_env, interval_seconds=args.interval)
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.exit(main())
