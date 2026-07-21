"""Production-readiness hardening tests.

Covers: healthz, security headers, cookie Secure flag, body-size limit,
static path traversal, stored XSS fix, secret derivation, and startup
validation.  These are architecture fitness functions that prevent
regressions on the fixes from the production-readiness review.
"""
import http.client
import json
import os
import re
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlencode

from lead_ingest.auth import expired_session_cookie, session_cookie
from lead_ingest.request_security import RateLimiter
from lead_ingest.server import (
    MAX_BODY_BYTES,
    VERSION,
    Handler,
    _derive_dev_secret,
    validate_production_ready,
)


class HardeningServerBase(unittest.TestCase):
    """Isolated HTTP server with a temp database for hardening tests."""

    @classmethod
    def setUpClass(cls):
        cls._tempdir = tempfile.TemporaryDirectory()
        cls._db_path = os.path.join(cls._tempdir.name, "hardening_test.sqlite3")

        cls._patcher_db = patch("lead_ingest.server.DEFAULT_DB_PATH", cls._db_path)
        cls._patcher_db.start()
        cls._patcher_rl = patch(
            "lead_ingest.server.RATE_LIMITER",
            RateLimiter(max_requests=100_000, window_seconds=60),
        )
        cls._patcher_rl.start()

        cls._saved_env: dict[str, str | None] = {}
        for key in (
            "ADMIN_PASSWORD", "ADMIN_SESSION_SECRET", "CSRF_SECRET",
            "COOKIE_SECURE", "ENV", "QUIET_HTTP_LOGS",
        ):
            cls._saved_env[key] = os.environ.get(key)

        os.environ["ADMIN_PASSWORD"] = "hardening-test-password"
        os.environ["ADMIN_SESSION_SECRET"] = "hardening-test-session-secret-32chars!"
        os.environ["CSRF_SECRET"] = "hardening-test-csrf-secret-also32chars!!"
        os.environ["QUIET_HTTP_LOGS"] = "1"
        os.environ.pop("COOKIE_SECURE", None)
        os.environ.pop("ENV", None)

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls._patcher_db.stop()
        cls._patcher_rl.stop()
        cls._tempdir.cleanup()
        for key, val in cls._saved_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        content = response.read()
        conn.close()
        return response, content

    def extract_csrf(self, content):
        match = re.search(rb'name="csrf_token" value="([^"]+)"', content)
        self.assertIsNotNone(match, "CSRF token not found in page")
        return match.group(1).decode()

    def login_cookie(self):
        _, content = self.request("GET", "/admin-login")
        body = urlencode({
            "password": "hardening-test-password",
            "csrf_token": self.extract_csrf(content),
        })
        response, _ = self.request(
            "POST", "/admin-login", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 302)
        return response.getheader("Set-Cookie")


# -----------------------------------------------------------------------
# Health check endpoint
# -----------------------------------------------------------------------

class TestHealthz(HardeningServerBase):
    def test_healthz_returns_200_json(self):
        response, content = self.request("GET", "/healthz")
        self.assertEqual(response.status, 200)
        self.assertIn("application/json", response.getheader("Content-Type", ""))
        data = json.loads(content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["version"], VERSION)
        self.assertTrue(data["tests_passed"])

    def test_healthz_unauthenticated(self):
        """Healthz must work without any cookie or auth header."""
        response, _ = self.request("GET", "/healthz")
        self.assertEqual(response.status, 200)

    def test_healthz_has_security_headers(self):
        response, _ = self.request("GET", "/healthz")
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.getheader("X-Frame-Options"), "DENY")
        self.assertEqual(response.getheader("Referrer-Policy"), "no-referrer")


# -----------------------------------------------------------------------
# Security headers
# -----------------------------------------------------------------------

class TestSecurityHeaders(HardeningServerBase):
    def test_html_response_has_security_headers(self):
        response, _ = self.request("GET", "/signup")
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.getheader("X-Frame-Options"), "DENY")
        self.assertEqual(response.getheader("Referrer-Policy"), "no-referrer")

    def test_admin_page_has_no_store_cache_control(self):
        cookie = self.login_cookie()
        response, _ = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_admin_login_page_has_no_store_cache_control(self):
        response, _ = self.request("GET", "/admin-login")
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_export_route_has_no_store_cache_control(self):
        cookie = self.login_cookie()
        response, _ = self.request("GET", "/export/csv", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_lead_detail_has_no_store_cache_control(self):
        cookie = self.login_cookie()
        response, _ = self.request("GET", "/admin/lead/1", headers={"Cookie": cookie})
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_static_files_have_cache_control_max_age(self):
        response, _ = self.request("GET", "/static/leaflet/leaflet.css")
        self.assertEqual(response.status, 200)
        cache_ctrl = response.getheader("Cache-Control", "")
        self.assertIn("max-age=86400", cache_ctrl)
        self.assertIn("public", cache_ctrl)

    def test_redirect_has_security_headers(self):
        """Unauthenticated /admin redirect should include security headers."""
        response, _ = self.request("GET", "/admin")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.getheader("Cache-Control"), "no-store")


# -----------------------------------------------------------------------
# Cookie security
# -----------------------------------------------------------------------

class TestCookieSecure(HardeningServerBase):
    def test_default_cookie_not_secure(self):
        cookie = self.login_cookie()
        self.assertIsNotNone(cookie)
        self.assertNotIn("Secure", cookie)

    def test_cookie_secure_env_flag(self):
        os.environ["COOKIE_SECURE"] = "1"
        try:
            cookie = self.login_cookie()
            self.assertIn("Secure", cookie)
        finally:
            os.environ.pop("COOKIE_SECURE", None)

    def test_cookie_secure_via_forwarded_proto(self):
        _, content = self.request("GET", "/admin-login")
        body = urlencode({
            "password": "hardening-test-password",
            "csrf_token": self.extract_csrf(content),
        })
        response, _ = self.request(
            "POST", "/admin-login", body=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Forwarded-Proto": "https",
            },
        )
        self.assertEqual(response.status, 302)
        cookie = response.getheader("Set-Cookie", "")
        self.assertIn("Secure", cookie)

    def test_logout_cookie_respects_secure_flag(self):
        os.environ["COOKIE_SECURE"] = "1"
        try:
            response, _ = self.request("GET", "/admin-logout")
            self.assertEqual(response.status, 302)
            cookie = response.getheader("Set-Cookie", "")
            self.assertIn("Secure", cookie)
        finally:
            os.environ.pop("COOKIE_SECURE", None)

    def test_expired_session_cookie_helper_supports_secure(self):
        cookie = expired_session_cookie(secure=True)
        self.assertIn("Secure", cookie)
        cookie_plain = expired_session_cookie(secure=False)
        self.assertNotIn("Secure", cookie_plain)

    def test_session_cookie_helper_secure_flag(self):
        self.assertIn("Secure", session_cookie("x", secure=True))
        self.assertNotIn("Secure", session_cookie("x", secure=False))


# -----------------------------------------------------------------------
# Request body size limit
# -----------------------------------------------------------------------

class TestBodySizeLimit(HardeningServerBase):
    def test_oversized_post_returns_413(self):
        _, content = self.request("GET", "/signup")
        csrf = self.extract_csrf(content)
        # Build a body > 64 KB
        big_value = "x" * (MAX_BODY_BYTES + 100)
        body = urlencode({
            "first_name": "Big",
            "last_name": "Body",
            "email": "big@example.com",
            "address_line1": "1 Drone Way",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "Big Body",
            "csrf_token": csrf,
            "notes": big_value,
        })
        response, content = self.request(
            "POST", "/signup", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 413)
        self.assertIn(b"too large", content)

    def test_normal_post_still_works(self):
        _, content = self.request("GET", "/signup")
        csrf = self.extract_csrf(content)
        body = urlencode({
            "first_name": "Normal",
            "last_name": "Size",
            "email": "normal@example.com",
            "address_line1": "1 Drone Way",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "Normal Size",
            "csrf_token": csrf,
        })
        response, content = self.request(
            "POST", "/signup", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 200)
        self.assertIn(b"Your signup was saved", content)


# -----------------------------------------------------------------------
# Static path traversal
# -----------------------------------------------------------------------

class TestStaticPathTraversal(HardeningServerBase):
    def test_traversal_blocked(self):
        response, _ = self.request("GET", "/static/../../../etc/passwd")
        self.assertIn(response.status, (403, 404))

    def test_traversal_encoded_blocked(self):
        response, _ = self.request("GET", "/static/%2e%2e%2f%2e%2e%2fetc%2fpasswd")
        self.assertIn(response.status, (403, 404))


# -----------------------------------------------------------------------
# Stored XSS fix in admin map
# -----------------------------------------------------------------------

class TestAdminMapXssFix(HardeningServerBase):
    def test_popup_uses_esc_function(self):
        """The map popup JS must escape name/address via esc()."""
        # Submit a lead with a name containing HTML to populate the map.
        _, content = self.request("GET", "/signup")
        csrf = self.extract_csrf(content)
        body = urlencode({
            "first_name": "<img src=x onerror=alert(1)>",
            "last_name": "Test",
            "email": "xss-test@example.com",
            "address_line1": "100 Flight Path",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "Xss Test",
            "csrf_token": csrf,
        })
        resp, _ = self.request(
            "POST", "/signup", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(resp.status, 200)

        cookie = self.login_cookie()
        _, admin_content = self.request("GET", "/admin", headers={"Cookie": cookie})
        # The esc() helper must be present
        self.assertIn(b"function esc(s)", admin_content)
        # Popup must wrap name/address in esc()
        self.assertIn(b"esc(feature.properties.name)", admin_content)
        self.assertIn(b"esc(feature.properties.address)", admin_content)
        # Raw unescaped injection must NOT appear in bindPopup
        self.assertNotIn(b"bindPopup('<a href=\"/admin/lead/' + feature.properties.id + '\">' + feature.properties.name", admin_content)


# -----------------------------------------------------------------------
# Secret derivation
# -----------------------------------------------------------------------

class TestSecretDerivation(unittest.TestCase):
    def setUp(self):
        self._old_pw = os.environ.get("ADMIN_PASSWORD")
        os.environ["ADMIN_PASSWORD"] = "test-pw-for-derivation"

    def tearDown(self):
        if self._old_pw is None:
            os.environ.pop("ADMIN_PASSWORD", None)
        else:
            os.environ["ADMIN_PASSWORD"] = self._old_pw

    def test_derive_returns_nonempty_hex(self):
        secret = _derive_dev_secret("csrf")
        self.assertTrue(secret)
        self.assertEqual(len(secret), 64)  # 32 bytes → 64 hex chars

    def test_different_purposes_yield_different_secrets(self):
        a = _derive_dev_secret("csrf")
        b = _derive_dev_secret("session")
        self.assertNotEqual(a, b)

    def test_derive_empty_when_no_password(self):
        os.environ.pop("ADMIN_PASSWORD", None)
        self.assertEqual(_derive_dev_secret("csrf"), "")

    def test_derive_is_deterministic(self):
        self.assertEqual(_derive_dev_secret("csrf"), _derive_dev_secret("csrf"))


# -----------------------------------------------------------------------
# Startup validation
# -----------------------------------------------------------------------

class TestValidateProductionReady(unittest.TestCase):
    def setUp(self):
        import logging
        self._logger = logging.getLogger("test_validate")
        self._saved = {}
        for key in (
            "ENV", "ADMIN_PASSWORD", "ADMIN_SESSION_SECRET", "CSRF_SECRET",
            "JIRA_BASE_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY",
        ):
            self._saved[key] = os.environ.get(key)
        # Clean slate
        for key in self._saved:
            os.environ.pop(key, None)

    def tearDown(self):
        for key, val in self._saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def test_production_refuses_without_secrets(self):
        os.environ["ENV"] = "production"
        os.environ["ADMIN_PASSWORD"] = "strong-prod-password"
        with self.assertRaises(SystemExit):
            validate_production_ready(self._logger)

    def test_production_refuses_with_short_secret(self):
        os.environ["ENV"] = "production"
        os.environ["ADMIN_PASSWORD"] = "strong-prod-password"
        os.environ["ADMIN_SESSION_SECRET"] = "too-short"
        os.environ["CSRF_SECRET"] = "also-too-short"
        with self.assertRaises(SystemExit):
            validate_production_ready(self._logger)

    def test_production_starts_with_strong_config(self):
        os.environ["ENV"] = "production"
        os.environ["ADMIN_PASSWORD"] = "strong-prod-password"
        os.environ["ADMIN_SESSION_SECRET"] = "x" * 32
        os.environ["CSRF_SECRET"] = "y" * 32
        # Should NOT raise
        validate_production_ready(self._logger)

    def test_production_refuses_weak_password(self):
        os.environ["ENV"] = "production"
        os.environ["ADMIN_PASSWORD"] = "change-me"
        os.environ["ADMIN_SESSION_SECRET"] = "x" * 32
        os.environ["CSRF_SECRET"] = "y" * 32
        with self.assertRaises(SystemExit):
            validate_production_ready(self._logger)

    def test_dev_mode_does_not_raise_on_weak_config(self):
        os.environ["ADMIN_PASSWORD"] = "change-me"
        # Should NOT raise in dev mode (just warns)
        validate_production_ready(self._logger)

    def test_dev_mode_does_not_raise_without_password(self):
        os.environ.pop("ADMIN_PASSWORD", None)
        validate_production_ready(self._logger)

    def test_partial_jira_config_warns_but_does_not_raise(self):
        os.environ["ADMIN_PASSWORD"] = "good-password"
        os.environ["JIRA_BASE_URL"] = "https://jira.example.com"
        # Only 1 of 4 JIRA vars set — should warn, not raise
        validate_production_ready(self._logger)


if __name__ == "__main__":
    unittest.main()
