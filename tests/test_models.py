"""Tests for lead_ingest.models dataclasses and helpers."""
import re
import unittest

from lead_ingest.models import LeadPoint, SignupInput, utc_now_iso


class SignupInputTests(unittest.TestCase):
    def test_full_address_includes_all_fields(self):
        signup = SignupInput(
            first_name="Ada", last_name="Lovelace", email="ada@example.com",
            phone="555-1234", address_line1="1 Drone Way",
            address_line2="Apt 2", city="Bentonville", state="AR",
            postal_code="72712", consent_accepted=True,
            waiver_accepted=True, typed_name="Ada Lovelace",
        )
        addr = signup.full_address
        self.assertIn("1 Drone Way", addr)
        self.assertIn("Apt 2", addr)
        self.assertIn("Bentonville", addr)
        self.assertIn("AR", addr)
        self.assertIn("72712", addr)

    def test_full_address_omits_empty_optional_fields(self):
        signup = SignupInput(
            first_name="Ada", last_name="Lovelace", email="ada@example.com",
            phone="", address_line1="1 Drone Way", address_line2="",
            city="Bentonville", state="AR", postal_code="72712",
            consent_accepted=True, waiver_accepted=True, typed_name="Ada Lovelace",
        )
        addr = signup.full_address
        self.assertIn("1 Drone Way", addr)
        self.assertIn("Bentonville", addr)
        # address_line2 is empty so it should not appear as a dangling comma
        self.assertNotIn(", ,", addr)

    def test_full_address_handles_whitespace_only_fields(self):
        signup = SignupInput(
            first_name="Ada", last_name="Lovelace", email="ada@example.com",
            phone="", address_line1="1 Drone Way", address_line2="   ",
            city="Bentonville", state="AR", postal_code="72712",
            consent_accepted=True, waiver_accepted=True, typed_name="Ada Lovelace",
        )
        addr = signup.full_address
        # Whitespace-only address_line2 should be filtered out.
        parts = [p.strip() for p in addr.split(",")]
        self.assertNotIn("", parts)

    def test_signup_input_is_frozen(self):
        signup = SignupInput(
            first_name="Ada", last_name="L", email="a@b.com", phone="",
            address_line1="1 Way", city="City", state="AR", postal_code="72712",
            consent_accepted=True, waiver_accepted=True, typed_name="Ada L",
        )
        with self.assertRaises(AttributeError):
            signup.first_name = "Changed"


class LeadPointTests(unittest.TestCase):
    def test_lead_point_fields(self):
        point = LeadPoint(signup_id=42, name="Test Pilot", latitude=36.37, longitude=-94.20)
        self.assertEqual(point.signup_id, 42)
        self.assertEqual(point.name, "Test Pilot")
        self.assertAlmostEqual(point.latitude, 36.37)
        self.assertAlmostEqual(point.longitude, -94.20)

    def test_lead_point_is_frozen(self):
        point = LeadPoint(1, "A", 1.0, 2.0)
        with self.assertRaises(AttributeError):
            point.signup_id = 99


class UtcNowIsoTests(unittest.TestCase):
    def test_utc_now_iso_returns_iso_format(self):
        timestamp = utc_now_iso()
        # Should look like 2026-01-15T12:34:56+00:00
        self.assertRegex(timestamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")

    def test_utc_now_iso_is_recent(self):
        timestamp = utc_now_iso()
        # Should be parseable and close to now.
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", timestamp)
        self.assertIsNotNone(match)


if __name__ == "__main__":
    unittest.main()
