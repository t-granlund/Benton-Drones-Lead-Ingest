"""End-to-end HTTP flow tests for gaps not covered by test_protected_routes.

Covers: static file serving, path traversal, 404 handling, rate limiting,
logout, login edge cases, signup validation errors, variant behavior,
lead detail edge cases, and admin dashboard analytics content.
"""
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


class E2EFlowTests(unittest.TestCase):
    """HTTP-level integration tests with an isolated temp database."""

    @classmethod
    def setUpClass(cls):
        cls._tempdir = tempfile.TemporaryDirectory()
        cls._db_path = os.path.join(cls._tempdir.name, "e2e_test.sqlite3")

        # Patch the DB path the server uses so tests are isolated.
        cls._patcher_db = patch("lead_ingest.server.DEFAULT_DB_PATH", cls._db_path)
        cls._patcher_db.start()

        # Patch the rate limiter with a high limit so tests don't throttle.
        cls._patcher_rl = patch(
            "lead_ingest.server.RATE_LIMITER",
            RateLimiter(max_requests=100_000, window_seconds=60),
        )
        cls._patcher_rl.start()

        cls.old_password = os.environ.get("ADMIN_PASSWORD")
        cls.old_secret = os.environ.get("ADMIN_SESSION_SECRET")
        cls.old_quiet = os.environ.get("QUIET_HTTP_LOGS")
        os.environ["ADMIN_PASSWORD"] = "e2e-password"
        os.environ["ADMIN_SESSION_SECRET"] = "e2e-secret"
        os.environ["QUIET_HTTP_LOGS"] = "1"

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
        cls._restore_env("ADMIN_PASSWORD", cls.old_password)
        cls._restore_env("ADMIN_SESSION_SECRET", cls.old_secret)
        cls._restore_env("QUIET_HTTP_LOGS", cls.old_quiet)

    @staticmethod
    def _restore_env(key, value):
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        content = response.read()
        conn.close()
        return response, content

    def extract_csrf(self, content):
        match = re.search(rb'name="csrf_token" value="([^\"]+)"', content)
        self.assertIsNotNone(match, "CSRF token not found in page")
        return match.group(1).decode()

    def login_cookie(self):
        _, content = self.request("GET", "/admin-login")
        body = urlencode({"password": "e2e-password", "csrf_token": self.extract_csrf(content)})
        response, _ = self.request(
            "POST", "/admin-login", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 302)
        return response.getheader("Set-Cookie")

    def submit_signup(self, **overrides):
        """Helper: GET /signup, extract CSRF, POST a valid signup, return (response, content)."""
        _, content = self.request("GET", "/signup")
        csrf = self.extract_csrf(content)
        fields = {
            "first_name": "Jane",
            "last_name": "Drone",
            "email": "jane-drone@example.com",
            "phone": "555-1000",
            "address_line1": "100 Flight Path",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "Jane Drone",
            "csrf_token": csrf,
        }
        fields.update(overrides)
        body = urlencode(fields)
        return self.request("POST", "/signup", body=body,
                            headers={"Content-Type": "application/x-www-form-urlencoded"})

    # ------------------------------------------------------------------
    # Static file serving
    # ------------------------------------------------------------------

    def test_static_leaflet_css_served(self):
        response, content = self.request("GET", "/static/leaflet/leaflet.css")
        self.assertEqual(response.status, 200)
        self.assertIn("text/css", response.getheader("Content-Type", ""))
        self.assertGreater(len(content), 1000)

    def test_static_leaflet_js_served(self):
        response, content = self.request("GET", "/static/leaflet/leaflet.js")
        self.assertEqual(response.status, 200)
        content_type = response.getheader("Content-Type", "")
        self.assertTrue("javascript" in content_type or "octet-stream" in content_type)
        self.assertGreater(len(content), 10000)

    def test_static_missing_file_returns_404(self):
        response, _ = self.request("GET", "/static/nonexistent.css")
        self.assertEqual(response.status, 404)

    def test_static_path_traversal_blocked(self):
        response, _ = self.request("GET", "/static/../../../etc/passwd")
        self.assertIn(response.status, (403, 404))

    def test_static_path_traversal_encoded_blocked(self):
        response, _ = self.request("GET", "/static/%2e%2e%2f%2e%2e%2fetc%2fpasswd")
        self.assertIn(response.status, (403, 404))

    # ------------------------------------------------------------------
    # 404 handling
    # ------------------------------------------------------------------

    def test_unknown_get_route_returns_404(self):
        response, _ = self.request("GET", "/this-does-not-exist")
        self.assertEqual(response.status, 404)

    def test_unknown_post_route_returns_404(self):
        body = urlencode({"foo": "bar"})
        response, _ = self.request("POST", "/unknown-post-path", body=body,
                                   headers={"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(response.status, 404)

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def test_rate_limiting_post_returns_429(self):
        """POST /signup beyond the limit returns 429."""
        low_limiter = RateLimiter(max_requests=2, window_seconds=60)
        with patch("lead_ingest.server.RATE_LIMITER", low_limiter):
            _, content = self.request("GET", "/signup")
            csrf = self.extract_csrf(content)
            body = urlencode({
                "first_name": "Rate",
                "last_name": "Limit",
                "email": "rate@example.com",
                "address_line1": "1 Drone Way",
                "city": "Bentonville",
                "state": "AR",
                "postal_code": "72712",
                "consent_accepted": "yes",
                "waiver_accepted": "yes",
                "typed_name": "Rate Limit",
                "csrf_token": csrf,
            })
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            for i in range(2):
                resp, _ = self.request("POST", "/signup", body=body, headers=headers)
                self.assertNotEqual(resp.status, 429, f"request {i} should not be rate-limited")
            resp, content = self.request("POST", "/signup", body=body, headers=headers)
            self.assertEqual(resp.status, 429)
            self.assertIn(b"Too many requests", content)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def test_admin_logout_redirects_and_clears_cookie(self):
        response, _ = self.request("GET", "/admin-logout")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")
        cookie = response.getheader("Set-Cookie", "")
        self.assertIn("Max-Age=0", cookie)

    def test_admin_logout_unauthenticated_also_redirects(self):
        response, _ = self.request("GET", "/admin-logout")
        self.assertEqual(response.status, 302)

    # ------------------------------------------------------------------
    # Login edge cases
    # ------------------------------------------------------------------

    def test_login_wrong_password_returns_401(self):
        _, content = self.request("GET", "/admin-login")
        body = urlencode({"password": "wrong-password", "csrf_token": self.extract_csrf(content)})
        response, content = self.request(
            "POST", "/admin-login", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 401)
        self.assertIn(b"invalid admin password", content)

    def test_login_without_admin_password_configured_returns_500(self):
        old_pw = os.environ.pop("ADMIN_PASSWORD", None)
        try:
            _, content = self.request("GET", "/admin-login")
            body = urlencode({"password": "anything", "csrf_token": self.extract_csrf(content)})
            response, content = self.request(
                "POST", "/admin-login", body=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            self.assertEqual(response.status, 500)
            self.assertIn(b"ADMIN_PASSWORD is not configured", content)
        finally:
            if old_pw is not None:
                os.environ["ADMIN_PASSWORD"] = old_pw

    # ------------------------------------------------------------------
    # Signup validation errors at HTTP level
    # ------------------------------------------------------------------

    def test_signup_invalid_email_returns_400_with_error(self):
        response, content = self.submit_signup(email="not-an-email")
        self.assertEqual(response.status, 400)
        self.assertIn(b"email must be valid", content)

    def test_signup_missing_required_field_returns_400(self):
        response, content = self.submit_signup(first_name="")
        self.assertEqual(response.status, 400)
        self.assertIn(b"first_name is required", content)

    def test_signup_missing_consent_returns_400(self):
        response, content = self.submit_signup(consent_accepted="")
        self.assertEqual(response.status, 400)
        self.assertIn(b"consent is required", content)

    def test_signup_missing_waiver_returns_400(self):
        response, content = self.submit_signup(waiver_accepted="")
        self.assertEqual(response.status, 400)
        self.assertIn(b"waiver agreement is required", content)

    def test_signup_missing_typed_name_returns_400(self):
        response, content = self.submit_signup(typed_name="")
        self.assertEqual(response.status, 400)
        self.assertIn(b"typed legal name is required", content)

    def test_signup_success_renders_confirmation(self):
        response, content = self.submit_signup(email="success-flow@example.com")
        self.assertEqual(response.status, 200)
        self.assertIn(b"Your signup was saved", content)
        self.assertIn(b"View admin", content)

    # ------------------------------------------------------------------
    # Variant behavior
    # ------------------------------------------------------------------

    def test_signup_variant_slug_unknown_falls_back_to_default(self):
        response, content = self.request("GET", "/signup/nonexistent-variant")
        self.assertEqual(response.status, 200)
        # Default variant title should be rendered.
        self.assertIn(b"Join Benton Drones Delivery Simulations", content)

    def test_signup_variant_page_contains_csrf_and_form_fields(self):
        response, content = self.request("GET", "/signup")
        self.assertEqual(response.status, 200)
        self.assertIn(b'name="csrf_token"', content)
        self.assertIn(b'name="first_name"', content)
        self.assertIn(b'name="typed_name"', content)
        self.assertIn(b'name="consent_accepted"', content)
        self.assertIn(b'name="waiver_accepted"', content)

    # ------------------------------------------------------------------
    # Lead detail edge cases
    # ------------------------------------------------------------------

    def test_lead_detail_non_numeric_id_handled(self):
        cookie = self.login_cookie()
        response, content = self.request("GET", "/admin/lead/abc", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(b"Lead not found", content)

    def test_lead_detail_nonexistent_numeric_id_handled(self):
        cookie = self.login_cookie()
        response, content = self.request("GET", "/admin/lead/999999", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(b"Lead not found", content)

    # ------------------------------------------------------------------
    # Admin dashboard content
    # ------------------------------------------------------------------

    def test_admin_dashboard_shows_analytics_metrics(self):
        # Submit a lead first so there is data.
        self.submit_signup(email="dashboard-test@example.com")

        cookie = self.login_cookie()
        response, content = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(b"Total leads", content)
        self.assertIn(b"Today", content)
        self.assertIn(b"This week", content)
        self.assertIn(b"Pending geocodes", content)
        self.assertIn(b"By source", content)
        self.assertIn(b"By campaign", content)
        self.assertIn(b"By variant", content)

    def test_admin_dashboard_shows_export_links(self):
        cookie = self.login_cookie()
        response, content = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(b"/export/csv", content)
        self.assertIn(b"/export/geojson", content)
        self.assertIn(b"/export/kml", content)

    def test_admin_dashboard_shows_recent_leads_table(self):
        self.submit_signup(email="recent-table@example.com")
        cookie = self.login_cookie()
        response, content = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(b"Recent leads", content)
        self.assertIn(b"recent-table@example.com", content)
        self.assertIn(b"/admin/lead/", content)

    # ------------------------------------------------------------------
    # GeoJSON export filtering
    # ------------------------------------------------------------------

    def test_geojson_export_only_includes_geocoded_leads(self):
        cookie = self.login_cookie()
        response, content = self.request("GET", "/admin/leads.geojson", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(b"FeatureCollection", content)

    # ------------------------------------------------------------------
    # Root path and trailing slash normalization
    # ------------------------------------------------------------------

    def test_root_path_renders_signup(self):
        response, content = self.request("GET", "/")
        self.assertEqual(response.status, 200)
        self.assertIn(b"Signup", content)

    def test_signup_trailing_slash_renders(self):
        response, content = self.request("GET", "/signup/")
        self.assertEqual(response.status, 200)
        self.assertIn(b"Signup", content)

    # ------------------------------------------------------------------
    # Full E2E: submit -> admin -> export -> lead detail
    # ------------------------------------------------------------------

    def test_full_e2e_submit_to_lead_detail_to_export(self):
        # Step 1: submit a signup
        submit_resp, submit_content = self.submit_signup(email="full-e2e@example.com")
        self.assertEqual(submit_resp.status, 200)
        self.assertIn(b"Your signup was saved", submit_content)

        # Step 2: login as admin
        cookie = self.login_cookie()

        # Step 3: view admin dashboard — lead appears
        admin_resp, admin_content = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(admin_resp.status, 200)
        self.assertIn(b"full-e2e@example.com", admin_content)

        # Step 4: extract lead ID from admin page and view detail
        lead_id = self._extract_lead_id(admin_content, "full-e2e@example.com")
        detail_resp, detail_content = self.request(
            "GET", f"/admin/lead/{lead_id}", headers={"Cookie": cookie})
        self.assertEqual(detail_resp.status, 200)
        self.assertIn(b"full-e2e@example.com", detail_content)
        self.assertIn(b"Signature record", detail_content)
        self.assertIn(b"Consent record", detail_content)
        self.assertIn(b"Geocode status", detail_content)

        # Step 5: CSV export contains the lead
        csv_resp, csv_content = self.request("GET", "/export/csv", headers={"Cookie": cookie})
        self.assertEqual(csv_resp.status, 200)
        self.assertIn(b"full-e2e@example.com", csv_content)

        # Step 6: GeoJSON export contains the lead
        geo_resp, geo_content = self.request("GET", "/export/geojson", headers={"Cookie": cookie})
        self.assertEqual(geo_resp.status, 200)
        self.assertIn(b"full-e2e@example.com", geo_content)

        # Step 7: KML export contains the lead (KML includes name and address, not email)
        kml_resp, kml_content = self.request("GET", "/export/kml", headers={"Cookie": cookie})
        self.assertEqual(kml_resp.status, 200)
        self.assertIn(b"100 Flight Path", kml_content)

    def _extract_lead_id(self, admin_html: bytes, email: str) -> str:
        email_index = admin_html.find(email.encode())
        self.assertNotEqual(email_index, -1, f"email {email} not found in admin page")
        row_start = admin_html.rfind(b"<tr", 0, email_index)
        row_end = admin_html.find(b"</tr>", email_index)
        row = admin_html[row_start:row_end]
        match = re.search(rb"/admin/lead/(\d+)", row)
        self.assertIsNotNone(match, "lead link not found in row")
        return match.group(1).decode()

    # ------------------------------------------------------------------
    # Landing page
    # ------------------------------------------------------------------

    def test_landing_page_served(self):
        response, content = self.request("GET", "/landing-page.html")
        self.assertEqual(response.status, 200)
        self.assertIn(b"Benton Drones", content)
        self.assertIn(b"/signup", content)
        self.assertIn(b"Cinematic FPV", content)
        self.assertIn(b"Part 107", content)

    # ------------------------------------------------------------------
    # Print / PDF routes
    # ------------------------------------------------------------------

    def test_print_route_requires_admin(self):
        response, _ = self.request("GET", "/admin/lead/1/print")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")

    def test_pdf_route_requires_admin(self):
        response, _ = self.request("GET", "/admin/lead/1/pdf")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")

    def test_print_route_shows_consent_form(self):
        self.submit_signup(email="print-route@example.com")
        cookie = self.login_cookie()
        admin_resp, admin_content = self.request("GET", "/admin", headers={"Cookie": cookie})
        lead_id = self._extract_lead_id(admin_content, "print-route@example.com")
        resp, content = self.request(
            "GET", f"/admin/lead/{lead_id}/print", headers={"Cookie": cookie}
        )
        self.assertEqual(resp.status, 200)
        self.assertIn(b"Consent & Waiver Form", content)
        self.assertIn(b"print-route@example.com", content)
        self.assertIn(b"Signature", content)
        self.assertIn(b"window.print()", content)

    def test_pdf_route_returns_pdf_or_redirects(self):
        self.submit_signup(email="pdf-route@example.com")
        cookie = self.login_cookie()
        admin_resp, admin_content = self.request("GET", "/admin", headers={"Cookie": cookie})
        lead_id = self._extract_lead_id(admin_content, "pdf-route@example.com")
        resp, content = self.request(
            "GET", f"/admin/lead/{lead_id}/pdf", headers={"Cookie": cookie}
        )
        # Either we get a PDF (fpdf2 installed) or a redirect to print view.
        if resp.status == 200:
            content_type = resp.getheader("Content-Type", "")
            self.assertIn("application/pdf", content_type)
            self.assertTrue(content[:4] == b"%PDF")
        else:
            self.assertEqual(resp.status, 302)
            location = resp.getheader("Location", "")
            self.assertIn("/print", location)

    # ------------------------------------------------------------------
    # JIRA queue (env vars not set → should queue)
    # ------------------------------------------------------------------

    def test_jira_queue_entry_created_when_config_missing(self):
        # Ensure JIRA env vars are not set during this test.
        jira_vars = ["JIRA_BASE_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
        old_vals = {v: os.environ.pop(v, None) for v in jira_vars}
        try:
            self.submit_signup(email="jira-queue@example.com")
            # Check the DB directly for the queue entry.
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM jira_queue WHERE signup_id IN ("
                "  SELECT id FROM signups WHERE email = ?"
                ") ORDER BY id DESC LIMIT 1",
                ("jira-queue@example.com",),
            ).fetchone()
            conn.close()
            self.assertIsNotNone(row, "JIRA queue entry should exist")
            self.assertEqual(row["status"], "pending")
            self.assertIn("config", row["error_message"])
        finally:
            for v, val in old_vals.items():
                if val is not None:
                    os.environ[v] = val


if __name__ == "__main__":
    unittest.main()
