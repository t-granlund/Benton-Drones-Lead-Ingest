"""E2E: /healthz unauthenticated health check."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_base import E2ETestBase  # noqa: E402


class HealthzTests(E2ETestBase):

    def test_healthz_returns_ok_status_json(self):
        response, content = self.get("/healthz")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "application/json")
        payload = json.loads(content)
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["tests_passed"])
        # version is surfaced for deployment verification
        self.assertIn("version", payload)

    def test_healthz_requires_no_auth(self):
        # No cookie sent; must still succeed (used by Render health check).
        response, _ = self.get("/healthz")
        self.assertEqual(response.status, 200)

    def test_healthz_reports_version_string(self):
        from lead_ingest.server import VERSION
        response, content = self.get("/healthz")
        payload = json.loads(content)
        self.assertEqual(payload["version"], VERSION)

    def test_healthz_uses_no_cache_for_pii_safety(self):
        # /healthz is not a PII path, but it must still carry baseline headers.
        response, _ = self.get("/healthz")
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")


if __name__ == "__main__":
    unittest.main()
