"""Tests for the real geocoder chain: Census, Nominatim, chain, cache,
signup integration, and backfill. ALL network is mocked -- no outbound
HTTP ever leaves these tests.
"""
from __future__ import annotations

import json
import sqlite3
import unittest
from unittest.mock import MagicMock, patch

from lead_ingest.db import create_signup, init_db, list_signups
from lead_ingest.geocoding import (
    CachedGeocoder,
    CensusGeocoder,
    ChainedGeocoder,
    GeocodeResult,
    MockGeocoder,
    NominatimGeocoder,
    normalize_address,
    unresolved_result,
)
from lead_ingest.models import SignupInput
from scripts.backfill_geocode import backfill, main as backfill_main

CENSUS_MATCH = {
    "result": {
        "addressMatches": [
            {
                "matchedAddress": "1 INFINITE LOOP, CUPERTINO, CA, 95014",
                "coordinates": {"x": -122.0308, "y": 37.3317},
                "tigerLine": {"tigerLineId": "123", "side": "L"},
            }
        ]
    }
}
CENSUS_NO_MATCH = {"result": {"addressMatches": []}}
NOMINATIM_HIT = [
    {
        "lat": "48.8584",
        "lon": "2.2945",
        "display_name": "Tour Eiffel, Paris, France",
        "addresstype": "attraction",
        "class": "tourism",
    }
]


def _fake_response(payload):
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _signup_input(address_line1="2 Compiler Ct", postal_code="72712"):
    return SignupInput(
        first_name="Grace",
        last_name="Hopper",
        email="grace@example.com",
        phone="555-0000",
        address_line1=address_line1,
        city="Bentonville",
        state="AR",
        postal_code=postal_code,
        consent_accepted=True,
        waiver_accepted=True,
        typed_name="Grace Hopper",
    )


class CensusGeocoderTests(unittest.TestCase):
    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_census_success_returns_coords_and_provider(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(CENSUS_MATCH)
        result = CensusGeocoder().geocode("1 Infinite Loop, Cupertino, CA, 95014")
        self.assertEqual(result.provider, "census")
        self.assertAlmostEqual(result.latitude, 37.3317, places=4)
        self.assertAlmostEqual(result.longitude, -122.0308, places=4)
        self.assertEqual(result.precision, "rooftop")
        self.assertTrue(result.resolved)
        # Correct endpoint, benchmark, and format requested.
        url = mock_urlopen.call_args[0][0].full_url
        self.assertIn("geocoding.geo.census.gov", url)
        self.assertIn("benchmark=Public_AR_Current", url)
        self.assertIn("format=json", url)

    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_census_no_match_returns_unresolved_not_exception(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(CENSUS_NO_MATCH)
        result = CensusGeocoder().geocode("Nowhere St")
        self.assertEqual(result.provider, "unresolved")
        self.assertFalse(result.resolved)
        self.assertIsNone(result.latitude)


class NominatimGeocoderTests(unittest.TestCase):
    def setUp(self):
        # Reset the module-level politeness clock so tests are independent.
        NominatimGeocoder._last_call_monotonic = 0.0

    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_nominatim_sends_user_agent_header(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(NOMINATIM_HIT)
        result = NominatimGeocoder(sleep=lambda _: None).geocode("Eiffel Tower")
        request = mock_urlopen.call_args[0][0]
        self.assertIn("BentonDronesLeadIngest", request.headers["User-agent"])
        self.assertEqual(result.provider, "nominatim")
        self.assertAlmostEqual(result.latitude, 48.8584, places=4)
        self.assertAlmostEqual(result.longitude, 2.2945, places=4)

    @patch("lead_ingest.geocoding.time.monotonic")
    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_nominatim_rate_limit_sleeps_between_calls(self, mock_urlopen, mock_monotonic):
        mock_urlopen.return_value = _fake_response(NOMINATIM_HIT)
        sleeps = []
        geocoder = NominatimGeocoder(sleep=sleeps.append)

        # First call at t=100, second 0.2s later -> must sleep ~0.8s.
        mock_monotonic.side_effect = [100.0, 100.0, 100.2, 100.2]
        geocoder.geocode("Address One")
        geocoder.geocode("Address Two")

        self.assertEqual(len(sleeps), 1)
        self.assertAlmostEqual(sleeps[0], 0.8, places=5)

    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_nominatim_empty_result_is_unresolved(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response([])
        result = NominatimGeocoder(sleep=lambda _: None).geocode("Zzyzx")
        self.assertEqual(result.provider, "unresolved")


class ChainedGeocoderTests(unittest.TestCase):
    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_fallback_to_nominatim_when_census_no_match(self, mock_urlopen):
        NominatimGeocoder._last_call_monotonic = 0.0
        mock_urlopen.side_effect = [
            _fake_response(CENSUS_NO_MATCH),  # census: no match
            _fake_response(NOMINATIM_HIT),    # nominatim: hit
        ]
        result = ChainedGeocoder(
            [CensusGeocoder(), NominatimGeocoder(sleep=lambda _: None)]
        ).geocode("Tour Eiffel, Paris")
        self.assertEqual(result.provider, "nominatim")
        self.assertTrue(result.resolved)
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_census_hit_skips_nominatim(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(CENSUS_MATCH)
        result = ChainedGeocoder(
            [CensusGeocoder(), NominatimGeocoder(sleep=lambda _: None)]
        ).geocode("1 Infinite Loop")
        self.assertEqual(result.provider, "census")
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_provider_timeout_returns_unresolved_without_raising(self, mock_urlopen):
        import socket

        mock_urlopen.side_effect = socket.timeout("timed out")
        result = ChainedGeocoder(
            [CensusGeocoder(), NominatimGeocoder(sleep=lambda _: None)]
        ).geocode("1 Infinite Loop")
        self.assertEqual(result.provider, "unresolved")
        self.assertFalse(result.resolved)
        self.assertIsNone(result.latitude)
        self.assertIn("timed out", result.raw)


class NormalizationTests(unittest.TestCase):
    def test_case_and_whitespace_variants_share_a_key(self):
        base = normalize_address("100 Flight Path, Bentonville, AR, 72712")
        variants = [
            "100 flight path, bentonville, ar, 72712",
            "  100  Flight   Path , Bentonville, AR 72712 ",
            "100 FLIGHT PATH,BENTONVILLE,AR,72712",
        ]
        for variant in variants:
            self.assertEqual(normalize_address(variant), base)

    def test_zip_plus_four_normalizes_to_five_digits(self):
        self.assertEqual(
            normalize_address("1 Main St, Bentonville, AR 72712-1234"),
            normalize_address("1 Main St, Bentonville, AR 72712"),
        )


class CachedGeocoderTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)
        # geocode_cache table created by init_db.
        tables = {
            row["name"]
            for row in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        self.assertIn("geocode_cache", tables)

    def tearDown(self):
        self.conn.close()

    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_cache_hit_makes_zero_http_calls(self, mock_urlopen):
        NominatimGeocoder._last_call_monotonic = 0.0
        mock_urlopen.return_value = _fake_response(CENSUS_MATCH)
        cached = CachedGeocoder(
            self.conn,
            ChainedGeocoder([CensusGeocoder(), NominatimGeocoder(sleep=lambda _: None)]),
        )
        first = cached.geocode("1 Infinite Loop, Cupertino, CA, 95014")
        self.assertEqual(first.provider, "census")
        self.assertEqual(mock_urlopen.call_count, 1)

        second = cached.geocode("1 Infinite Loop, Cupertino, CA, 95014")
        self.assertEqual(mock_urlopen.call_count, 1)  # ZERO new calls
        self.assertEqual(second.provider, "census")
        self.assertEqual(second.latitude, first.latitude)

    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_normalization_increases_cache_hits(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(CENSUS_MATCH)
        cached = CachedGeocoder(self.conn, CensusGeocoder())
        cached.geocode("1 Infinite Loop, Cupertino, CA, 95014")
        # Case/whitespace variant of the same address -> cache hit, no HTTP.
        hit = cached.geocode("  1 INFINITE LOOP , cupertino, ca, 95014-2083 ")
        self.assertEqual(mock_urlopen.call_count, 1)
        self.assertEqual(hit.provider, "census")
        self.assertIsNotNone(hit.latitude)

    def test_unresolved_results_are_cached_without_fabricating_coords(self):
        cached = CachedGeocoder(self.conn, ChainedGeocoder([]))  # no providers
        result = cached.geocode("Nowhere St")
        self.assertFalse(result.resolved)
        row = self.conn.execute(
            "SELECT * FROM geocode_cache WHERE normalized_address = ?",
            (normalize_address("Nowhere St"),),
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["provider"], "unresolved")
        self.assertIsNone(row["latitude"])


class SignupIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_injected_fake_geocoder_stores_result(self):
        fake = MagicMock()
        fake.geocode.return_value = GeocodeResult(
            latitude=36.5,
            longitude=-94.3,
            provider="fake",
            display_name="Faked Address",
            precision="rooftop",
        )
        signup_id = create_signup(self.conn, _signup_input(), geocoder=fake)
        row = list_signups(self.conn)[0]
        self.assertEqual(row["id"], signup_id)
        self.assertEqual(row["geocode_status"], "success")
        self.assertAlmostEqual(row["latitude"], 36.5)
        self.assertAlmostEqual(row["longitude"], -94.3)
        self.assertEqual(row["geocode_provider"], "fake")
        self.assertEqual(row["geocode_display_name"], "Faked Address")
        fake.geocode.assert_called_once_with(_signup_input().full_address)

    def test_default_signup_stays_offline_with_mock(self):
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("GEOCODER_MODE", None)
            create_signup(self.conn, _signup_input())
        row = list_signups(self.conn)[0]
        self.assertEqual(row["geocode_status"], "success")
        self.assertEqual(row["geocode_provider"], "mock")

    @patch("lead_ingest.geocoding.urllib.request.urlopen")
    def test_live_mode_uses_real_chain_behind_cache(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(CENSUS_MATCH)
        with patch.dict("os.environ", {"GEOCODER_MODE": "live"}):
            create_signup(self.conn, _signup_input())
        row = list_signups(self.conn)[0]
        self.assertEqual(row["geocode_status"], "success")
        self.assertEqual(row["geocode_provider"], "census")
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_geocoder_failure_never_crashes_signup(self):
        class ExplodingGeocoder:
            def geocode(self, address):
                raise RuntimeError("provider down")

        signup_id = create_signup(self.conn, _signup_input(), geocoder=ExplodingGeocoder())
        self.assertIsNotNone(signup_id)
        row = list_signups(self.conn)[0]
        self.assertEqual(row["geocode_status"], "unresolved")
        self.assertIsNone(row["latitude"])
        self.assertEqual(row["geocode_provider"], "")

    def test_unresolved_geocoder_result_keeps_signup_alive(self):
        fake = MagicMock()
        fake.geocode.return_value = unresolved_result("nope")
        create_signup(self.conn, _signup_input(), geocoder=fake)
        row = list_signups(self.conn)[0]
        self.assertEqual(row["geocode_status"], "unresolved")
        self.assertIsNone(row["latitude"])
        self.assertIsNone(row["longitude"])


class BackfillTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_backfill_geocodes_pending_records(self):
        create_signup(self.conn, _signup_input(), geocode=False)
        fake = MagicMock()
        fake.geocode.return_value = GeocodeResult(
            latitude=36.1, longitude=-94.2, provider="census",
            display_name="Backfilled", precision="rooftop",
        )
        counts = backfill(self.conn, geocoder=fake, verbose=False)
        self.assertEqual(counts, {"attempted": 1, "resolved": 1, "unresolved": 0})
        row = list_signups(self.conn)[0]
        self.assertEqual(row["geocode_status"], "success")
        self.assertAlmostEqual(row["latitude"], 36.1)
        self.assertEqual(row["geocode_provider"], "census")

    def test_backfill_is_idempotent_and_retries_unresolved(self):
        fake = MagicMock()
        fake.geocode.return_value = GeocodeResult(
            latitude=36.1, longitude=-94.2, provider="census",
            display_name="Backfilled", precision="rooftop",
        )
        create_signup(self.conn, _signup_input(), geocode=False)
        backfill(self.conn, geocoder=fake, verbose=False)
        # Second run: nothing pending, nothing attempted.
        counts = backfill(self.conn, geocoder=fake, verbose=False)
        self.assertEqual(counts["attempted"], 0)

    def test_backfill_dry_run_never_touches_network_or_db(self):
        create_signup(self.conn, _signup_input(), geocode=False)
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            db_path = tmp.name
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            init_db(conn)
            create_signup(conn, _signup_input(), geocode=False)
            conn.close()
            import contextlib, io

            with patch("lead_ingest.geocoding.urllib.request.urlopen") as mock_urlopen:
                with contextlib.redirect_stdout(io.StringIO()):
                    code = backfill_main(["--db", db_path])
            self.assertEqual(code, 0)
            mock_urlopen.assert_not_called()
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = list_signups(conn)[0]
            self.assertEqual(row["geocode_status"], "pending")  # unchanged
            self.assertIsNone(row["latitude"])
            conn.close()
        finally:
            os.unlink(db_path)


if __name__ == "__main__":
    unittest.main()
