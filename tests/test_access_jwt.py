"""Tests for Cloudflare Access JWT verification (env-gated, fail-closed)."""

from __future__ import annotations

import base64
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from lead_ingest import access_jwt
from urllib.error import URLError
from lead_ingest.access_jwt import (
    AccessJwksError,
    AccessNotEnabledError,
    AccessVerifyError,
    _JwksCache,
    assertion_header,
    config_from_env,
    is_enabled,
    is_strict,
    verify_assertion,
    verify_or_none,
)


class AccessJwtTestBase(unittest.TestCase):
    """Base class that saves/restores CF_ACCESS_* env vars."""

    def setUp(self):
        self._old_env = {}
        for key in ("CF_ACCESS_TEAM_DOMAIN", "CF_ACCESS_AUD", "CF_ACCESS_STRICT", "CF_ACCESS_JWKS_TTL"):
            self._old_env[key] = os.environ.get(key)
            os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _make_claims() -> dict:
    return {
        "sub": "abc123",
        "email": "anderson@bentondrones.com",
        "aud": "dummy-aud",
        "iss": "https://bentondrones.cloudflareaccess.com",
        "iat": 1000000000,
        "exp": 9999999999,
    }


class TestAccessConfig(AccessJwtTestBase):
    def test_is_enabled_requires_both_env_vars(self):
        os.environ["CF_ACCESS_TEAM_DOMAIN"] = "bentondrones"
        os.environ.pop("CF_ACCESS_AUD", None)
        self.assertFalse(is_enabled())

        os.environ["CF_ACCESS_AUD"] = "aud-tag-123"
        self.assertTrue(is_enabled())

    def test_is_strict_requires_flag(self):
        os.environ["CF_ACCESS_TEAM_DOMAIN"] = "bentondrones"
        os.environ["CF_ACCESS_AUD"] = "aud-123"
        self.assertFalse(is_strict())
        os.environ["CF_ACCESS_STRICT"] = "1"
        self.assertTrue(is_strict())

    def test_config_from_env(self):
        os.environ["CF_ACCESS_TEAM_DOMAIN"] = "bentondrones"
        os.environ["CF_ACCESS_AUD"] = "aud-123"
        os.environ["CF_ACCESS_STRICT"] = "1"
        cfg = config_from_env()
        assert cfg["team_domain"] == "bentondrones"
        assert cfg["aud"] == "aud-123"
        assert cfg["strict"] is True


class TestAssertionHeader:
    def test_header_name(self):
        assert assertion_header == "Cf-Access-Jwt-Assertion"


class TestVerifyAssertionNoConfig(AccessJwtTestBase):
    def test_raises_not_enabled(self):
        headers = {assertion_header: "dummy"}
        with self.assertRaises(AccessNotEnabledError):
            verify_assertion(headers)

    def test_verify_or_none_returns_none(self):
        headers = {assertion_header: "dummy"}
        self.assertIsNone(verify_or_none(headers))


class TestVerifyAssertionMissingHeader(AccessJwtTestBase):
    def setUp(self):
        super().setUp()
        os.environ["CF_ACCESS_TEAM_DOMAIN"] = "bentondrones"
        os.environ["CF_ACCESS_AUD"] = "aud-123"

    def test_raises_missing_header(self):
        headers = {}
        with self.assertRaises(AccessVerifyError) as ctx:
            verify_assertion(headers)
        self.assertIn("missing", str(ctx.exception).lower())
        self.assertIn(assertion_header, str(ctx.exception))


class TestVerifyAssertionSuccessPath(AccessJwtTestBase):
    def setUp(self):
        super().setUp()
        os.environ["CF_ACCESS_TEAM_DOMAIN"] = "bentondrones"
        os.environ["CF_ACCESS_AUD"] = "aud-123"

    @patch.object(access_jwt, "_decode_and_verify")
    def test_success_returns_claims(self, mock_decode):
        mock_decode.return_value = _make_claims()
        headers = {assertion_header: "dummy-token"}
        claims = verify_assertion(headers)
        self.assertEqual(claims.sub, "abc123")
        self.assertEqual(claims.email, "anderson@bentondrones.com")
        self.assertEqual(claims.aud, "dummy-aud")
        self.assertEqual(claims.iss, "https://bentondrones.cloudflareaccess.com")
        mock_decode.assert_called_once()

    @patch.object(access_jwt, "_decode_and_verify")
    def test_success_sets_loggable_email(self, mock_decode):
        mock_decode.return_value = _make_claims()
        headers = {assertion_header: "dummy-token"}
        claims = verify_assertion(headers)
        self.assertIsInstance(claims.email, str)
        self.assertIn("@", claims.email)


# Real RSA public keys (PEM format, base64url) for test use only
_TEST_KEY1_N = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF0SS8xZUlULzZSWFVKMmdBM2wySAo2U0cxU25tMUIyTnJNQ1hYSFpzdlZoYnp0YWl0SGJVTUNwWXRBVk00a1BxUmlGUG5CeThoRC9nVGdRU05KR2dwCnZaWnorbEFjYmo2c1ArUzdOczQxOVN4d2MrU3JWQ0hST1FC"
_TEST_KEY2_N = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF3ZXNVTFh6bXhlTytMUk91VXBKVwpBT1hLZGRpQTlCUGRLeUJHRXZLR0JtQ2lCZVJGNUlTYVRxMllVZFc1SVEyVG45Z0hIWUFGYlp5VHc3alBwSk1tClA4UjZvV1ZmZVFRNk1BVU15UzRxa1JEdEZaN3hFWFpXT0lnQUE9PQo="


class TestJwksCacheFetch(unittest.TestCase):
    def setUp(self):
        self._old_env = {}
        for key in ("CF_ACCESS_TEAM_DOMAIN", "CF_ACCESS_AUD", "CF_ACCESS_STRICT", "CF_ACCESS_JWKS_TTL"):
            self._old_env[key] = os.environ.get(key)
            os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_fetch_successful_loads_keys(self):
        fake_keys = [
            {"kid": "k1", "kty": "RSA", "n": _TEST_KEY1_N, "e": "AQAB"},
            {"kid": "k2", "kty": "RSA", "n": _TEST_KEY2_N, "e": "AQAB"},
        ]
        fake_body = json.dumps({"keys": fake_keys}).encode()
        with patch.object(access_jwt, "_fetch_url", return_value=fake_body) as mock_fetch:
            cache = _JwksCache("bentondrones")
            cache._fetch()
            self.assertEqual(len(cache._keys), 2)
            self.assertGreater(cache._fetched_at, 0)
            mock_fetch.assert_called_once()

    def test_get_key_returns_public_key(self):
        fake_keys = [{"kid": "k1", "kty": "RSA", "n": _TEST_KEY1_N, "e": "AQAB"}]
        fake_body = json.dumps({"keys": fake_keys}).encode()
        with patch.object(access_jwt, "_fetch_url", return_value=fake_body):
            cache = _JwksCache("bentondrones")
            key = cache.get_key("k1")
            # PyJWT RSAAlgorithm returns a key object; from_jwk returns
            # a public key object with the same interface
            self.assertIsNotNone(key)
            # Should have the object PyJWT returns (not None)
            self.assertIsNotNone(key.public_key if hasattr(key, 'public_key') else key)

    def test_fetch_propagates_error(self):
        def raise_error(*args, **kwargs):
            raise URLError("Connection refused")

        with patch.object(access_jwt, "_fetch_url", side_effect=raise_error):
            cache = _JwksCache("bentondrones")
            with self.assertRaises(AccessJwksError):
                cache._fetch()

    def test_get_key_refreshes_on_miss(self):
        # First fetch returns k1
        fake_keys = [{"kid": "k1", "kty": "RSA", "n": _TEST_KEY1_N, "e": "AQAB"}]
        fake_body = json.dumps({"keys": fake_keys}).encode()
        with patch.object(access_jwt, "_fetch_url", return_value=fake_body) as mock_fetch:
            cache = _JwksCache("bentondrones")
            key = cache.get_key("k1")
            self.assertIsNotNone(key)
            self.assertEqual(mock_fetch.call_count, 1)

            # Within TTL, no refresh
            key = cache.get_key("k1")
            self.assertEqual(mock_fetch.call_count, 1)

            # Unknown kid forces refresh attempt
            fake_keys2 = [
                {"kid": "k1", "kty": "RSA", "n": _TEST_KEY1_N, "e": "AQAB"},
                {"kid": "k2", "kty": "RSA", "n": _TEST_KEY2_N, "e": "AQAB"},
            ]
            fake_body2 = json.dumps({"keys": fake_keys2}).encode()
            mock_fetch.return_value = fake_body2
            key = cache.get_key("k2")
            self.assertEqual(mock_fetch.call_count, 2)


class TestJwksCachingTtlExpiry(unittest.TestCase):
    def test_get_key_refreshes_after_ttl(self):
        fake_keys = [{"kid": "k1", "kty": "RSA", "n": _TEST_KEY1_N, "e": "AQAB"}]
        fake_body = json.dumps({"keys": fake_keys}).encode()

        with patch.object(access_jwt, "_fetch_url", return_value=fake_body) as mock_fetch:
            os.environ["CF_ACCESS_TEAM_DOMAIN"] = "bentondrones"
            os.environ["CF_ACCESS_AUD"] = "aud-123"
            os.environ["CF_ACCESS_JWKS_TTL"] = "1"
            cache = _JwksCache("bentondrones", ttl=1)
            cache.get_key("k1")
            self.assertEqual(mock_fetch.call_count, 1)

            # Push fetched_at back beyond TTL
            cache._fetched_at -= 2
            cache.get_key("k1")
            self.assertEqual(mock_fetch.call_count, 2)

        # Clean up env
        for key in ("CF_ACCESS_TEAM_DOMAIN", "CF_ACCESS_AUD", "CF_ACCESS_JWKS_TTL"):
            os.environ.pop(key, None)
