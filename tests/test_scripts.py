import os
import unittest
from unittest.mock import patch

from scripts.check_dns import resolve_host
from scripts.preflight_report import env_check


class ScriptTests(unittest.TestCase):
    def test_resolve_host_handles_invalid_domain(self):
        result = resolve_host("invalid.invalid.invalid")
        self.assertEqual(result.status, "WARN")

    def test_env_check_reports_missing_optional(self):
        with patch.dict(os.environ, {}, clear=True):
            result = env_check("MISSING_OPTIONAL")
        self.assertEqual(result.status, "INFO")

    def test_env_check_reports_missing_required(self):
        with patch.dict(os.environ, {}, clear=True):
            result = env_check("MISSING_REQUIRED", required_now=True)
        self.assertEqual(result.status, "WARN")

    def test_env_check_reports_present(self):
        with patch.dict(os.environ, {"PRESENT_SECRET": "value"}, clear=True):
            result = env_check("PRESENT_SECRET")
        self.assertEqual(result.status, "PASS")


if __name__ == "__main__":
    unittest.main()
