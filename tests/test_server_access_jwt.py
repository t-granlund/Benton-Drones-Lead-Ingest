"""Server-level Access JWT branch tests (unitized – no network or shared DB)."""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from unittest.mock import patch

from lead_ingest.access_jwt import AccessClaims, AccessNotEnabledError
from lead_ingest.server import Handler


@contextmanager
def access_patched(handler, enabled: bool, strict: bool, jwt_result):
    with patch("lead_ingest.server.access_is_enabled", return_value=enabled), \
         patch("lead_ingest.server.access_is_strict", return_value=strict), \
         patch("lead_ingest.server.verify_assertion", return_value=jwt_result):
        yield handler


def _make_handler() -> Handler:
    h = Handler.__new__(Handler)
    h.headers = {"Cookie": "bd_admin_session=fake"}
    h.log_message = lambda *a, **k: None
    return h


class TestServerAccessJwtBranches(unittest.TestCase):
    def test_strict_jwt_valid_allows_admin(self):
        claims = AccessClaims(
            sub="abc", email="anderson@bentondrones.com",
            aud="aud-1", iss="https://team.cloudflareaccess.com",
            iat=1000, exp=9999,
        )
        h = _make_handler()
        with access_patched(h, True, True, claims):
            self.assertTrue(h.is_admin_authenticated())

    def test_strict_jwt_missing_denies_admin(self):
        h = _make_handler()
        with access_patched(h, True, True, None):
            self.assertFalse(h.is_admin_authenticated())

    def test_non_strict_jwt_missing_falls_back_to_password(self):
        h = _make_handler()
        with access_patched(h, True, False, None):
            with patch("lead_ingest.server.verify_session_token", return_value=True):
                self.assertTrue(h.is_admin_authenticated())

    def test_disabled_normal_password_flow(self):
        h = _make_handler()
        with access_patched(h, False, False, None):
            with patch("lead_ingest.server.verify_session_token", return_value=True):
                self.assertTrue(h.is_admin_authenticated())
