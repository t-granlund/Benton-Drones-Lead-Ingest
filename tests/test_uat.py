"""User Acceptance Testing (UAT) suite for the Benton Drones lead ingest system.

These tests verify complete, business-facing user workflows end-to-end.
Each scenario answers: "Can a real user successfully complete this workflow?"

Scenarios covered:
  1. Complete lead capture flow (landing → signup → database persistence)
  2. Admin review flow (login → dashboard → lead detail → print view)
  3. Export flow (CSV + GeoJSON with lead and signature data)
  4. JIRA fallback flow (env vars not set → local queue, no HTTP call)
  5. JIRA success flow (mocked endpoint → ticket stored in database)
  6. Variant tracking flow (source/campaign/variant metadata persisted)
  7. Security / abuse flow (honeypot, CSRF, admin auth, export auth)
  8. PDF fallback flow (fpdf2 absent → redirect to print view)

Test framework: Python stdlib unittest (no external dependencies).
Each scenario class gets its own isolated temp database and server instance.
"""
import http.client
import json
import os
import re
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlencode

from lead_ingest.request_security import RateLimiter
from lead_ingest.server import Handler


# ---------------------------------------------------------------------------
# Base class: isolated HTTP server with temp database
# ---------------------------------------------------------------------------

class UATServerBase(unittest.TestCase):
    """Base class providing a running test server with an isolated temp database.

    Each UAT scenario subclass inherits this and gets its own fresh server
    and database via setUpClass, ensuring full test independence with no
    shared mutable state between scenarios.
    """

    @classmethod
    def setUpClass(cls):
        # Temp directory and database file
        cls._tempdir = tempfile.TemporaryDirectory()
        cls._db_path = os.path.join(cls._tempdir.name, "uat_test.sqlite3")

        # Patch the DB path the server uses so tests are isolated
        cls._patcher_db = patch("lead_ingest.server.DEFAULT_DB_PATH", cls._db_path)
        cls._patcher_db.start()

        # Patch the rate limiter with a high limit so tests don't throttle
        cls._patcher_rl = patch(
            "lead_ingest.server.RATE_LIMITER",
            RateLimiter(max_requests=100_000, window_seconds=60),
        )
        cls._patcher_rl.start()

        # Set admin credentials for the test server
        cls._old_password = os.environ.get("ADMIN_PASSWORD")
        cls._old_secret = os.environ.get("ADMIN_SESSION_SECRET")
        cls._old_quiet = os.environ.get("QUIET_HTTP_LOGS")
        os.environ["ADMIN_PASSWORD"] = "uat-admin-password"
        os.environ["ADMIN_SESSION_SECRET"] = "uat-admin-secret"
        os.environ["QUIET_HTTP_LOGS"] = "1"

        # Start server on a random port
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
        cls._restore_env("ADMIN_PASSWORD", cls._old_password)
        cls._restore_env("ADMIN_SESSION_SECRET", cls._old_secret)
        cls._restore_env("QUIET_HTTP_LOGS", cls._old_quiet)

    @staticmethod
    def _restore_env(key, value):
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    # --- HTTP helpers ---

    def request(self, method, path, body=None, headers=None):
        """Make an HTTP request to the test server. Returns (response, content)."""
        conn = http.client.HTTPConnection(self.host, self.port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        content = response.read()
        conn.close()
        return response, content

    def extract_csrf(self, content):
        """Extract a CSRF token from an HTML page."""
        match = re.search(rb'name="csrf_token" value="([^"]+)"', content)
        self.assertIsNotNone(match, "CSRF token not found in page")
        return match.group(1).decode()

    def login_cookie(self):
        """Log in as admin and return the Set-Cookie header value."""
        _, content = self.request("GET", "/admin-login")
        body = urlencode({
            "password": "uat-admin-password",
            "csrf_token": self.extract_csrf(content),
        })
        response, _ = self.request(
            "POST", "/admin-login", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 302, "Admin login should redirect to dashboard")
        return response.getheader("Set-Cookie")

    def submit_signup(self, **overrides):
        """GET /signup, extract CSRF, POST a valid signup form. Returns (response, content)."""
        signup_path = overrides.pop("_signup_path", "/signup")
        _, content = self.request("GET", signup_path)
        csrf = self.extract_csrf(content)
        fields = {
            "first_name": "Jane",
            "last_name": "Drone",
            "email": "jane-uat@example.com",
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
        return self.request(
            "POST", "/signup", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def extract_lead_id(self, admin_html, email):
        """Extract a lead ID from the admin dashboard HTML by email."""
        email_bytes = email.encode()
        email_index = admin_html.find(email_bytes)
        self.assertNotEqual(email_index, -1, f"Email {email} not found in admin page")
        row_start = admin_html.rfind(b"<tr", 0, email_index)
        row_end = admin_html.find(b"</tr>", email_index)
        row = admin_html[row_start:row_end]
        match = re.search(rb"/admin/lead/(\d+)", row)
        self.assertIsNotNone(match, "Lead link not found in admin table row")
        return match.group(1).decode()

    def db_conn(self):
        """Return a sqlite3 connection to the test database."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn


# ---------------------------------------------------------------------------
# Scenario 1: Complete lead capture flow
# ---------------------------------------------------------------------------

class TestCompleteLeadCaptureFlow(UATServerBase):
    """Scenario 1: Complete lead capture flow.

    Business value: A visitor must be able to discover Benton Drones via the
    landing page, click through to the signup form, provide consent and a
    typed-name signature, and have their lead persisted to the database with
    a full audit trail. This is the core revenue-generating workflow.
    """

    def test_landing_page_loads_with_branding_and_cta(self):
        """Visitor loads /landing-page.html and sees Benton Drones branding with a CTA to /signup."""
        response, content = self.request("GET", "/landing-page.html")
        self.assertEqual(response.status, 200)
        self.assertIn(b"Benton Drones", content)
        self.assertIn(b"/signup", content)
        # Verify there is a visible call-to-action link to signup
        self.assertIn(b"Sign up", content)

    def test_signup_form_has_consent_waiver_and_signature_fields(self):
        """The signup form includes consent checkbox, waiver checkbox, and typed-name field."""
        response, content = self.request("GET", "/signup")
        self.assertEqual(response.status, 200)
        self.assertIn(b'name="consent_accepted"', content)
        self.assertIn(b'name="waiver_accepted"', content)
        self.assertIn(b'name="typed_name"', content)
        # Waiver text should be present on the page
        self.assertIn(b"waiver", content.lower())
        # CSRF protection should be present
        self.assertIn(b'name="csrf_token"', content)

    def test_signup_submission_succeeds(self):
        """Submitting a valid form with consent and typed-name signature returns a success page."""
        response, content = self.submit_signup(email="capture-success@example.com")
        self.assertEqual(response.status, 200)
        self.assertIn(b"Your signup was saved", content)

    def test_lead_persisted_with_consent_and_signature(self):
        """The submitted lead, consent record, and signature record are all stored in SQLite."""
        email = "capture-persist@example.com"
        self.submit_signup(email=email)

        conn = self.db_conn()
        try:
            signup = conn.execute(
                "SELECT * FROM signups WHERE email = ?", (email,)
            ).fetchone()
            self.assertIsNotNone(signup, "Lead should be in signups table")
            self.assertEqual(signup["first_name"], "Jane")
            self.assertEqual(signup["last_name"], "Drone")

            consent = conn.execute(
                "SELECT * FROM consent_records WHERE signup_id = ?", (signup["id"],)
            ).fetchone()
            self.assertIsNotNone(consent, "Consent record should exist")
            self.assertEqual(consent["accepted"], 1)

            signature = conn.execute(
                "SELECT * FROM signatures WHERE signup_id = ?", (signup["id"],)
            ).fetchone()
            self.assertIsNotNone(signature, "Signature record should exist")
            self.assertEqual(signature["full_name_typed"], "Jane Drone")
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Scenario 2: Admin review flow
# ---------------------------------------------------------------------------

class TestAdminReviewFlow(UATServerBase):
    """Scenario 2: Admin review flow.

    Business value: An admin must be able to log in, view the dashboard,
    drill into a specific lead, see the full consent and signature audit
    trail, and print a consent form for records. This is the operational
    workflow for reviewing and processing captured leads.
    """

    def setUp(self):
        # Create a lead for this test's admin to review
        self.lead_email = "admin-review@example.com"
        self.submit_signup(email=self.lead_email)

    def test_admin_login_succeeds_and_redirects(self):
        """Admin logs in with correct password and is redirected to the dashboard."""
        cookie = self.login_cookie()
        self.assertIsNotNone(cookie)
        self.assertIn("bd_admin_session", cookie)

    def test_admin_dashboard_shows_lead_in_recent_leads(self):
        """Admin dashboard lists the newly captured lead in the recent leads table."""
        cookie = self.login_cookie()
        response, content = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(self.lead_email.encode(), content)
        self.assertIn(b"Recent leads", content)
        self.assertIn(b"/admin/lead/", content)

    def test_lead_detail_shows_complete_information(self):
        """Lead detail page shows contact info, consent record, signature, and geocode status."""
        cookie = self.login_cookie()
        _, admin_content = self.request("GET", "/admin", headers={"Cookie": cookie})
        lead_id = self.extract_lead_id(admin_content, self.lead_email)

        response, content = self.request(
            "GET", f"/admin/lead/{lead_id}", headers={"Cookie": cookie}
        )
        self.assertEqual(response.status, 200)
        self.assertIn(self.lead_email.encode(), content)
        self.assertIn(b"Consent record", content)
        self.assertIn(b"Signature record", content)
        self.assertIn(b"Geocode status", content)
        # The typed name should appear in the signature record section
        self.assertIn(b"Jane Drone", content)

    def test_print_view_shows_consent_form(self):
        """Print view renders a printable consent form with signature and waiver details."""
        cookie = self.login_cookie()
        _, admin_content = self.request("GET", "/admin", headers={"Cookie": cookie})
        lead_id = self.extract_lead_id(admin_content, self.lead_email)

        response, content = self.request(
            "GET", f"/admin/lead/{lead_id}/print", headers={"Cookie": cookie}
        )
        self.assertEqual(response.status, 200)
        self.assertIn(b"Consent & Waiver Form", content)
        self.assertIn(self.lead_email.encode(), content)
        self.assertIn(b"Signature", content)
        self.assertIn(b"window.print()", content)


# ---------------------------------------------------------------------------
# Scenario 3: Export flow
# ---------------------------------------------------------------------------

class TestExportFlow(UATServerBase):
    """Scenario 3: Export flow.

    Business value: Admin must be able to export lead data as CSV (with
    signature metadata for compliance) and GeoJSON (with geocoded
    coordinates for mapping). These exports feed downstream business
    processes like CRM import and territory analysis.
    """

    def setUp(self):
        self.lead_email = "export-test@example.com"
        self.submit_signup(email=self.lead_email)

    def test_csv_export_contains_lead_and_signature_metadata(self):
        """CSV export includes the lead's email and signature metadata columns."""
        cookie = self.login_cookie()
        response, content = self.request("GET", "/export/csv", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn("text/csv", response.getheader("Content-Type", ""))
        self.assertIn(self.lead_email.encode(), content)
        # CSV header should include signature metadata columns
        self.assertIn(b"signed_name", content)
        self.assertIn(b"signed_at", content)
        self.assertIn(b"waiver_version", content)
        self.assertIn(b"consent_version", content)

    def test_geojson_export_contains_geocoded_lead(self):
        """GeoJSON export includes the geocoded lead as a Feature with coordinates."""
        cookie = self.login_cookie()
        response, content = self.request("GET", "/export/geojson", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn("geo+json", response.getheader("Content-Type", ""))

        data = json.loads(content)
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertGreater(len(data["features"]), 0)

        # Find our lead in the features
        emails = [f["properties"]["email"] for f in data["features"]]
        self.assertIn(self.lead_email, emails)

        our_feature = next(
            f for f in data["features"] if f["properties"]["email"] == self.lead_email
        )
        self.assertEqual(our_feature["geometry"]["type"], "Point")
        self.assertEqual(len(our_feature["geometry"]["coordinates"]), 2)
        # Coordinates are [longitude, latitude]
        self.assertIsNotNone(our_feature["geometry"]["coordinates"][0])
        self.assertIsNotNone(our_feature["geometry"]["coordinates"][1])


# ---------------------------------------------------------------------------
# Scenario 4: JIRA fallback flow
# ---------------------------------------------------------------------------

class TestJiraFallbackFlow(UATServerBase):
    """Scenario 4: JIRA fallback flow.

    Business value: When JIRA is not configured, signups must be queued
    locally so no lead is lost. The system must NOT attempt any external
    HTTP call when config is missing. This ensures leads are never dropped
    even when integrations are down or unconfigured.
    """

    def setUp(self):
        # Save and clear JIRA env vars
        self._jira_vars = [
            "JIRA_BASE_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY",
        ]
        self._old_jira = {v: os.environ.pop(v, None) for v in self._jira_vars}

    def tearDown(self):
        for v, val in self._old_jira.items():
            if val is not None:
                os.environ[v] = val

    def test_signup_queued_when_jira_not_configured(self):
        """When JIRA env vars are not set, the signup is queued in jira_queue with status pending."""
        email = "jira-fallback@example.com"
        self.submit_signup(email=email)

        conn = self.db_conn()
        try:
            signup = conn.execute(
                "SELECT * FROM signups WHERE email = ?", (email,)
            ).fetchone()
            self.assertIsNotNone(signup, "Lead should exist in signups table")

            queue = conn.execute(
                "SELECT * FROM jira_queue WHERE signup_id = ? ORDER BY id DESC LIMIT 1",
                (signup["id"],),
            ).fetchone()
            self.assertIsNotNone(queue, "JIRA queue entry should exist")
            self.assertEqual(queue["status"], "pending")
            self.assertIn("config", queue["error_message"].lower())
        finally:
            conn.close()

    def test_no_external_http_call_attempted(self):
        """No external HTTP call is made when JIRA is not configured."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            self.submit_signup(email="jira-no-call@example.com")
            mock_urlopen.assert_not_called()

        # Verify no jira_tickets row was created
        conn = self.db_conn()
        try:
            signup = conn.execute(
                "SELECT * FROM signups WHERE email = ?", ("jira-no-call@example.com",)
            ).fetchone()
            self.assertIsNotNone(signup)
            ticket = conn.execute(
                "SELECT * FROM jira_tickets WHERE signup_id = ?", (signup["id"],)
            ).fetchone()
            self.assertIsNone(
                ticket,
                "No JIRA ticket should be created when config is missing",
            )
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Scenario 5: JIRA success flow
# ---------------------------------------------------------------------------

class TestJiraSuccessFlow(UATServerBase):
    """Scenario 5: JIRA success flow.

    Business value: When JIRA is configured, a signup should automatically
    create a JIRA ticket so the sales team can track and follow up on leads
    in their existing workflow tool. The ticket key and URL should be stored
    in the database for traceability.
    """

    def setUp(self):
        # Set JIRA env vars so jira_config_from_env() returns a valid config
        self._jira_vars = [
            "JIRA_BASE_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY",
        ]
        self._old_jira = {v: os.environ.get(v) for v in self._jira_vars}
        os.environ["JIRA_BASE_URL"] = "https://test.atlassian.net"
        os.environ["JIRA_USER_EMAIL"] = "admin@test.com"
        os.environ["JIRA_API_TOKEN"] = "test-token"
        os.environ["JIRA_PROJECT_KEY"] = "BDS"

    def tearDown(self):
        for v, val in self._old_jira.items():
            if val is not None:
                os.environ[v] = val
            else:
                os.environ.pop(v, None)

    def test_jira_ticket_created_and_stored(self):
        """When JIRA is configured, a ticket is created and stored in jira_tickets table."""
        email = "jira-success@example.com"
        mock_ticket_key = "BDS-TEST-123"

        # Mock create_jira_ticket in the server's namespace (it was imported from jira.py)
        with patch("lead_ingest.server.create_jira_ticket", return_value=mock_ticket_key):
            self.submit_signup(email=email)

        conn = self.db_conn()
        try:
            signup = conn.execute(
                "SELECT * FROM signups WHERE email = ?", (email,)
            ).fetchone()
            self.assertIsNotNone(signup, "Lead should exist in signups table")

            ticket = conn.execute(
                "SELECT * FROM jira_tickets WHERE signup_id = ?", (signup["id"],)
            ).fetchone()
            self.assertIsNotNone(ticket, "JIRA ticket should be stored in database")
            self.assertEqual(ticket["ticket_key"], mock_ticket_key)
            self.assertIn("browse", ticket["jira_issue_url"])
            self.assertIn(mock_ticket_key, ticket["jira_issue_url"])

            # No jira_queue entry should exist — when config is set and ticket
            # creation succeeds, the ticket is stored directly in jira_tickets
            # without going through the queue.
            queue = conn.execute(
                "SELECT * FROM jira_queue WHERE signup_id = ?",
                (signup["id"],),
            ).fetchone()
            self.assertIsNone(
                queue,
                "No jira_queue entry should exist when ticket creation succeeds",
            )
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Scenario 6: Variant tracking flow
# ---------------------------------------------------------------------------

class TestVariantTrackingFlow(UATServerBase):
    """Scenario 6: Variant tracking flow.

    Business value: Marketing campaigns need to track which landing page
    variant and traffic source produced each lead. The system must persist
    source, campaign, and variant_slug metadata with each signup so ROI
    can be measured per channel.
    """

    def test_variant_source_campaign_stored_correctly(self):
        """A signup submitted with variant metadata stores source, campaign, and variant_slug in the DB."""
        # Visit the variant signup page (slug in URL path, query params for attribution)
        response, content = self.request(
            "GET", "/signup/facebook-ad?source=facebook&campaign=summer2026"
        )
        self.assertEqual(response.status, 200)
        csrf = self.extract_csrf(content)

        # Submit the form with variant metadata
        fields = {
            "first_name": "Variant",
            "last_name": "Tracker",
            "email": "variant-test@example.com",
            "phone": "555-2000",
            "address_line1": "200 Ad Way",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "Variant Tracker",
            "csrf_token": csrf,
            "source": "facebook",
            "campaign": "summer2026",
            "variant_slug": "facebook-ad",
        }
        body = urlencode(fields)
        response, content = self.request(
            "POST", "/signup", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 200)
        self.assertIn(b"Your signup was saved", content)

        # Verify DB has the correct metadata
        conn = self.db_conn()
        try:
            signup = conn.execute(
                "SELECT * FROM signups WHERE email = ?", ("variant-test@example.com",)
            ).fetchone()
            self.assertIsNotNone(signup)
            self.assertEqual(signup["source"], "facebook")
            self.assertEqual(signup["campaign"], "summer2026")
            self.assertEqual(signup["variant_slug"], "facebook-ad")
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Scenario 7: Security / abuse flow
# ---------------------------------------------------------------------------

class TestSecurityAbuseFlow(UATServerBase):
    """Scenario 7: Security / abuse flow.

    Business value: The system must resist automated abuse (bot spam via
    honeypot), CSRF attacks, and unauthorized access to admin features.
    This protects lead data integrity and prevents malicious signups.
    """

    def test_honeypot_field_filled_rejected(self):
        """A signup with the honeypot field filled is rejected with 400."""
        response, content = self.submit_signup(
            email="honeypot@example.com",
            website_url="http://spam.example.com",
        )
        self.assertEqual(response.status, 400)
        self.assertIn(b"submission rejected", content)

    def test_missing_csrf_rejected(self):
        """A signup without a valid CSRF token is rejected with 400."""
        body = urlencode({
            "first_name": "No",
            "last_name": "Csrf",
            "email": "no-csrf@example.com",
            "address_line1": "100 Flight Path",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "No Csrf",
            # Deliberately no csrf_token
        })
        response, content = self.request(
            "POST", "/signup", body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 400)
        self.assertIn(b"invalid CSRF token", content)

    def test_admin_without_login_redirected(self):
        """Accessing /admin without authentication redirects to /admin-login."""
        response, _ = self.request("GET", "/admin")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")

    def test_export_without_login_returns_403(self):
        """Accessing /export/csv without authentication returns 403 Forbidden."""
        response, content = self.request("GET", "/export/csv")
        self.assertEqual(response.status, 403)
        self.assertIn(b"admin login required", content)


# ---------------------------------------------------------------------------
# Scenario 8: PDF fallback flow
# ---------------------------------------------------------------------------

class TestPdfFallbackFlow(UATServerBase):
    """Scenario 8: PDF fallback flow.

    Business value: When the optional fpdf2 library is not installed, the
    system must gracefully fall back to the printable HTML view rather
    than crashing. This ensures consent forms can always be printed for
    records, even on minimal deployments without extra dependencies.
    """

    def setUp(self):
        self.lead_email = "pdf-fallback@example.com"
        self.submit_signup(email=self.lead_email)

    def test_pdf_route_falls_back_to_print_view(self):
        """When fpdf2 is unavailable, /admin/lead/<id>/pdf redirects to the print view (302)."""
        cookie = self.login_cookie()
        _, admin_content = self.request("GET", "/admin", headers={"Cookie": cookie})
        lead_id = self.extract_lead_id(admin_content, self.lead_email)

        # Mock try_render_pdf to return None (simulating fpdf2 not installed)
        with patch("lead_ingest.server.try_render_pdf", return_value=None):
            response, _ = self.request(
                "GET", f"/admin/lead/{lead_id}/pdf", headers={"Cookie": cookie}
            )

        self.assertEqual(response.status, 302)
        location = response.getheader("Location", "")
        self.assertIn("/print", location)


if __name__ == "__main__":
    unittest.main()
