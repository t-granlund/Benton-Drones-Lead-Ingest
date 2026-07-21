import unittest

from lead_ingest.auth import (
    ADMIN_COOKIE_NAME,
    authenticate_password,
    create_session_token,
    expired_session_cookie,
    parse_cookie,
    session_cookie,
    verify_session_token,
)


class AuthTests(unittest.TestCase):
    def test_authenticate_password_requires_configured_password(self):
        self.assertFalse(authenticate_password("anything", ""))

    def test_authenticate_password_accepts_match(self):
        self.assertTrue(authenticate_password("puppy", "puppy"))

    def test_session_token_round_trip(self):
        token = create_session_token("secret", now=100)
        self.assertTrue(verify_session_token(token, "secret", now=101))

    def test_session_token_rejects_tampering(self):
        token = create_session_token("secret", now=100)
        tampered = token.replace(".", "x.", 1)
        self.assertFalse(verify_session_token(tampered, "secret", now=101))

    def test_session_token_expires(self):
        token = create_session_token("secret", now=100)
        self.assertFalse(verify_session_token(token, "secret", now=100_000, max_age_seconds=10))

    def test_parse_cookie_extracts_admin_session(self):
        cookie = session_cookie("abc123")
        self.assertEqual(parse_cookie(cookie), "abc123")

    def test_expired_cookie_targets_admin_cookie(self):
        cookie = expired_session_cookie()
        self.assertIn(ADMIN_COOKIE_NAME, cookie)
        self.assertIn("Max-Age=0", cookie)

    def test_create_session_token_empty_secret_raises(self):
        with self.assertRaises(ValueError):
            create_session_token("")

    def test_verify_session_token_empty_token_returns_false(self):
        self.assertFalse(verify_session_token("", "secret"))

    def test_verify_session_token_empty_secret_returns_false(self):
        token = create_session_token("secret", now=100)
        self.assertFalse(verify_session_token(token, ""))

    def test_verify_session_token_no_dot_returns_false(self):
        self.assertFalse(verify_session_token("nodothere", "secret"))

    def test_verify_session_token_future_iat_returns_false(self):
        token = create_session_token("secret", now=100)
        # A token issued in the future (negative age) should be rejected.
        self.assertFalse(verify_session_token(token, "secret", now=50))

    def test_verify_session_token_wrong_secret_returns_false(self):
        token = create_session_token("secret-a", now=100)
        self.assertFalse(verify_session_token(token, "secret-b", now=101))

    def test_session_cookie_secure_includes_secure_flag(self):
        cookie = session_cookie("token123", secure=True)
        self.assertIn("Secure", cookie)
        self.assertIn(ADMIN_COOKIE_NAME, cookie)

    def test_session_cookie_not_secure_omits_secure_flag(self):
        cookie = session_cookie("token123", secure=False)
        self.assertNotIn("Secure", cookie)

    def test_session_cookie_includes_httponly_and_samesite(self):
        cookie = session_cookie("token123")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        self.assertIn("Path=/", cookie)

    def test_parse_cookie_empty_header_returns_empty(self):
        self.assertEqual(parse_cookie(""), "")

    def test_parse_cookie_missing_admin_cookie_returns_empty(self):
        self.assertEqual(parse_cookie("other_cookie=value"), "")

    def test_parse_cookie_with_other_cookies_still_extracts(self):
        cookie = f"foo=bar; {ADMIN_COOKIE_NAME}=mytoken; baz=qux"
        self.assertEqual(parse_cookie(cookie), "mytoken")

    def test_authenticate_password_rejects_mismatch(self):
        self.assertFalse(authenticate_password("wrong", "correct"))

    def test_authenticate_password_rejects_empty_candidate(self):
        self.assertFalse(authenticate_password("", "configured"))


if __name__ == "__main__":
    unittest.main()
