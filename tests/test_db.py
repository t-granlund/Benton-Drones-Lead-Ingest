import sqlite3
import unittest

from lead_ingest.db import (
    analytics_summary,
    create_signup,
    get_consent_record,
    get_export_rows,
    get_signature_record,
    get_signup,
    get_variant,
    init_db,
    list_lead_points,
    list_signups,
    recent_leads,
)
from lead_ingest.models import CONSENT_VERSION, SIGNATURE_DISCLAIMER, WAIVER_VERSION, SignupInput


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def signup(self):
        return SignupInput(
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
            phone="555-0000",
            address_line1="2 Compiler Ct",
            city="Bentonville",
            state="AR",
            postal_code="72712",
            consent_accepted=True,
            waiver_accepted=True,
            typed_name="Grace Hopper",
        )

    def test_create_signup_creates_consent_record(self):
        signup_id = create_signup(self.conn, self.signup(), "127.0.0.1", "tests")
        row = self.conn.execute("SELECT * FROM consent_records WHERE signup_id = ?", (signup_id,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["consent_version"], CONSENT_VERSION)
        self.assertEqual(row["accepted"], 1)

    def test_create_signup_geocodes_locally(self):
        create_signup(self.conn, self.signup())
        row = list_signups(self.conn)[0]
        self.assertEqual(row["geocode_status"], "success")
        self.assertIsNotNone(row["latitude"])
        self.assertIsNotNone(row["longitude"])

    def test_list_lead_points(self):
        create_signup(self.conn, self.signup())
        points = list_lead_points(self.conn)
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].name, "Grace Hopper")

    def test_create_signup_persists_shopify_context(self):
        signup = self.signup()
        signup = SignupInput(
            **{
                **signup.__dict__,
                "shopify_shop_domain": "bentondrones.myshopify.com",
                "shopify_customer_id": "12345",
                "shopify_page_url": "/pages/drone-delivery",
            }
        )
        create_signup(self.conn, signup)
        row = list_signups(self.conn)[0]
        self.assertEqual(row["shopify_shop_domain"], "bentondrones.myshopify.com")
        self.assertEqual(row["shopify_customer_id"], "12345")
        self.assertEqual(row["shopify_page_url"], "/pages/drone-delivery")

    def test_signature_record_created(self):
        signup_id = create_signup(self.conn, self.signup(), "127.0.0.1", "tests")
        signature = get_signature_record(self.conn, signup_id)
        self.assertIsNotNone(signature)
        self.assertEqual(signature["full_name_typed"], "Grace Hopper")
        self.assertEqual(signature["signature_disclaimer_text"], SIGNATURE_DISCLAIMER)
        self.assertEqual(signature["waiver_version"], WAIVER_VERSION)
        self.assertEqual(signature["ip_address"], "127.0.0.1")
        self.assertEqual(signature["user_agent"], "tests")

    def test_analytics_summary(self):
        signup = self.signup()
        signup = SignupInput(**{**signup.__dict__, "source": "local", "campaign": "test-campaign"})
        create_signup(self.conn, signup)
        stats = analytics_summary(self.conn)
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["pending_geocodes"], 0)
        self.assertIn("local", stats["by_source"])
        self.assertIn("test-campaign", stats["by_campaign"])

    def test_export_rows_include_signature(self):
        signup_id = create_signup(self.conn, self.signup())
        rows = get_export_rows(self.conn)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["signed_name"], "Grace Hopper")
        self.assertEqual(rows[0]["id"], signup_id)

    def test_create_signup_without_geocode(self):
        signup_id = create_signup(self.conn, self.signup(), geocode=False)
        row = list_signups(self.conn)[0]
        self.assertEqual(row["geocode_status"], "pending")
        self.assertIsNone(row["latitude"])
        self.assertIsNone(row["longitude"])
        self.assertEqual(row["geocode_provider"], "")

    def test_get_signup_returns_none_for_missing(self):
        self.assertIsNone(get_signup(self.conn, 99999))

    def test_get_consent_record_returns_none_for_missing(self):
        self.assertIsNone(get_consent_record(self.conn, 99999))

    def test_get_signature_record_returns_none_for_missing(self):
        self.assertIsNone(get_signature_record(self.conn, 99999))

    def test_get_variant_default_exists(self):
        variant = get_variant(self.conn, "default")
        self.assertIsNotNone(variant)
        self.assertEqual(variant["slug"], "default")
        self.assertEqual(variant["title"], "Join Benton Drones Delivery Simulations")

    def test_get_variant_nonexistent_returns_none(self):
        self.assertIsNone(get_variant(self.conn, "nonexistent"))

    def test_get_variant_inactive_returns_none(self):
        self.conn.execute(
            "INSERT INTO landing_page_variants (slug, title, cta_text, is_active) "
            "VALUES ('inactive-test', 'Inactive', 'Sign up', 0)"
        )
        self.conn.commit()
        self.assertIsNone(get_variant(self.conn, "inactive-test"))

    def test_analytics_summary_empty_db(self):
        stats = analytics_summary(self.conn)
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["today"], 0)
        self.assertEqual(stats["this_week"], 0)
        self.assertEqual(stats["pending_geocodes"], 0)
        self.assertEqual(stats["by_source"], {})
        self.assertEqual(stats["by_campaign"], {})
        self.assertEqual(stats["by_variant"], {})

    def test_recent_leads_respects_limit(self):
        for i in range(5):
            create_signup(self.conn, SignupInput(
                **{**self.signup().__dict__, "email": f"lead{i}@example.com"}))
        rows = recent_leads(self.conn, limit=3)
        self.assertEqual(len(rows), 3)

    def test_email_normalized_to_lowercase(self):
        create_signup(self.conn, SignupInput(
            **{**self.signup().__dict__, "email": "UPPER@EXAMPLE.COM"}))
        row = list_signups(self.conn)[0]
        self.assertEqual(row["email"], "upper@example.com")

    def test_state_normalized_to_uppercase(self):
        create_signup(self.conn, SignupInput(
            **{**self.signup().__dict__, "state": "ar"}))
        row = list_signups(self.conn)[0]
        self.assertEqual(row["state"], "AR")

    def test_variant_slug_defaults_to_default(self):
        signup = SignupInput(**{**self.signup().__dict__, "variant_slug": ""})
        create_signup(self.conn, signup)
        row = list_signups(self.conn)[0]
        self.assertEqual(row["variant_slug"], "default")

    def test_full_address_stored_correctly(self):
        signup = SignupInput(
            **{**self.signup().__dict__, "address_line2": "Apt 5"})
        create_signup(self.conn, signup)
        row = list_signups(self.conn)[0]
        self.assertIn("2 Compiler Ct", row["full_address"])
        self.assertIn("Apt 5", row["full_address"])
        self.assertIn("Bentonville", row["full_address"])

    def test_consent_and_signature_are_unique_per_signup(self):
        signup_id = create_signup(self.conn, self.signup())
        # Inserting another signup should not conflict.
        signup_id2 = create_signup(self.conn, SignupInput(
            **{**self.signup().__dict__, "email": "second@example.com"}))
        self.assertNotEqual(signup_id, signup_id2)
        self.assertIsNotNone(get_consent_record(self.conn, signup_id))
        self.assertIsNotNone(get_consent_record(self.conn, signup_id2))
        self.assertIsNotNone(get_signature_record(self.conn, signup_id))
        self.assertIsNotNone(get_signature_record(self.conn, signup_id2))


if __name__ == "__main__":
    unittest.main()
