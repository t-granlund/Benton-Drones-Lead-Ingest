"""Tests for the JSON admin API, CORS gating, and admin audit trail (ADR-001)."""

from __future__ import annotations

import json
import os
import unittest
from urllib.parse import urlencode

from lead_ingest import admin_api
from tests.test_production_hardening import HardeningServerBase


class AdminApiBase(HardeningServerBase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("CORS_ADMIN_ORIGIN",)}
        os.environ.pop("CORS_ADMIN_ORIGIN", None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TestAdminApiAuth(AdminApiBase):
    def test_api_requires_auth_redirect_or_403(self):
        response, _ = self.request("GET", "/admin/api/summary")
        # require_admin_export returns 403 for unauthenticated API clients
        self.assertEqual(response.status, 403)

    def test_api_summary_with_session_cookie(self):
        cookie = self.login_cookie()
        response, body = self.request("GET", "/admin/api/summary", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        data = json.loads(body)
        for key in ("total", "today", "this_week", "pending_geocodes",
                    "jira_pending", "email_pending"):
            self.assertIn(key, data)

    def test_api_leads_list_with_session_cookie(self):
        cookie = self.login_cookie()
        response, body = self.request("GET", "/admin/api/leads", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn("leads", json.loads(body))

    def test_api_lead_detail_404_for_missing(self):
        cookie = self.login_cookie()
        response, body = self.request("GET", "/admin/api/lead/99999", headers={"Cookie": cookie})
        self.assertEqual(response.status, 404)

    def test_api_routes_have_noindex_header(self):
        cookie = self.login_cookie()
        response, _ = self.request("GET", "/admin/api/summary", headers={"Cookie": cookie})
        self.assertIn("noindex", response.getheader("X-Robots-Tag", ""))


class TestCorsGating(AdminApiBase):
    def _login(self):
        return self.login_cookie()

    def test_no_cors_headers_when_env_unset(self):
        os.environ.pop("CORS_ADMIN_ORIGIN", None)
        cookie = self._login()
        response, _ = self.request(
            "GET", "/admin/api/summary",
            headers={"Cookie": cookie, "Origin": "https://admin.bentondrones.com"},
        )
        self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))

    def test_cors_headers_for_matching_origin(self):
        os.environ["CORS_ADMIN_ORIGIN"] = "https://admin.bentondrones.com"
        cookie = self._login()
        response, _ = self.request(
            "GET", "/admin/api/summary",
            headers={"Cookie": cookie, "Origin": "https://admin.bentondrones.com"},
        )
        self.assertEqual(
            response.getheader("Access-Control-Allow-Origin"),
            "https://admin.bentondrones.com",
        )
        self.assertEqual(response.getheader("Access-Control-Allow-Credentials"), "true")

    def test_no_cors_headers_for_wrong_origin(self):
        os.environ["CORS_ADMIN_ORIGIN"] = "https://admin.bentondrones.com"
        cookie = self._login()
        response, _ = self.request(
            "GET", "/admin/api/summary",
            headers={"Cookie": cookie, "Origin": "https://evil.example.com"},
        )
        self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))

    def test_origin_never_wildcard(self):
        os.environ["CORS_ADMIN_ORIGIN"] = "https://admin.bentondrones.com"
        cookie = self._login()
        response, _ = self.request(
            "GET", "/admin/api/summary",
            headers={"Cookie": cookie, "Origin": "https://admin.bentondrones.com"},
        )
        self.assertNotEqual(response.getheader("Access-Control-Allow-Origin"), "*")

    def test_preflight_options_returns_204_with_headers(self):
        os.environ["CORS_ADMIN_ORIGIN"] = "https://admin.bentondrones.com"
        response, _ = self.request(
            "OPTIONS", "/admin/api/summary",
            headers={"Origin": "https://admin.bentondrones.com"},
        )
        self.assertEqual(response.status, 204)
        self.assertEqual(
            response.getheader("Access-Control-Allow-Origin"),
            "https://admin.bentondrones.com",
        )
        self.assertIn("Cf-Access-Jwt-Assertion",
                      response.getheader("Access-Control-Allow-Headers", ""))

    def test_preflight_rejected_for_bad_origin(self):
        os.environ["CORS_ADMIN_ORIGIN"] = "https://admin.bentondrones.com"
        response, _ = self.request(
            "OPTIONS", "/admin/api/summary",
            headers={"Origin": "https://evil.example.com"},
        )
        self.assertEqual(response.status, 204)
        self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))

    def test_options_404_for_non_api_route(self):
        response, _ = self.request("OPTIONS", "/signup",
                                   headers={"Origin": "https://admin.bentondrones.com"})
        self.assertEqual(response.status, 404)


class TestAdminAudit(AdminApiBase):
    def test_password_login_writes_audit_row(self):
        cookie = self.login_cookie()  # successful password login
        self.assertIsNotNone(cookie)
        response, body = self.request("GET", "/admin/api/audit", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        events = json.loads(body)["events"]
        types = [e["event_type"] for e in events]
        self.assertIn("password_login", types)
        row = [e for e in events if e["event_type"] == "password_login"][0]
        self.assertEqual(row["actor"], "shared-admin")

    def test_audit_endpoint_requires_auth(self):
        response, _ = self.request("GET", "/admin/api/audit")
        self.assertEqual(response.status, 403)


class TestAdminApiHelpers(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("CORS_ADMIN_ORIGIN")

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("CORS_ADMIN_ORIGIN", None)
        else:
            os.environ["CORS_ADMIN_ORIGIN"] = self._saved

    def test_allowed_origin_trailing_slash_normalised(self):
        os.environ["CORS_ADMIN_ORIGIN"] = "https://admin.bentondrones.com/"
        self.assertEqual(admin_api.allowed_origin(), "https://admin.bentondrones.com")

    def test_origin_match_exact_only(self):
        os.environ["CORS_ADMIN_ORIGIN"] = "https://admin.bentondrones.com"
        headers = {"Origin": "https://admin.bentondrones.com.evil.io"}
        self.assertFalse(admin_api.request_origin_is_allowed(headers))
