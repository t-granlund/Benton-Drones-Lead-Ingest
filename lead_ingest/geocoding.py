from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeocodeResult:
    latitude: float
    longitude: float
    provider: str = "mock"
    display_name: str = "Mock geocode result"
    raw: str = "{}"


class MockGeocoder:
    """Deterministic local geocoder for tests/dev. No external calls. Good puppy."""

    def geocode(self, full_address: str) -> GeocodeResult:
        seed = sum(ord(char) for char in full_address)
        lat = 36.372 + (seed % 1000) / 100000
        lng = -94.208 - (seed % 1000) / 100000
        return GeocodeResult(latitude=lat, longitude=lng, display_name=full_address)
