"""Tests for lead_ingest.branded_template — page rendering, nav, logo, CSS."""
import unittest

from lead_ingest.branded_template import (
    ACCENT_BLUE,
    CREAM,
    LINK_BLUE,
    LOGO_URL,
    PAGE_BG,
    PALE_BLUE,
    PALE_GREEN,
    PRIMARY_OLIVE,
    WHITE,
    branded_page,
)


class BrandedTemplateTests(unittest.TestCase):
    def test_branded_page_returns_bytes(self):
        content = branded_page("Test", "<p>Body</p>")
        self.assertIsInstance(content, bytes)
        self.assertIn(b"Test", content)
        self.assertIn(b"Body", content)

    def test_branded_page_includes_doctype_and_html(self):
        content = branded_page("Title", "<p>Content</p>").decode()
        self.assertTrue(content.startswith("<!doctype html>"))
        self.assertIn("<html", content)
        self.assertIn("</html>", content)

    def test_branded_page_without_nav_has_no_nav_links(self):
        content = branded_page("Title", "<p>Content</p>", show_nav=False).decode()
        self.assertNotIn("<nav class=\"benton-nav\">", content)
        self.assertNotIn('href="/admin"', content)
        self.assertNotIn('href="/admin-logout"', content)

    def test_branded_page_with_nav_includes_links(self):
        content = branded_page("Title", "<p>Content</p>", show_nav=True).decode()
        self.assertIn("benton-nav", content)
        self.assertIn('href="/overview"', content)
        self.assertIn('href="/admin"', content)
        self.assertIn('href="/admin-logout"', content)

    def test_branded_page_includes_logo_url(self):
        content = branded_page("Title", "<p>Content</p>", show_nav=True).decode()
        self.assertIn(LOGO_URL, content)

    def test_branded_page_includes_olive_color(self):
        content = branded_page("Title", "<p>Content</p>").decode()
        self.assertIn(PRIMARY_OLIVE, content)

    def test_branded_page_includes_css_variables(self):
        content = branded_page("Title", "<p>Content</p>").decode()
        for color in (PRIMARY_OLIVE, PAGE_BG, LINK_BLUE, ACCENT_BLUE,
                      CREAM, PALE_BLUE, PALE_GREEN, WHITE):
            self.assertIn(color, content, f"Missing CSS variable color {color}")

    def test_branded_page_includes_jost_font(self):
        content = branded_page("Title", "<p>Content</p>").decode()
        self.assertIn("Jost", content)

    def test_branded_page_includes_viewport_meta(self):
        content = branded_page("Title", "<p>Content</p>").decode()
        self.assertIn("viewport", content)
        self.assertIn("width=device-width", content)

    def test_branded_page_escapes_title(self):
        content = branded_page("<script>alert(1)</script>", "<p>Body</p>").decode()
        self.assertNotIn("<script>alert(1)</script>", content)
        self.assertIn("&lt;script&gt;", content)

    def test_branded_page_has_main_element(self):
        content = branded_page("Title", "<p>Body</p>").decode()
        self.assertIn("<main>", content)
        self.assertIn("</main>", content)


if __name__ == "__main__":
    unittest.main()
