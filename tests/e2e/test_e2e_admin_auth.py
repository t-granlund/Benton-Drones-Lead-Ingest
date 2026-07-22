"""E2E: admin authentication (/admin-login, /admin, /admin-logout).

Covers: login form renders, CSRF required, wrong password rejected, correct
password sets a session cookie + redirects to /admin, unauthenticated /admin
redirects to login, logout clears the session, and a tampered cookie is rejected.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_base import E2ETestBase, ADMIN_PASSWORD  # noqa: E402


class AdminAuthTests(E2ETestBase):

    def test_login_page_renders_with_csrf(self):
        response, content = self.get("/admin-login")
        self.assertEqual(response.status, 200)
        self.assertIn(b'name="csrf_token"', content)
        self.assertIn(b'name="password"', content)

    def test_admin_unauthenticated_redirects_to_login(self):
        response, _ = self.get("/admin")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")

    def test_admin_lead_detail_unauthenticated_redirects(self):
        response, _ = self.get("/admin/lead/1")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")

    def test_login_without_csrf_returns_400(self):
        response, content = self.post_form(
            "/admin-login", {"password": ADMIN_PASSWORD}
        )
        self.assertEqual(response.status, 400)
        self.assertIn(b"invalid CSRF token", content)

    def test_login_wrong_password_returns_401(self):
        csrf = self.login_csrf()
        response, content = self.post_form(
            "/admin-login",
            {"password": "definitely-wrong", "csrf_token": csrf},
        )
        self.assertEqual(response.status, 401)
        self.assertIn(b"invalid admin password", content)

    def test_login_correct_password_redirects_with_session_cookie(self):
        response, _ = self.login()
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin")
        cookie = response.getheader("Set-Cookie") or ""
        self.assertIn("session=", cookie)

    def test_admin_with_valid_session_returns_200(self):
        cookie = self.admin_cookie()
        response, content = self.get("/admin", cookie=cookie)
        self.assertEqual(response.status, 200)
        self.assertTrue(content)

    def test_admin_with_tampered_session_cookie_redirects(self):
        response, _ = self.get("/admin", cookie="session=tampered-bogus-value")
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")

    def test_logout_redirects_and_clears_session(self):
        cookie = self.admin_cookie()
        # First confirm we are authed.
        response, _ = self.get("/admin", cookie=cookie)
        self.assertEqual(response.status, 200)
        # Then log out.
        response, _ = self.get("/admin-logout", cookie=cookie)
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "/admin-login")
        set_cookie = response.getheader("Set-Cookie") or ""
        # An expired/cleared cookie is sent (Max-Age=0 / Expires in the past).
        self.assertIn("session=", set_cookie)

    def test_login_csrf_is_scoped_to_admin_login_action(self):
        # A signup-scoped token must not authorise a login.
        response, content = self.post_form(
            "/admin-login",
            {"password": ADMIN_PASSWORD, "csrf_token": self.signup_csrf()},
        )
        self.assertEqual(response.status, 400)
        self.assertIn(b"invalid CSRF token", content)


if __name__ == "__main__":
    unittest.main()
