"""E2E: data exports (/export/csv, /export/geojson, /export/kml).

Covers: all three exports reject unauthenticated requests with 403, and once
authenticated return 200 with the correct content type and a recognisable body.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_base import E2ETestBase  # noqa: E402

EXPORTS = [
    ("/export/csv", "text/csv", b","),
    ("/export/geojson", "application/geo+json", b"FeatureCollection"),
    ("/export/kml", "application/vnd.google-earth.kml+xml", b"<kml"),
]


class ExportsUnauthenticatedTests(E2ETestBase):

    def test_each_export_requires_admin_login_403(self):
        for path, _, _ in EXPORTS:
            with self.subTest(path=path):
                response, content = self.get(path)
                self.assertEqual(response.status, 403, path)
                self.assertIn(b"admin login required", content)


class ExportsAuthenticatedTests(E2ETestBase):

    def setUp(self):
        self.email = "e2e.export@example.com"
        fields = self.valid_signup_fields(self.email, source="e2e-export")
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 200, content)
        self.cookie = self.admin_cookie()

    def test_each_export_returns_200_with_content_type_and_marker(self):
        for path, expected_type, marker in EXPORTS:
            with self.subTest(path=path):
                response, content = self.get(path, cookie=self.cookie)
                self.assertEqual(response.status, 200, path)
                self.assertIn(expected_type, response.getheader("Content-Type", ""),
                              path)
                self.assertIn(marker, content, f"{path} missing marker")
                # All exports expose the lead email; KML additionally shows the name.
                self.assertIn(self.email.encode(), content, path)
                if path == "/export/kml":
                    self.assertIn(b"E2E Tester", content, path)

    def test_csv_export_is_text_csv_with_leads(self):
        response, content = self.get("/export/csv", cookie=self.cookie)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "text/csv")
        self.assertIn(self.email.encode(), content)


if __name__ == "__main__":
    unittest.main()
