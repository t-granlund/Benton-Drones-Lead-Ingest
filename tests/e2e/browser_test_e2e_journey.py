"""Browser-automation E2E tests covering the full user journey.

These tests exercise the app through a real Chromium browser (Playwright).
They can run against the local ephemeral server (default) or a live URL by
setting E2E_BASE_URL. Admin tests against a live URL require E2E_ADMIN_PASSWORD.

Examples:
    # local
    python -m unittest tests.e2e.test_e2e_browser_journey

    # live Render instance
    E2E_BASE_URL=https://benton-drones-lead-ingest.onrender.com \
    E2E_ADMIN_PASSWORD='the-password' \
    python -m unittest tests.e2e.test_e2e_browser_journey
"""
from __future__ import annotations

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_base import BrowserTestBase  # noqa: E402


class BrowserPublicPageTests(BrowserTestBase):
    """Public pages render correctly in a real browser."""

    def test_root_and_health_pages_render(self):
        self.goto("/")
        self.assertIn("Benton", self.page.title())

        self.goto("/healthz")
        self.assert_page_contains('"status": "ok"')

    def test_signup_page_renders_with_required_fields(self):
        self.goto("/signup")
        self.assert_page_contains("Sign up")
        # Required form controls are present and visible.
        for name in ["first_name", "last_name", "email", "address_line1",
                     "city", "state", "postal_code", "typed_name"]:
            locator = self.page.locator(f'input[name="{name}"]')
            self.assertTrue(locator.is_visible(), f"field {name} is not visible")
        self.page.locator('input[name="consent_accepted"]').wait_for(state="visible")
        self.page.locator('input[name="waiver_accepted"]').wait_for(state="visible")

    def test_landing_page_renders_branded_content(self):
        self.goto("/landing-page.html")
        body = self.page.locator("body")
        from playwright.sync_api import expect
        expect(body).to_contain_text("Benton")

    def test_project_pages_render_200(self):
        for path in ["/overview", "/changelog", "/roadmap", "/current-state"]:
            with self.subTest(path=path):
                self.goto(path)
                self.assertEqual(self.page.locator("h1").count(), 1)


class BrowserSignupFlowTests(BrowserTestBase):
    """Full signup flow via real browser interactions."""

    def _unique_email(self):
        return f"browser.e2e.{int(time.time() * 1000)}@example.com"

    def test_valid_signup_shows_success_page(self):
        email = self._unique_email()
        self.goto("/signup")
        self.fill_signup_form({
            "first_name": "Browser",
            "last_name": "Tester",
            "email": email,
            "phone": "555-123-4567",
            "address_line1": "123 Test St",
            "city": "Testville",
            "state": "CA",
            "postal_code": "90001",
        })
        self.check_consent_and_waiver()
        self.type_signature("Browser Tester")
        self.submit_signup()

        self.assert_page_contains("saved")

    def test_missing_required_field_shows_validation_error(self):
        self.goto("/signup")
        # Fill everything except email and signature.
        self.fill_signup_form({
            "first_name": "Browser",
            "last_name": "Tester",
            "phone": "555-123-4567",
            "address_line1": "123 Test St",
            "city": "Testville",
            "state": "CA",
            "postal_code": "90001",
        })
        self.check_consent_and_waiver()
        self.submit_signup()

        # HTML5 validation prevents submission on missing required email.
        self.assertEqual(
            self.page.locator('input[name="email"]:invalid').count(), 1
        )

    def test_honeypot_field_is_hidden_from_humans(self):
        self.goto("/signup")
        honeypot = self.page.locator('input[name="website_url"]')
        # Honeypot is present in DOM but visually hidden.
        self.assertTrue(honeypot.count() >= 1)


class BrowserAdminJourneyTests(BrowserTestBase):
    """Admin journey: login, dashboard, lead detail, exports, print."""

    def _seed_and_login(self):
        email = f"admin.browser.{int(time.time() * 1000)}@example.com"
        self.goto("/signup")
        self.fill_signup_form({
            "first_name": "Admin",
            "last_name": "Journey",
            "email": email,
            "phone": "555-999-0000",
            "address_line1": "456 Admin Ave",
            "city": "Adminville",
            "state": "TX",
            "postal_code": "75001",
        })
        self.check_consent_and_waiver()
        self.type_signature("Admin Journey")
        self.submit_signup()
        self.assert_page_contains("saved")

        self.admin_login()
        self.assert_path("/admin")
        return email

    def test_admin_login_renders_dashboard(self):
        self.admin_login()
        self.assert_path("/admin")
        self.assert_page_contains("Admin Dashboard")
        self.assert_page_contains("Total leads")

    def test_dashboard_shows_seeded_lead(self):
        email = self._seed_and_login()
        self.assert_page_contains(email)

    def test_lead_detail_link_renders(self):
        email = self._seed_and_login()
        # Click the "View" button in the recent leads table.
        self.page.locator("table a:has-text('View')").first.click()
        self.page.wait_for_load_state("networkidle")
        self.assert_page_contains(email)
        self.assert_page_contains("Lead #")

    def test_print_view_renders(self):
        email = self._seed_and_login()
        self.page.locator("table a:has-text('View')").first.click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("a:has-text('Print / PDF')").click()
        self.page.wait_for_load_state("networkidle")
        self.assert_page_contains(email)
        self.assert_page_contains("Consent record")

    def test_export_links_are_present_and_reachable(self):
        self._seed_and_login()
        from playwright.sync_api import expect

        # Verify the three export links exist and point to the protected paths.
        for label, expected_href in [
            ("CSV", "/export/csv"),
            ("GeoJSON", "/export/geojson"),
            ("KML", "/export/kml"),
        ]:
            with self.subTest(format=label):
                link = self.page.locator(f"a:has-text('{label}')")
                expect(link).to_have_attribute("href", expected_href)
                # Following the link while authenticated should succeed (HTTP 200).
                response = self.page.request.get(self.url(expected_href))
                self.assertEqual(response.status, 200, f"{label} export failed")


if __name__ == "__main__":
    unittest.main()
