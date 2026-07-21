"""Tests for the MockGeocoder — determinism, provider, and display name."""
import unittest

from lead_ingest.geocoding import MockGeocoder
from lead_ingest.models import SignupInput


class MockGeocoderTests(unittest.TestCase):
    def setUp(self):
        self.geocoder = MockGeocoder()

    def test_geocode_returns_result_with_provider(self):
        result = self.geocoder.geocode("100 Flight Path, Bentonville, AR, 72712")
        self.assertEqual(result.provider, "mock")

    def test_geocode_display_name_is_address(self):
        address = "100 Flight Path, Bentonville, AR, 72712"
        result = self.geocoder.geocode(address)
        self.assertEqual(result.display_name, address)

    def test_geocode_is_deterministic_same_address(self):
        address = "200 Orchard Way, Bentonville, AR, 72712"
        result1 = self.geocoder.geocode(address)
        result2 = self.geocoder.geocode(address)
        self.assertEqual(result1.latitude, result2.latitude)
        self.assertEqual(result1.longitude, result2.longitude)

    def test_geocode_different_addresses_different_coords(self):
        result1 = self.geocoder.geocode("100 Flight Path, Bentonville, AR, 72712")
        result2 = self.geocoder.geocode("200 Orchard Way, Bentonville, AR, 72712")
        # Different addresses should produce different coordinates
        # (seed is based on character sum).
        self.assertNotEqual(
            (result1.latitude, result1.longitude),
            (result2.latitude, result2.longitude),
        )

    def test_geocode_coords_near_nwa(self):
        result = self.geocoder.geocode("100 Flight Path, Bentonville, AR, 72712")
        # Should be near Northwest Arkansas (Bentonville ~36.37, -94.20).
        self.assertAlmostEqual(result.latitude, 36.37, delta=0.1)
        self.assertAlmostEqual(result.longitude, -94.20, delta=0.1)

    def test_geocode_raw_is_json_string(self):
        result = self.geocoder.geocode("100 Flight Path, Bentonville, AR, 72712")
        # The default raw is "{}".
        self.assertEqual(result.raw, "{}")


if __name__ == "__main__":
    unittest.main()
