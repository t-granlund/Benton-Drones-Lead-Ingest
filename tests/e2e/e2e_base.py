"""Shared base for the E2E HTTP test suite.

Each subclass gets its OWN isolated database (a temp SQLite file) and its OWN
server on an ephemeral port (127.0.0.1:0), so tests are fully independent with no
shared mutable state and no interference with the 281 existing unit tests.

Run the whole suite with::

    python -m unittest discover -s tests/e2e -t tests/e2e -v

The module name deliberately does NOT start with ``test`` so unittest's default
``test*.py`` pattern skips it -- it is a helper, not a test module.
"""
from __future__ import annotations

import http.client
import os
import re
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlencode

from lead_ingest.request_security import RateLimiter
from lead_ingest.server import Handler

# Strong, non-weak test credentials (must avoid the WEAK_PASSWORDS blocklist).
ADMIN_PASSWORD = "e2e-Strong-Password-742!"
ADMIN_SESSION_SECRET = "e2e-session-secret-very-long-and-random-0123456789"
CSRF_SECRET = "e2e-csrf-secret-also-long-and-random-9876543210"

# Env vars the base touches; saved/restored per class so nothing leaks out.
_ENV_KEYS = (
    "ADMIN_PASSWORD", "ADMIN_SESSION_SECRET", "CSRF_SECRET",
    "QUIET_HTTP_LOGS", "ENV", "DATABASE_URL", "SHOPIFY_APP_SECRET",
    "COOKIE_SECURE",
)


class E2ETestBase(unittest.TestCase):
    """Black-box HTTP tests against a real server with an isolated temp DB.

    Subclasses may override ``rate_limit`` (a (max_requests, window_seconds)
    tuple) to install a tighter limiter for rate-limit-specific tests.
    """

    # Default: effectively unlimited so normal tests never throttle.
    rate_limit = (100_000, 60)

    # ----- lifecycle --------------------------------------------------
    @classmethod
    def setUpClass(cls):
        cls._tempdir = tempfile.TemporaryDirectory()
        cls._db_path = os.path.join(cls._tempdir.name, "e2e.sqlite3")

        cls._patches = [
            patch("lead_ingest.server.DEFAULT_DB_PATH", cls._db_path),
            patch(
                "lead_ingest.server.RATE_LIMITER",
                RateLimiter(max_requests=cls.rate_limit[0],
                             window_seconds=cls.rate_limit[1]),
            ),
        ]
        for p in cls._patches:
            p.start()

        # Pre-create the schema so direct DB helpers (list_lead_ids) work even
        # before the server handles its first request.  Idempotent (IF NOT EXISTS).
        from lead_ingest.db import connect as _connect, init_db as _init_db
        _conn = _connect(cls._db_path)
        _init_db(_conn)
        _conn.close()

        cls._saved_env = {k: os.environ.get(k) for k in _ENV_KEYS}
        os.environ["ADMIN_PASSWORD"] = ADMIN_PASSWORD
        os.environ["ADMIN_SESSION_SECRET"] = ADMIN_SESSION_SECRET
        os.environ["CSRF_SECRET"] = CSRF_SECRET
        os.environ["QUIET_HTTP_LOGS"] = "1"
        os.environ.pop("DATABASE_URL", None)        # force the SQLite engine
        os.environ.pop("ENV", None)                # never "production" in tests
        os.environ.pop("SHOPIFY_APP_SECRET", None)  # direct Shopify fields ok
        os.environ.pop("COOKIE_SECURE", None)

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        for p in cls._patches:
            p.stop()
        cls._tempdir.cleanup()
        for k, v in cls._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # ----- HTTP helpers ----------------------------------------------
    def request(self, method, path, body=None, headers=None, cookie=None):
        hdrs = dict(headers or {})
        if cookie:
            hdrs["Cookie"] = cookie
        conn = http.client.HTTPConnection(self.host, self.port, timeout=5)
        conn.request(method, path, body=body, headers=hdrs)
        response = conn.getresponse()
        content = response.read()
        conn.close()
        return response, content

    def get(self, path, cookie=None, headers=None):
        return self.request("GET", path, cookie=cookie, headers=headers)

    def post_form(self, path, fields, cookie=None, headers=None):
        body = urlencode(fields)
        hdrs = {"Content-Type": "application/x-www-form-urlencoded"}
        if headers:
            hdrs.update(headers)
        return self.request("POST", path, body=body, headers=hdrs, cookie=cookie)

    def post_raw(self, path, body, content_type="application/x-www-form-urlencoded",
                 cookie=None, extra_headers=None):
        hdrs = {"Content-Type": content_type}
        if extra_headers:
            hdrs.update(extra_headers)
        return self.request("POST", path, body=body, headers=hdrs, cookie=cookie)

    # ----- CSRF / auth helpers ---------------------------------------
    def extract_csrf(self, content, name="csrf_token"):
        match = re.search(
            rb'name="' + name.encode() + rb'" value="([^"]+)"', content
        )
        self.assertIsNotNone(match, f"CSRF token ({name}) not found in page")
        return match.group(1).decode()

    def signup_csrf(self):
        _, content = self.get("/signup")
        return self.extract_csrf(content)

    def login_csrf(self):
        _, content = self.get("/admin-login")
        return self.extract_csrf(content)

    @staticmethod
    def _cookie_from(response):
        cookie = response.getheader("Set-Cookie") or ""
        return cookie.split(";", 1)[0] if cookie else ""

    def login(self, password=None):
        """Log in; return (response, session_cookie)."""
        csrf = self.login_csrf()
        response, _ = self.post_form(
            "/admin-login",
            {"password": password or ADMIN_PASSWORD, "csrf_token": csrf},
        )
        return response, self._cookie_from(response)

    def admin_cookie(self):
        """Return a valid admin session cookie, asserting login succeeded."""
        response, cookie = self.login()
        self.assertEqual(response.status, 302, f"login returned {response.status}")
        self.assertTrue(cookie, "no session cookie set on login")
        return cookie

    # ----- signup payload builder ------------------------------------
    @staticmethod
    def valid_signup_fields(email, **overrides):
        base = {
            "first_name": "E2E",
            "last_name": "Tester",
            "email": email,
            "phone": "5551234567",
            "address_line1": "123 Test St",
            "address_line2": "",
            "city": "Testville",
            "state": "CA",
            "postal_code": "90001",
            "campaign": "e2e",
            "source": "e2e-suite",
            "variant_slug": "default",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "E2E Tester",
        }
        base.update(overrides)
        return base

    def submit_signup(self, fields, cookie=None):
        """POST /signup with the given fields plus a fresh signup CSRF."""
        fields = dict(fields)
        fields.setdefault("csrf_token", self.signup_csrf())
        return self.post_form("/signup", fields, cookie=cookie)

    # ----- DB access (temp DB) --------------------------------------
    def list_lead_ids(self):
        """Read lead ids directly from the isolated temp DB."""
        from lead_ingest.db import connect, list_signups
        conn = connect(self._db_path)
        try:
            return [row["id"] for row in list_signups(conn)]
        finally:
            conn.close()
