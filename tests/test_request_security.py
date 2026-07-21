import unittest

from lead_ingest.request_security import RateLimiter, create_csrf_token, verify_csrf_token


class RequestSecurityTests(unittest.TestCase):
    def test_csrf_token_round_trip(self):
        token = create_csrf_token("secret", "signup", now=100)
        self.assertTrue(verify_csrf_token(token, "secret", "signup", now=101))

    def test_csrf_rejects_wrong_action(self):
        token = create_csrf_token("secret", "signup", now=100)
        self.assertFalse(verify_csrf_token(token, "secret", "admin-login", now=101))

    def test_csrf_rejects_tampering(self):
        token = create_csrf_token("secret", "signup", now=100)
        tampered = token.replace(".", "x.", 1)
        self.assertFalse(verify_csrf_token(tampered, "secret", "signup", now=101))

    def test_csrf_expires(self):
        token = create_csrf_token("secret", "signup", now=100)
        self.assertFalse(verify_csrf_token(token, "secret", "signup", now=500, max_age_seconds=10))

    def test_rate_limiter_allows_until_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        self.assertTrue(limiter.allow("ip:/signup", now=1))
        self.assertTrue(limiter.allow("ip:/signup", now=2))
        self.assertFalse(limiter.allow("ip:/signup", now=3))

    def test_rate_limiter_window_resets(self):
        limiter = RateLimiter(max_requests=1, window_seconds=10)
        self.assertTrue(limiter.allow("ip:/signup", now=1))
        self.assertFalse(limiter.allow("ip:/signup", now=2))
        self.assertTrue(limiter.allow("ip:/signup", now=12))


if __name__ == "__main__":
    unittest.main()
