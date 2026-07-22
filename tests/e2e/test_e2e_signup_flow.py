"""E2E: POST /signup lead creation flow + the full signup->admin journey.

Covers: GET /signup form, happy-path submission, validation errors, honeypot
rejection, invalid CSRF, variant slug, and a true end-to-end journey
(submit -> log in -> lead appears in admin dashboard and CSV export).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_base import E2ETestBase  # noqa: E402


class SignupFlowTests(E2ETestBase):

    def test_submit_valid_lead_returns_success(self):
        fields = self.valid_signup_fields("e2e.success@example.com")
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 200)
        self.assertIn(b"signup was saved", content.lower())

    def test_submit_missing_email_returns_400_with_error(self):
        fields = self.valid_signup_fields("")  # empty email
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"email is required", content)

    def test_submit_invalid_email_format_returns_400(self):
        fields = self.valid_signup_fields("not-an-email")
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"email must be valid", content)

    def test_submit_bad_state_returns_400(self):
        fields = self.valid_signup_fields(
            "e2e.state@example.com", state="California"
        )
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"state must be a 2-letter code", content)

    def test_submit_bad_zip_returns_400(self):
        fields = self.valid_signup_fields(
            "e2e.zip@example.com", postal_code="ZIPCODE"
        )
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"postal_code must be a valid US ZIP code", content)

    def test_submit_without_consent_returns_400(self):
        fields = self.valid_signup_fields("e2e.consent@example.com")
        fields["consent_accepted"] = ""
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"consent is required", content)

    def test_submit_without_waiver_returns_400(self):
        fields = self.valid_signup_fields("e2e.waiver@example.com")
        fields["waiver_accepted"] = ""
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"waiver agreement is required", content)

    def test_submit_without_typed_name_returns_400(self):
        fields = self.valid_signup_fields("e2e.typed@example.com")
        fields["typed_name"] = ""
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"typed legal name is required", content)

    def test_submit_honeypot_filled_is_rejected(self):
        fields = self.valid_signup_fields("e2e.honeypot@example.com")
        fields["website_url"] = "http://spam.example.com"  # honeypot trap
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"submission rejected", content)

    def test_submit_invalid_csrf_returns_400(self):
        fields = self.valid_signup_fields("e2e.csrf@example.com")
        fields["csrf_token"] = "garbage-token"
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"invalid CSRF token", content)

    def test_submit_cross_action_csrf_rejected(self):
        # A login-scoped token must not validate for the signup action.
        fields = self.valid_signup_fields("e2e.crossaction@example.com")
        fields["csrf_token"] = self.login_csrf()
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 400)
        self.assertIn(b"invalid CSRF token", content)

    def test_signup_variant_slug_accepted(self):
        # /signup/custom-variant falls back to default variant but still 200.
        response, content = self.get("/signup/custom-variant")
        self.assertEqual(response.status, 200)
        self.assertIn(b'name="csrf_token"', content)


class SignupEndToEndJourneyTests(E2ETestBase):
    """One true black-box journey through multiple features."""

    def test_signup_then_login_then_admin_and_export_show_lead(self):
        email = "e2e.journey@example.com"

        # 1. Submit a lead via the public form.
        fields = self.valid_signup_fields(email, source="e2e-journey")
        response, content = self.submit_signup(fields)
        self.assertEqual(response.status, 200, content)
        self.assertIn(b"signup was saved", content.lower())

        # 2. A lead id was persisted.
        lead_ids = self.list_lead_ids()
        self.assertEqual(len(lead_ids), 1, "exactly one lead should exist")

        # 3. Log in as admin.
        cookie = self.admin_cookie()

        # 4. The lead appears on the admin dashboard.
        response, content = self.get("/admin", cookie=cookie)
        self.assertEqual(response.status, 200)
        self.assertIn(email.encode(), content)

        # 5. The lead appears in the CSV export.
        response, content = self.get("/export/csv", cookie=cookie)
        self.assertEqual(response.status, 200)
        self.assertIn("text/csv", response.getheader("Content-Type", ""))
        self.assertIn(email.encode(), content)

        # 6. The lead detail page renders for that id.
        lead_id = lead_ids[0]
        response, content = self.get(f"/admin/lead/{lead_id}", cookie=cookie)
        self.assertEqual(response.status, 200)
        self.assertIn(email.encode(), content)


if __name__ == "__main__":
    unittest.main()
