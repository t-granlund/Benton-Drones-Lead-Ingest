"""E2E: public GET routes render branded HTML pages.

Covers: /, /signup, /signup/<slug>, /overview, /shopify-preview, /changelog,
/roadmap, /domain-setup, /api-preflight, /current-state, /goals, /judges,
/landing-page.html, and /static/* serving.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_base import E2ETestBase  # noqa: E402


def _is_branded_html(content: bytes) -> bool:
    """Every page is wrapped by branded_page() -> full HTML doc with the logo."""
    low = content.lower()
    return b"<!doctype html>" in low and b"bentondrones.com" in content


class PublicPagesTests(E2ETestBase):

    PUBLIC_PAGES = [
        "/",
        "/signup",
        "/signup/default",
        "/signup/custom-variant",
        "/overview",
        "/shopify-preview",
        "/changelog",
        "/roadmap",
        "/domain-setup",
        "/api-preflight",
        "/current-state",
        "/goals",
        "/judges",
    ]

    def test_each_public_page_renders_200_branded_html(self):
        for path in self.PUBLIC_PAGES:
            with self.subTest(path=path):
                response, content = self.get(path)
                self.assertEqual(response.status, 200,
                                 f"{path} returned {response.status}")
                self.assertTrue(content, f"{path} returned empty body")
                self.assertTrue(_is_branded_html(content),
                                f"{path} did not render branded HTML")

    def test_signup_page_contains_csrf_and_required_fields(self):
        response, content = self.get("/signup")
        self.assertEqual(response.status, 200)
        self.assertIn(b'name="csrf_token"', content)
        for field in ("first_name", "last_name", "email", "consent_accepted",
                      "waiver_accepted", "typed_name"):
            self.assertIn(field.encode(), content,
                          f"signup form missing field {field}")

    def test_landing_page_html_route_serves_file(self):
        response, content = self.get("/landing-page.html")
        self.assertEqual(response.status, 200)
        self.assertTrue(content)
        # landing page is a standalone HTML file; should contain a doctype
        self.assertIn(b"<!doctype html", content.lower())

    def test_static_serves_known_asset_with_cache_header(self):
        response, content = self.get("/static/leaflet/leaflet.css")
        self.assertEqual(response.status, 200)
        self.assertIn("text/css", response.getheader("Content-Type", ""))
        self.assertEqual(response.getheader("Cache-Control"), "public, max-age=86400")
        self.assertTrue(content)

    def test_static_unknown_file_returns_404(self):
        response, _ = self.get("/static/does-not-exist.css")
        self.assertEqual(response.status, 404)

    def test_unknown_path_returns_404(self):
        response, _ = self.get("/this-route-does-not-exist")
        self.assertEqual(response.status, 404)


if __name__ == "__main__":
    unittest.main()
