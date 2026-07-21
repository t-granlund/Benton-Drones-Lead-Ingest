"""Tests for PDF / HTML print rendering."""
import sqlite3
import unittest

from lead_ingest.db import create_signup, get_consent_record, get_signature_record, init_db
from lead_ingest.models import SignupInput
from lead_ingest.pdf import render_signup_html, try_render_pdf


class PdfHtmlRenderTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        init_db(self.conn)
        self.signup_id = create_signup(
            self.conn,
            SignupInput(
                first_name="Print", last_name="Test",
                email="print@example.com", phone="555-9999",
                address_line1="42 Aerial Way", city="Bentonville",
                state="AR", postal_code="72712",
                consent_accepted=True, waiver_accepted=True,
                typed_name="Print Test",
            ),
            ip_address="127.0.0.1",
            user_agent="TestAgent/1.0",
        )
        self.signup = self.conn.execute(
            "SELECT * FROM signups WHERE id = ?", (self.signup_id,)
        ).fetchone()
        self.consent = get_consent_record(self.conn, self.signup_id)
        self.signature = get_signature_record(self.conn, self.signup_id)

    def tearDown(self):
        self.conn.close()

    def test_render_signup_html_returns_bytes(self):
        html = render_signup_html(self.signup, self.consent, self.signature)
        self.assertIsInstance(html, bytes)
        self.assertGreater(len(html), 500)

    def test_render_signup_html_contains_lead_name(self):
        html = render_signup_html(self.signup, self.consent, self.signature).decode("utf-8")
        self.assertIn("Print Test", html)

    def test_render_signup_html_contains_email(self):
        html = render_signup_html(self.signup, self.consent, self.signature).decode("utf-8")
        self.assertIn("print@example.com", html)

    def test_render_signup_html_contains_address(self):
        html = render_signup_html(self.signup, self.consent, self.signature).decode("utf-8")
        self.assertIn("42 Aerial Way", html)
        self.assertIn("Bentonville", html)

    def test_render_signup_html_contains_consent_version(self):
        html = render_signup_html(self.signup, self.consent, self.signature).decode("utf-8")
        self.assertIn("Consent", html)

    def test_render_signup_html_contains_signature_info(self):
        html = render_signup_html(self.signup, self.consent, self.signature).decode("utf-8")
        self.assertIn("Signature", html)
        self.assertIn("Print Test", html)
        self.assertIn("Waiver", html)

    def test_render_signup_html_contains_ip_and_ua(self):
        html = render_signup_html(self.signup, self.consent, self.signature).decode("utf-8")
        self.assertIn("127.0.0.1", html)
        self.assertIn("TestAgent", html)

    def test_render_signup_html_contains_logo(self):
        html = render_signup_html(self.signup, self.consent, self.signature).decode("utf-8")
        self.assertIn("bentondrones.com", html)
        self.assertIn("BENTON_DRONES", html)

    def test_render_signup_html_has_print_button(self):
        html = render_signup_html(self.signup, self.consent, self.signature).decode("utf-8")
        self.assertIn("window.print()", html)

    def test_render_signup_html_handles_none_consent_and_signature(self):
        html = render_signup_html(self.signup, None, None).decode("utf-8")
        self.assertIn("-", html)
        self.assertIn("Print Test", html)

    def test_try_render_pdf_returns_none_or_bytes(self):
        result = try_render_pdf(self.signup, self.consent, self.signature)
        # fpdf2 may or may not be installed — either is valid.
        if result is not None:
            self.assertIsInstance(result, bytes)
            self.assertGreater(len(result), 100)
            # PDF files start with %PDF
            self.assertTrue(result[:4] == b"%PDF")

    def test_try_render_pdf_returns_none_with_missing_data(self):
        result = try_render_pdf(self.signup, None, None)
        # Should not crash even with missing consent/signature.
        if result is not None:
            self.assertIsInstance(result, bytes)


if __name__ == "__main__":
    unittest.main()
