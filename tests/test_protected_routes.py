import http.client
import os
import re
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

from lead_ingest.server import Handler


class ProtectedRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_password = os.environ.get("ADMIN_PASSWORD")
        cls.old_secret = os.environ.get("ADMIN_SESSION_SECRET")
        cls.old_quiet_logs = os.environ.get("QUIET_HTTP_LOGS")
        os.environ["ADMIN_PASSWORD"] = "test-password"
        os.environ["ADMIN_SESSION_SECRET"] = "test-secret"
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
        cls.restore_env("ADMIN_PASSWORD", cls.old_password)
        cls.restore_env("ADMIN_SESSION_SECRET", cls.old_secret)
        cls.restore_env("QUIET_HTTP_LOGS", cls.old_quiet_logs)

    @staticmethod
    def restore_env(key, value):
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
        match = re.search(rb'name="csrf_token" value="([^"]+)"', content)
        self.assertIsNotNone(match)
        return match.group(1).decode()

    def login_cookie(self):
        login_page, content = self.request("GET", "/admin-login")
        self.assertEqual(login_page.status, 200)
        body = urlencode({"password": "test-password", "csrf_token": self.extract_csrf(content)})
        response, _ = self.request(
            "POST",
            "/admin-login",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 302)
        cookie = response.getheader("Set-Cookie")
        self.assertIsNotNone(cookie)
        return cookie

    def test_admin_login_missing_csrf_rejected(self):
        body = urlencode({"password": "test-password"})
        response, content = self.request(
            "POST",
            "/admin-login",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 400)
        self.assertIn(b"invalid CSRF token", content)

    def test_unauthenticated_admin_blocked(self):
        response, _ = self.request("GET", "/admin")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")

    def test_authenticated_admin_allowed(self):
        cookie = self.login_cookie()
        response, content = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(b"Admin Dashboard", content)

    def test_unauthenticated_exports_blocked(self):
        for path in ("/export/csv", "/export/geojson", "/export/kml"):
            with self.subTest(path=path):
                response, content = self.request("GET", path)
                self.assertEqual(response.status, 403)
                self.assertIn(b"admin login required", content)

    def test_authenticated_exports_allowed(self):
        cookie = self.login_cookie()
        expected_content = {
            "/export/csv": b"first_name",
            "/export/geojson": b"FeatureCollection",
            "/export/kml": b"kml",
        }
        for path, expected in expected_content.items():
            with self.subTest(path=path):
                response, content = self.request("GET", path, headers={"Cookie": cookie})
                self.assertEqual(response.status, 200)
                self.assertIn(expected, content)

    def test_invalid_tampered_session_rejected(self):
        cookie = self.login_cookie().replace(".", "x.", 1)
        admin_response, _ = self.request("GET", "/admin", headers={"Cookie": cookie})
        export_response, _ = self.request("GET", "/export/csv", headers={"Cookie": cookie})
        self.assertEqual(admin_response.status, 302)
        self.assertEqual(export_response.status, 403)

    def test_signup_missing_csrf_rejected(self):
        body = urlencode({
            "first_name": "Test",
            "last_name": "Pilot",
            "email": "pilot@example.com",
            "address_line1": "1 Drone Way",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "Test Pilot",
        })
        response, content = self.request(
            "POST",
            "/signup",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 400)
        self.assertIn(b"invalid CSRF token", content)

    def test_signup_honeypot_rejected(self):
        signup_page, content = self.request("GET", "/signup")
        self.assertEqual(signup_page.status, 200)
        body = urlencode({
            "first_name": "Bot",
            "last_name": "McSpam",
            "email": "bot@example.com",
            "address_line1": "1 Drone Way",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "Bot McSpam",
            "csrf_token": self.extract_csrf(content),
            "website_url": "https://spam.example",
        })
        response, body_content = self.request(
            "POST",
            "/signup",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status, 400)
        self.assertIn(b"submission rejected", body_content)

    def test_project_review_pages_available(self):
        expected = {
            "/overview": b"Benton Drones Lead Ingest MVP",
            "/shopify-preview": b"Shopify Landing Page Preview",
            "/changelog": b"MVP Changelog",
            "/roadmap": b"MVP Roadmap",
            "/domain-setup": b"Domain & DNS Setup Plan",
            "/api-preflight": b"API & CLI Automation Preflight",
            "/current-state": b"Current State & Next Steps",
            "/goals": b"Implementation Goals",
            "/judges": b"Implementation Judges",
        }
        for path, marker in expected.items():
            with self.subTest(path=path):
                response, content = self.request("GET", path)
                self.assertEqual(response.status, 200)
                self.assertIn(marker, content)

    def test_e2e_shopify_preview_to_signup_to_admin_export(self):
        preview_response, preview = self.request("GET", "/shopify-preview")
        self.assertEqual(preview_response.status, 200)
        self.assertIn(b"/signup/default?source=shopify", preview)

        signup_response, signup = self.request("GET", "/signup/default?source=shopify&campaign=e2e-test&page_url=/pages/drone-delivery-signup")
        self.assertEqual(signup_response.status, 200)
        csrf = self.extract_csrf(signup)
        body = urlencode({
            "first_name": "E2E",
            "last_name": "Pilot",
            "email": "e2e-pilot@example.com",
            "phone": "555-2222",
            "address_line1": "101 Flight Path",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "E2E Pilot",
            "csrf_token": csrf,
            "campaign": "e2e-test",
            "source": "shopify",
            "variant_slug": "default",
            "shopify_page_url": "/pages/drone-delivery-signup",
        })
        submit_response, submit = self.request(
            "POST",
            "/signup",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(submit_response.status, 200)
        self.assertIn(b"Your signup was saved", submit)

        cookie = self.login_cookie()
        admin_response, admin = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(admin_response.status, 200)
        self.assertIn(b"e2e-pilot@example.com", admin)

        csv_response, csv_content = self.request("GET", "/export/csv", headers={"Cookie": cookie})
        self.assertEqual(csv_response.status, 200)
        self.assertIn(b"e2e-pilot@example.com", csv_content)
        self.assertIn(b"signed_name", csv_content)

    def _extract_lead_id_for_email(self, admin_html: bytes, email: str) -> str:
        # Find the row containing the email and extract the lead id from onclick.
        email_index = admin_html.find(email.encode())
        self.assertNotEqual(email_index, -1, "email not found in admin page")
        row_start = admin_html.rfind(b"<tr", 0, email_index)
        row_end = admin_html.find(b"</tr>", email_index)
        row = admin_html[row_start:row_end]
        match = re.search(rb"/admin/lead/(\d+)", row)
        self.assertIsNotNone(match)
        return match.group(1).decode()

    def test_admin_lead_detail_and_geojson(self):
        # Submit a signup so there is a lead
        signup_response, signup = self.request("GET", "/signup")
        self.assertEqual(signup_response.status, 200)
        csrf = self.extract_csrf(signup)
        body = urlencode({
            "first_name": "Detail",
            "last_name": "Test",
            "email": "detail-test@example.com",
            "address_line1": "202 Flight Path",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": "yes",
            "waiver_accepted": "yes",
            "typed_name": "Detail Test",
            "csrf_token": csrf,
        })
        submit_response, _ = self.request(
            "POST",
            "/signup",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(submit_response.status, 200)

        cookie = self.login_cookie()

        # Find the lead id from the admin page
        admin_response, admin_html = self.request("GET", "/admin", headers={"Cookie": cookie})
        self.assertEqual(admin_response.status, 200)
        lead_id = self._extract_lead_id_for_email(admin_html, "detail-test@example.com")

        # Lead detail page
        detail_response, detail = self.request("GET", f"/admin/lead/{lead_id}", headers={"Cookie": cookie})
        self.assertEqual(detail_response.status, 200)
        self.assertIn(b"Detail Test", detail)
        self.assertIn(b"Signature record", detail)
        self.assertIn(b"Waiver version", detail)

        # GeoJSON endpoint
        geo_response, geo = self.request("GET", "/admin/leads.geojson", headers={"Cookie": cookie})
        self.assertEqual(geo_response.status, 200)
        self.assertIn(b"FeatureCollection", geo)

    def test_admin_lead_detail_unauthenticated_blocked(self):
        response, _ = self.request("GET", "/admin/lead/1")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")

    def test_admin_leads_geojson_unauthenticated_blocked(self):
        response, _ = self.request("GET", "/admin/leads.geojson")
        self.assertEqual(response.status, 403)


if __name__ == "__main__":
    unittest.main()
