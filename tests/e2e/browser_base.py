"""Shared Playwright browser automation base for E2E tests.

This base can run against:
  * a locally-spun server (default, when E2E_BASE_URL is not set), using the
    same isolated temp DB as the HTTP E2E suite;
  * a remote/live URL (set E2E_BASE_URL, e.g. the Render instance).

Use E2E_ADMIN_PASSWORD to supply the admin password; without it, admin tests
are skipped when running against a live URL. Local tests use the hard-coded
E2ETestBase admin password.

Run browser tests with:
    python -m unittest discover -s tests/e2e -t tests/e2e -v -k browser

Or via Makefile:
    make test-e2e-browser
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from playwright.sync_api import Page, expect, sync_playwright

# Reuse the HTTP base's server/auth fixtures.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_base import ADMIN_PASSWORD as _LOCAL_ADMIN_PASSWORD  # noqa: E402
from e2e_base import E2ETestBase  # noqa: E402

# Env vars touched by the local server fixture.
_ENV_KEYS = (
    "ADMIN_PASSWORD", "ADMIN_SESSION_SECRET", "CSRF_SECRET",
    "QUIET_HTTP_LOGS", "ENV", "DATABASE_URL", "SHOPIFY_APP_SECRET",
    "COOKIE_SECURE",
)


class BrowserTestBase(unittest.TestCase):
    """Browser automation base with local or remote target support."""

    # Subclasses may override; only used for local server mode.
    rate_limit = (100_000, 60)

    @classmethod
    def setUpClass(cls):
        cls.base_url = os.environ.get("E2E_BASE_URL", "").rstrip("/")
        cls.live = bool(cls.base_url)

        if cls.live:
            cls.host = cls.base_url.replace("https://", "").replace("http://", "").split(":")[0]
            cls.port = 443 if cls.base_url.startswith("https://") else 80
            cls._start_remote()
        else:
            cls._start_local()

        cls.playwright = sync_playwright().start()
        headless = os.environ.get("E2E_HEADLESS", "1") != "0"
        cls.browser = cls.playwright.chromium.launch(headless=headless)
        cls.browser_context = cls.browser.new_context(
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )
        cls.page: Page = cls.browser_context.new_page()

    @classmethod
    def _start_local(cls):
        """Mirror E2ETestBase lifecycle for an isolated in-process server."""
        cls._tempdir = tempfile.TemporaryDirectory()
        cls._db_path = os.path.join(cls._tempdir.name, "e2e.sqlite3")

        from lead_ingest.request_security import RateLimiter
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

        from lead_ingest.db import connect, init_db
        conn = connect(cls._db_path)
        init_db(conn)
        conn.close()

        cls._saved_env = {k: os.environ.get(k) for k in _ENV_KEYS}
        os.environ["ADMIN_PASSWORD"] = _LOCAL_ADMIN_PASSWORD
        os.environ["ADMIN_SESSION_SECRET"] = "e2e-session-secret-very-long-and-random-0123456789"
        os.environ["CSRF_SECRET"] = "e2e-csrf-secret-also-long-and-random-9876543210"
        os.environ["QUIET_HTTP_LOGS"] = "1"
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("ENV", None)
        os.environ.pop("SHOPIFY_APP_SECRET", None)
        os.environ.pop("COOKIE_SECURE", None)

        from lead_ingest.server import Handler
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address
        cls.base_url = f"http://{cls.host}:{cls.port}"

    @classmethod
    def _start_remote(cls):
        cls._tempdir = None
        cls._patches = []
        cls._saved_env = {}
        cls.server = None
        cls.thread = None

    @classmethod
    def tearDownClass(cls):
        cls.browser_context.close()
        cls.browser.close()
        cls.playwright.stop()

        if not cls.live:
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

    def setUp(self):
        # Clear cookies between tests so auth state doesn't leak.
        self.browser_context.clear_cookies()

    # ----- URL helpers ------------------------------------------------
    def url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return self.base_url + ("/" + path.lstrip("/") if path else "")

    def goto(self, path: str):
        self.page.goto(self.url(path), timeout=60_000)

    # ----- Common page interactions ------------------------------------
    def fill_signup_form(self, fields: dict[str, str]):
        """Fill the public signup form using human-friendly selectors."""
        page = self.page
        if "first_name" in fields:
            page.locator('input[name="first_name"]').fill(fields["first_name"])
        if "last_name" in fields:
            page.locator('input[name="last_name"]').fill(fields["last_name"])
        if "email" in fields:
            page.locator('input[name="email"]').fill(fields["email"])
        if "phone" in fields:
            page.locator('input[name="phone"]').fill(fields["phone"])
        if "address_line1" in fields:
            page.locator('input[name="address_line1"]').fill(fields["address_line1"])
        if "address_line2" in fields:
            page.locator('input[name="address_line2"]').fill(fields["address_line2"])
        if "city" in fields:
            page.locator('input[name="city"]').fill(fields["city"])
        if "state" in fields:
            page.locator('input[name="state"]').fill(fields["state"])
        if "postal_code" in fields:
            page.locator('input[name="postal_code"]').fill(fields["postal_code"])

    def check_consent_and_waiver(self):
        self.page.locator('input[name="consent_accepted"]').check()
        self.page.locator('input[name="waiver_accepted"]').check()

    def type_signature(self, name: str):
        self.page.locator('input[name="typed_name"]').fill(name)

    def submit_signup(self):
        self.page.locator('form[action="/signup"] button').click()

    def admin_login(self, password: str | None = None):
        """Navigate to /admin-login and log in."""
        password = password or self.admin_password()
        self.goto("/admin-login")
        self.page.locator('input[name="password"]').fill(password)
        self.page.locator('form[action="/admin-login"] button').click()

    def admin_password(self) -> str:
        if self.live:
            pw = os.environ.get("E2E_ADMIN_PASSWORD", "")
            if not pw:
                raise unittest.SkipTest(
                    "E2E_ADMIN_PASSWORD env var required for live admin browser tests"
                )
            return pw
        return _LOCAL_ADMIN_PASSWORD

    # ----- Assertions -------------------------------------------------
    def assert_page_contains(self, text: str):
        expect(self.page.locator("body")).to_contain_text(text)

    def assert_path(self, path: str):
        expect(self.page).to_have_url(self.url(path))

    def screenshot_on_failure(self, name: str):
        """Call in an addCleanup or exception handler to capture state."""
        try:
            os.makedirs("data/browser-screenshots", exist_ok=True)
            self.page.screenshot(path=f"data/browser-screenshots/{name}.png")
        except Exception:
            pass
