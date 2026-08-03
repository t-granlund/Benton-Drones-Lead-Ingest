"""Tests for the persistent, DB-backed token-bucket rate limiter.

Covers: bucket math, refill-on-read (no sweeper), CAS atomicity across
concurrent consumers sharing one DB, per-route-class limits, restart
persistence, and the loud storage-error fallback. All SQLite, stdlib
only, no network.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from lead_ingest.db import init_db
from lead_ingest.request_security import (
    PersistentRateLimiter,
    RateLimiter,
    RouteLimit,
    TokenBucketStore,
)
from lead_ingest.server import LimiterAdapter, route_class_for


def _file_db():
    """Temp-file SQLite DB; returns (path, cleanup)."""
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    return path


def _connect_file(path):
    def go():
        conn = sqlite3.connect(path, timeout=30)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    return go


class _UnclosableConn:
    """Wraps a fixed connection so the store's per-op ``close()`` is a no-op.

    The store is designed around fresh short-lived connections; tests that
    want a single shared in-memory DB hand it a fixed one via this shim.
    """

    def __init__(self, conn):
        self._conn = conn

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def commit(self):
        self._conn.commit()

    def close(self):
        pass  # deliberately NOT closing the shared in-memory DB


def _connect_memory():
    """Shared in-memory DB behind a store-compatible connect callable."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    shared = _UnclosableConn(conn)
    return lambda: shared  # single-threaded tests only


class BucketMathTests(unittest.TestCase):
    def setUp(self):
        self.limits = {"public": RouteLimit(burst=3, window_seconds=30)}  # 0.1 tok/s
        self.store = TokenBucketStore(_connect_memory(), self.limits)

    def test_burst_then_deny_at_exact_limit(self):
        self.assertTrue(self.store.allow("ip:/x", "public", now=1000.0))
        self.assertTrue(self.store.allow("ip:/x", "public", now=1000.0))
        self.assertTrue(self.store.allow("ip:/x", "public", now=1000.0))
        self.assertFalse(self.store.allow("ip:/x", "public", now=1000.0))

    def test_refill_over_time_without_sweeper(self):
        for _ in range(3):
            self.store.allow("ip:/x", "public", now=1000.0)
        self.assertFalse(self.store.allow("ip:/x", "public", now=1000.0))
        # 10 seconds later -> exactly 1 token refilled (0.1 tok/s).
        self.assertTrue(self.store.allow("ip:/x", "public", now=1010.0))
        self.assertFalse(self.store.allow("ip:/x", "public", now=1010.0))

    def test_refill_capped_at_burst(self):
        for _ in range(3):
            self.store.allow("ip:/x", "public", now=1000.0)
        # An hour later the bucket holds at most `burst`, not a zillion.
        allowed = sum(
            self.store.allow("ip:/x", "public", now=4600.0) for _ in range(10)
        )
        self.assertEqual(allowed, 3)

    def test_idle_client_resets_naturally(self):
        for _ in range(3):
            self.store.allow("ip:/idle", "public", now=1000.0)
        # Long idle -> full bucket again on next read.
        self.assertEqual(
            sum(self.store.allow("ip:/idle", "public", now=5000.0) for _ in range(5)),
            3,
        )

    def test_retry_after_grows_while_empty(self):
        for _ in range(3):
            self.store.allow("ip:/x", "public", now=1000.0)
        # Empty at 0.1 tok/s -> 10s until next token.
        self.assertEqual(self.store.retry_after("ip:/x", "public", now=1000.0), 10)
        # After 9.5s of refill -> 1s left (ceil).
        self.assertEqual(self.store.retry_after("ip:/x", "public", now=1009.5), 1)


class AtomicityTests(unittest.TestCase):
    def test_two_threads_sharing_db_never_exceed_limit(self):
        """Two 'processes' (threads, separate connections, same file DB)
        racing on the same client key: combined allows == burst, exactly."""
        path = _file_db()
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        burst = 10
        limits = {"signup": RouteLimit(burst=burst, window_seconds=60)}

        results = {"a": 0, "b": 0}

        def hammer(name):
            store = TokenBucketStore(_connect_file(path), limits)
            for _ in range(burst):  # each thread tries to take the whole bucket
                if store.allow("1.2.3.4:/signup", "signup"):
                    results[name] += 1

        t1 = threading.Thread(target=hammer, args=("a",))
        t2 = threading.Thread(target=hammer, args=("b",))
        t1.start(); t2.start(); t1.join(); t2.join()

        self.assertEqual(results["a"] + results["b"], burst)

    def test_consumed_tokens_survive_restart(self):
        """New limiter instance over the same DB sees prior consumption."""
        path = _file_db()
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        limits = {"signup": RouteLimit(burst=2, window_seconds=60)}

        first = TokenBucketStore(_connect_file(path), limits)
        self.assertTrue(first.allow("9.9.9.9:/signup", "signup"))
        self.assertTrue(first.allow("9.9.9.9:/signup", "signup"))
        self.assertFalse(first.allow("9.9.9.9:/signup", "signup"))

        # 'Restart': brand-new store object, same DB file.
        second = TokenBucketStore(_connect_file(path), limits)
        self.assertFalse(second.allow("9.9.9.9:/signup", "signup"))


class RouteClassTests(unittest.TestCase):
    def test_signup_strictest_then_admin_then_public(self):
        store = TokenBucketStore(_connect_memory())  # production defaults
        limits = store.limits
        self.assertLess(limits["signup"].burst, limits["admin"].burst)
        self.assertLess(limits["admin"].burst, limits["public"].burst)
        self.assertEqual(limits["signup"].burst, 5)

    def test_env_overrides(self):
        from lead_ingest.request_security import _default_route_limits

        with patch.dict(
            os.environ,
            {"RATE_LIMIT_SIGNUP_BURST": "2", "RATE_LIMIT_PUBLIC_WINDOW": "120"},
        ):
            limits = _default_route_limits()
        self.assertEqual(limits["signup"].burst, 2)
        self.assertEqual(limits["public"].window_seconds, 120)

    def test_route_class_mapping(self):
        self.assertEqual(route_class_for("/signup", "POST"), "signup")
        self.assertEqual(route_class_for("/admin-login", "POST"), "admin")
        self.assertEqual(route_class_for("/overview", "GET"), "public")
        self.assertEqual(route_class_for("/signup", "GET"), "public")  # form view
        self.assertEqual(route_class_for("/admin", "GET"), "public")

    def test_adapter_derives_class_from_key(self):
        limits = {"signup": RouteLimit(2, 60), "public": RouteLimit(100, 60)}
        adapter = LimiterAdapter(PersistentRateLimiter(_connect_memory(), limits))
        self.assertTrue(adapter.allow("7.7.7.7:/signup:POST"))
        self.assertTrue(adapter.allow("7.7.7.7:/signup:POST"))
        self.assertFalse(adapter.allow("7.7.7.7:/signup:POST"))  # signup cap hit
        # Same client, different class: public bucket untouched.
        self.assertTrue(adapter.allow("7.7.7.7:/overview"))


class FallbackTests(unittest.TestCase):
    def test_storage_error_logs_loud_and_falls_back(self):
        def bad_connect():
            raise sqlite3.OperationalError("no such table: rate_limit_buckets")

        limiter = PersistentRateLimiter(bad_connect)
        with self.assertLogs("lead_ingest.ratelimit", level="WARNING") as logs:
            first = limiter.allow("ip:/signup", "signup")
        self.assertTrue(any("RATE LIMIT STORAGE FAILURE" in m for m in logs.output))
        # Not silently unlimited: the conservative fallback limiter applies.
        self.assertTrue(first)
        self.assertIsInstance(limiter.FALLBACK, RateLimiter)
        self.assertLessEqual(limiter.FALLBACK.max_requests, 10)
        # Second failure does NOT re-log (fallback state already latched).
        with self.assertNoLogs("lead_ingest.ratelimit", level="WARNING"):
            limiter.allow("ip:/signup", "signup")

    def test_fallback_still_throttles(self):
        limiter = PersistentRateLimiter(_connect_memory())
        limiter._broken = True  # simulate prior storage failure
        limiter.FALLBACK = RateLimiter(max_requests=2, window_seconds=60)
        self.assertTrue(limiter.allow("ip:/x", "public"))
        self.assertTrue(limiter.allow("ip:/x", "public"))
        self.assertFalse(limiter.allow("ip:/x", "public"))  # still limited!
        self.assertEqual(limiter.retry_after("ip:/x", "public"), 60)

    def test_missing_table_trips_fallback_not_crash(self):
        conn = sqlite3.connect(":memory:")  # NO init_db -> no buckets table
        conn.row_factory = sqlite3.Row
        limiter = PersistentRateLimiter(lambda: conn)
        with self.assertLogs("lead_ingest.ratelimit", level="WARNING"):
            limiter.allow("ip:/x", "public")
        self.assertTrue(limiter._broken)


if __name__ == "__main__":
    unittest.main()
