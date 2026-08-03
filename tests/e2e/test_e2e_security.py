"""E2E: request security & production hardening.

Covers: baseline security headers, Cache-Control no-store on PII/export paths,
oversized-body 413 rejection, rate-limit 429 rejection, static path-traversal
403, unknown POST 404, and the production weak-password startup gate.
"""
import logging
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_base import E2ETestBase, ADMIN_PASSWORD  # noqa: E402


class SecurityHeadersTests(E2ETestBase):

    def test_public_pages_have_baseline_security_headers(self):
        response, _ = self.get("/signup")
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.getheader("X-Frame-Options"), "DENY")
        self.assertEqual(response.getheader("Referrer-Policy"), "no-referrer")

    def test_public_page_is_not_marked_no_store(self):
        response, _ = self.get("/overview")
        # Public pages must not carry Cache-Control: no-store (not PII).
        cache = response.getheader("Cache-Control") or ""
        self.assertNotIn("no-store", cache)

    def test_admin_dashboard_sets_no_store_cache_control(self):
        cookie = self.admin_cookie()
        response, _ = self.get("/admin", cookie=cookie)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_exports_set_no_store_cache_control(self):
        cookie = self.admin_cookie()
        response, _ = self.get("/export/csv", cookie=cookie)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_static_path_traversal_is_blocked_403(self):
        # Literal ".." in the path must escape STATIC_ROOT and be refused.
        response, _ = self.get("/static/../../etc/passwd")
        self.assertEqual(response.status, 403)

    def test_unknown_post_path_returns_404(self):
        response, _ = self.post_form("/no-such-endpoint", {"x": "1"})
        self.assertEqual(response.status, 404)


class RateLimitTests(E2ETestBase):
    # Tight limiter so the 4th request in the window is refused.
    rate_limit = (3, 60)

    def test_rate_limit_blocks_after_threshold_returns_429(self):
        from lead_ingest import server
        server.RATE_LIMITER.clear()  # ignore any prior calls in this class
        statuses = []
        for _ in range(4):
            # Minimal POST to /signup; allow_request runs before CSRF, so a
            # bogus token still counts toward the limit.
            response, _ = self.post_form("/signup", {"csrf_token": "x"})
            statuses.append(response.status)
        # First three are processed (400 invalid CSRF); the fourth is throttled.
        self.assertEqual(statuses[:3], [400, 400, 400])
        self.assertEqual(statuses[3], 429)

    def test_429_includes_retry_after_and_generic_body(self):
        """Over-limit 429 must carry Retry-After and leak no internals."""
        from unittest.mock import patch
        from lead_ingest.request_security import PersistentRateLimiter
        from lead_ingest.server import LimiterAdapter
        from lead_ingest.db import connect as db_connect, init_db

        def _connect():
            conn = db_connect(self._db_path)
            init_db(conn)
            return conn

        from lead_ingest.request_security import RouteLimit

        limits = {"signup": RouteLimit(1, 30), "public": RouteLimit(1000, 60)}
        limiter = LimiterAdapter(PersistentRateLimiter(_connect, limits))
        with patch("lead_ingest.server.RATE_LIMITER", limiter):
            r1, _ = self.post_form("/signup", {"csrf_token": "x"})
            r2, body2 = self.post_form("/signup", {"csrf_token": "x"})
        self.assertEqual(r1.status, 400)  # first request processed (bad CSRF)
        self.assertEqual(r2.status, 429)
        retry = r2.getheader("Retry-After")
        self.assertIsNotNone(retry)
        self.assertGreaterEqual(int(retry), 1)
        # Generic body: no limit values, no internals.
        self.assertNotIn(b"1", body2.replace(b"a moment", b""))
        self.assertNotIn(b"bucket", body2.lower())
        self.assertNotIn(b"token", body2.lower())
        self.assertIn(b"Too many requests", body2)

    def test_body_size_limit_rejects_oversized_post_413(self):
        # /admin-login accepts POST; an enormous body is rejected before handling.
        big = b"x" * 70_000  # > 64 KiB server limit
        response, content = self.request(
            "POST", "/admin-login", body=big,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 413)
        self.assertIn(b"Request body too large", content)


class ProductionHardeningTests(E2ETestBase):

    def test_validate_refuses_weak_password_in_production(self):
        from lead_ingest.server import validate_production_ready
        log = logging.getLogger("e2e.production")
        saved_env = os.environ.get("ENV")
        saved_pw = os.environ.get("ADMIN_PASSWORD")
        try:
            os.environ["ENV"] = "production"
            os.environ["ADMIN_PASSWORD"] = "password"  # weak default
            with self.assertRaises(SystemExit):
                validate_production_ready(log)
        finally:
            os.environ["ADMIN_PASSWORD"] = ADMIN_PASSWORD
            os.environ.pop("ENV", None)
            if saved_env is not None:
                os.environ["ENV"] = saved_env
            if saved_pw is not None:
                os.environ["ADMIN_PASSWORD"] = saved_pw

    def test_validate_passes_with_strong_config_non_production(self):
        from lead_ingest.server import validate_production_ready
        log = logging.getLogger("e2e.production")
        # Class fixture already sets a strong password and ENV unset.
        validate_production_ready(log)  # must not raise


if __name__ == "__main__":
    unittest.main()
