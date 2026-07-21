import unittest

from lead_ingest.models import SignupInput
from lead_ingest.validation import ValidationError, validate_signup


class ValidationTests(unittest.TestCase):
    def valid_signup(self, **overrides):
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "phone": "555-1234",
            "address_line1": "1 Drone Way",
            "city": "Bentonville",
            "state": "AR",
            "postal_code": "72712",
            "consent_accepted": True,
            "waiver_accepted": True,
            "typed_name": "Ada Lovelace",
        }
        data.update(overrides)
        return SignupInput(**data)

    def test_valid_signup_passes(self):
        validate_signup(self.valid_signup())

    def test_consent_required(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(consent_accepted=False))
        self.assertIn("consent is required", ctx.exception.errors)

    def test_email_must_be_valid(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(email="nope"))
        self.assertIn("email must be valid", ctx.exception.errors)

    def test_state_must_be_two_letters(self):
        with self.assertRaises(ValidationError):
            validate_signup(self.valid_signup(state="Arkansas"))

    def test_waiver_required(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(waiver_accepted=False))
        self.assertIn("waiver agreement is required", ctx.exception.errors)

    def test_typed_name_required(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(typed_name=""))
        self.assertIn("typed legal name is required", ctx.exception.errors)

    def test_multiple_errors_at_once(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(
                first_name="", email="nope", state="Arkansas",
                postal_code="abc", consent_accepted=False,
            ))
        errors = ctx.exception.errors
        self.assertIn("first_name is required", errors)
        self.assertIn("email must be valid", errors)
        self.assertIn("state must be a 2-letter code", errors)
        self.assertIn("postal_code must be a valid US ZIP code", errors)
        self.assertIn("consent is required", errors)
        self.assertGreaterEqual(len(errors), 5)

    def test_zip_plus_4_accepted(self):
        validate_signup(self.valid_signup(postal_code="72712-1234"))

    def test_zip_short_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(postal_code="7271"))
        self.assertIn("postal_code must be a valid US ZIP code", ctx.exception.errors)

    def test_zip_non_numeric_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(postal_code="aaaaa"))
        self.assertIn("postal_code must be a valid US ZIP code", ctx.exception.errors)

    def test_whitespace_only_first_name_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(first_name="   "))
        self.assertIn("first_name is required", ctx.exception.errors)

    def test_whitespace_only_email_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(email="   "))
        self.assertIn("email is required", ctx.exception.errors)

    def test_all_required_fields_missing(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_signup(self.valid_signup(
                first_name="", last_name="", email="",
                address_line1="", city="", state="", postal_code="",
            ))
        errors = ctx.exception.errors
        for field in ("first_name", "last_name", "email", "address_line1",
                      "city", "state", "postal_code"):
            self.assertIn(f"{field} is required", errors)

    def test_email_with_spaces_rejected(self):
        with self.assertRaises(ValidationError):
            validate_signup(self.valid_signup(email="ada @example.com"))

    def test_state_lowercase_accepted(self):
        validate_signup(self.valid_signup(state="ar"))

    def test_state_three_letters_rejected(self):
        with self.assertRaises(ValidationError):
            validate_signup(self.valid_signup(state="ARK"))

    def test_phone_optional(self):
        validate_signup(self.valid_signup(phone=""))

    def test_validation_error_is_value_error_subclass(self):
        self.assertTrue(issubclass(ValidationError, ValueError))


if __name__ == "__main__":
    unittest.main()
