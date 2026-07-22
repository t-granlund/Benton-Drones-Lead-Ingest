"""E2E: authenticated admin dashboard, lead detail, print, pdf, geojson.

Each test seeds a lead via the public signup form, then exercises the
admin-protected GET views while authenticated.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_base import E2ETestBase  # noqa: E402


class AdminDashboardTests(E2ETestBase):

    def setUp(self):
        # The class DB may already hold leads from earlier tests, so capture
        # the id of the lead created in *this* test rather than assuming empty.
        self.email = "e2e.admin@example.com"
        before = set(self.list_lead_ids())
        fields = self.valid_signup_fields(self.email, source="e2e-admin")
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 200, content)
        new = set(self.list_lead_ids()) - before
        self.assertEqual(len(new), 1, "expected exactly one new lead")
        self.lead_id = new.pop()
        self.cookie = self.admin_cookie()

    def test_admin_dashboard_shows_recent_lead_and_sections(self):
        response, content = self.get("/admin", cookie=self.cookie)
        self.assertEqual(response.status, 200)
        self.assertIn(self.email.encode(), content)
        # Dashboard is branded HTML.
        self.assertIn(b"<!doctype html", content.lower())

    def test_admin_lead_detail_renders_lead(self):
        response, content = self.get(
            f"/admin/lead/{self.lead_id}", cookie=self.cookie
        )
        self.assertEqual(response.status, 200)
        self.assertIn(self.email.encode(), content)
        # Has a link back to admin and a print/pdf link.
        self.assertIn(b"/admin'>Back to admin", content)
        self.assertIn(f"/admin/lead/{self.lead_id}/print".encode(), content)

    def test_admin_lead_print_renders(self):
        response, content = self.get(
            f"/admin/lead/{self.lead_id}/print", cookie=self.cookie
        )
        self.assertEqual(response.status, 200)
        self.assertIn(self.email.encode(), content)

    def test_admin_lead_pdf_real_or_fallback(self):
        response, content = self.get(
            f"/admin/lead/{self.lead_id}/pdf", cookie=self.cookie
        )
        ctype = response.getheader("Content-Type", "")
        # Either fpdf2 produces a true PDF ...
        if response.status == 200 and "application/pdf" in ctype:
            self.assertTrue(content.startswith(b"%PDF"))
        # ... or the server falls back to a 302 redirect to the print view.
        else:
            self.assertEqual(response.status, 302)
            self.assertIn("/print", response.getheader("Location", ""))

    def test_admin_lead_pdf_invalid_id_returns_400(self):
        response, content = self.get(
            "/admin/lead/not-a-number/pdf", cookie=self.cookie
        )
        self.assertEqual(response.status, 400)
        self.assertIn(b"Invalid lead ID", content)

    def test_admin_lead_pdf_missing_lead_returns_404(self):
        response, content = self.get(
            "/admin/lead/99999999/pdf", cookie=self.cookie
        )
        self.assertEqual(response.status, 404)
        self.assertIn(b"Lead not found", content)

    def test_admin_leads_geojson_returns_feature_collection(self):
        response, content = self.get(
            "/admin/leads.geojson", cookie=self.cookie
        )
        self.assertEqual(response.status, 200)
        self.assertIn("application/geo+json", response.getheader("Content-Type", ""))
        self.assertIn(b"FeatureCollection", content)


if __name__ == "__main__":
    unittest.main()
