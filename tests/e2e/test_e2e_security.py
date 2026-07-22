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
