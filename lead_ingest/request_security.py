from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import math
import os
import time
from dataclasses import dataclass, field

from lead_ingest.db_compat import IS_POSTGRES

DEFAULT_CSRF_SECONDS = 60 * 60

logger = logging.getLogger("lead_ingest.ratelimit")

RATE_LIMIT_DDL = """
CREATE TABLE IF NOT EXISTS rate_limit_buckets (
    bucket_key TEXT NOT NULL,
    route_class TEXT NOT NULL,
    tokens REAL NOT NULL,
    last_refill REAL NOT NULL,
    PRIMARY KEY (bucket_key, route_class)
)
"""


def _env_int(name: str, default: int) -> int:
    """Env-var override with a sane fallback on junk values."""
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_csrf_token(secret: str, action: str, now: int | None = None) -> str:
    if not secret:
        raise ValueError("CSRF secret is required")
    issued_at = int(time.time() if now is None else now)
    payload = {"action": action, "iat": issued_at}
    encoded = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_csrf_token(
    token: str,
    secret: str,
    action: str,
    now: int | None = None,
    max_age_seconds: int = DEFAULT_CSRF_SECONDS,
) -> bool:
    if not token or not secret or "." not in token:
        return False
    encoded, signature = token.rsplit(".", 1)
    expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False
    try:
        payload = json.loads(_b64decode(encoded))
    except (ValueError, json.JSONDecodeError):
        return False
    if payload.get("action") != action:
        return False
    issued_at = int(payload.get("iat", 0))
    current_time = int(time.time() if now is None else now)
    return 0 <= current_time - issued_at <= max_age_seconds


@dataclass
class RateLimiter:
    max_requests: int
    window_seconds: int
    hits: dict[str, list[float]] = field(default_factory=dict)

    def allow(self, key: str, now: float | None = None) -> bool:
        current_time = time.time() if now is None else now
        cutoff = current_time - self.window_seconds
        recent = [timestamp for timestamp in self.hits.get(key, []) if timestamp >= cutoff]
        if len(recent) >= self.max_requests:
            self.hits[key] = recent
            return False
        recent.append(current_time)
        self.hits[key] = recent
        return True

    def clear(self) -> None:
        self.hits.clear()


@dataclass(frozen=True)
class RouteLimit:
    """Token-bucket config for one route class.

    ``burst`` tokens are available instantly; tokens refill at
    ``burst / window_seconds`` per second (refill-on-read, no sweeper).
    """

    burst: int
    window_seconds: int

    @property
    def refill_rate(self) -> float:
        return self.burst / self.window_seconds


def _default_route_limits() -> dict[str, RouteLimit]:
    """Production defaults; every value env-overridable.

    Signup POST is distinctly the strictest class. Admin-login POST rides
    the admin class (brute-force protection); admin GETs are page views.
    """
    return {
        "signup": RouteLimit(
            _env_int("RATE_LIMIT_SIGNUP_BURST", 5),
            _env_int("RATE_LIMIT_SIGNUP_WINDOW", 60),
        ),
        "admin": RouteLimit(
            _env_int("RATE_LIMIT_ADMIN_BURST", 30),
            _env_int("RATE_LIMIT_ADMIN_WINDOW", 60),
        ),
        "public": RouteLimit(
            _env_int("RATE_LIMIT_PUBLIC_BURST", 60),
            _env_int("RATE_LIMIT_PUBLIC_WINDOW", 60),
        ),
    }


class TokenBucketStore:
    """DB-backed token buckets with refill-on-read and CAS consume.

    Atomicity model (works on SQLite AND Postgres via db_compat):

    - A bucket row is created ONCE per key via
      ``INSERT ... ON CONFLICT DO NOTHING`` with a full bucket. No
      created row ever goes stale through abandonment.
    - Every later mutation is a compare-and-set:
      ``UPDATE ... SET tokens = <expected> WHERE ... AND tokens = <seen>``
      for the consume path, and ``... WHERE tokens < 1`` on the deny
      path (refreshes refill bookkeeping so denied storms cannot
      accumulate phantom credit).
    - ``rowcount`` tells us whether we won the race. A lost race
      (another process consumed between our read and update) retries
      from a fresh read -- classic optimistic concurrency. Postgres
      serializes competing UPDATEs on the row lock; SQLite serializes
      writers database-wide. Either way, two processes sharing a DB
      cannot jointly exceed the limit.

    No background sweeper: elapsed-time refill is computed at read time,
    so idle clients reset naturally.
    """

    _MAX_RETRIES = 3

    def __init__(self, connect, limits: dict[str, RouteLimit] | None = None):
        """``connect`` is a zero-arg callable returning a FRESH DB connection
        per operation (sqlite3 connections are thread-bound, so a shared
        connection cannot serve a threaded server).
        """
        self._connect = connect
        self.limits = dict(limits) if limits else _default_route_limits()

    # -- persistence helpers -------------------------------------------

    def _read(self, conn, key: str, route_class: str):
        return conn.execute(
            "SELECT tokens, last_refill FROM rate_limit_buckets "
            "WHERE bucket_key = ? AND route_class = ?",
            (key, route_class),
        ).fetchone()

    def _create(self, conn, key: str, route_class: str, tokens: float, now: float) -> None:
        """Idempotent bucket creation -- first writer wins, nobody errors."""
        if IS_POSTGRES:
            conn.execute(
                "INSERT INTO rate_limit_buckets "
                "(bucket_key, route_class, tokens, last_refill) VALUES (?, ?, ?, ?) "
                "ON CONFLICT DO NOTHING",
                (key, route_class, tokens, now),
            )
        else:
            conn.execute(
                "INSERT OR IGNORE INTO rate_limit_buckets "
                "(bucket_key, route_class, tokens, last_refill) VALUES (?, ?, ?, ?)",
                (key, route_class, tokens, now),
            )

    def _cas_update(
        self, conn, key: str, route_class: str, new_tokens: float, now: float, seen: float
    ) -> bool:
        cursor = conn.execute(
            "UPDATE rate_limit_buckets SET tokens = ?, last_refill = ? "
            "WHERE bucket_key = ? AND route_class = ? AND tokens = ?",
            (new_tokens, now, key, route_class, seen),
        )
        return cursor.rowcount == 1

    def _guard_refresh(
        self, conn, key: str, route_class: str, new_tokens: float, now: float
    ) -> bool:
        """Advance refill bookkeeping only when the bucket is still empty."""
        cursor = conn.execute(
            "UPDATE rate_limit_buckets SET tokens = ?, last_refill = ? "
            "WHERE bucket_key = ? AND route_class = ? AND tokens < 1",
            (new_tokens, now, key, route_class),
        )
        return cursor.rowcount == 1

    # -- public API -----------------------------------------------------

    def allow(self, key: str, route_class: str, now: float | None = None) -> bool:
        limit = self.limits[route_class]
        now = time.time() if now is None else now
        conn = self._connect()
        try:
            self._create(conn, key, route_class, float(limit.burst), now)

            for _ in range(self._MAX_RETRIES):
                row = self._read(conn, key, route_class)
                tokens, last_refill = float(row["tokens"]), float(row["last_refill"])
                available = min(
                    float(limit.burst),
                    tokens + max(0.0, now - last_refill) * limit.refill_rate,
                )
                if available >= 1.0:
                    if self._cas_update(conn, key, route_class, available - 1.0, now, tokens):
                        conn.commit()
                        return True
                    # Lost a CAS race; re-read and retry.
                    continue
                if self._guard_refresh(conn, key, route_class, available, now):
                    conn.commit()
                    return False
                # Someone refilled between read and deny; re-check.
            return False  # contended beyond retries: fail closed, stay safe
        finally:
            conn.close()

    def retry_after(self, key: str, route_class: str, now: float | None = None) -> int:
        """Seconds until the bucket next holds a full token (ceil, >= 1)."""
        limit = self.limits[route_class]
        now = time.time() if now is None else now
        conn = self._connect()
        try:
            row = self._read(conn, key, route_class)
            if row is None:
                return 1
            available = min(
                float(limit.burst),
                float(row["tokens"])
                + max(0.0, now - float(row["last_refill"])) * limit.refill_rate,
            )
        except Exception:
            return 1
        finally:
            conn.close()
        if available >= 1.0:
            return 1
        return max(1, math.ceil((1.0 - available) / limit.refill_rate))


class PersistentRateLimiter:
    """Fail-safe facade over :class:`TokenBucketStore`.

    Loud fallback: if the bucket table is unreadable/unwritable, every
    failure logs a LOUD warning and a conservative shared in-memory
    limiter takes over for the process lifetime. Limiting is NEVER
    silently disabled; a process with a broken DB still throttles.
    """

    FALLBACK = RateLimiter(max_requests=10, window_seconds=60)

    def __init__(self, connect, limits: dict[str, RouteLimit] | None = None):
        """``connect`` is a zero-arg callable returning a fresh DB connection
        (or, for tests, a fixed connection). Storage errors trip the loud
        in-memory fallback for the process lifetime.
        """
        self._store = TokenBucketStore(connect, limits)
        self._broken = False

    def allow(self, key: str, route_class: str = "public", now: float | None = None) -> bool:
        if self._broken:
            return self.FALLBACK.allow(key, now)
        try:
            return self._store.allow(key, route_class, now)
        except Exception:
            self._broken = True
            logger.warning(
                "RATE LIMIT STORAGE FAILURE: rate_limit_buckets unreadable; "
                "falling back to conservative in-memory limiter (%d req/%ds per key, "
                "this process only). Fix the database!",
                self.FALLBACK.max_requests,
                self.FALLBACK.window_seconds,
                exc_info=True,
            )
            return self.FALLBACK.allow(key, now)

    def retry_after(self, key: str, route_class: str = "public", now: float | None = None) -> int:
        if self._broken:
            return 60
        try:
            return self._store.retry_after(key, route_class, now)
        except Exception:
            return 60
