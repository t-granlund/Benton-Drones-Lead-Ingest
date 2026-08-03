"""Geocoding provider chain for Benton Lead-Ingest.

A single ``geocode(address) -> GeocodeResult`` interface fronts three
providers:

- :class:`MockGeocoder` -- deterministic offline fake (tests/dev default).
- :class:`CensusGeocoder` -- US Census Bureau oneline-address geocoder
  (free, keyless). Primary provider for US street addresses.
- :class:`NominatimGeocoder` -- OpenStreetMap Nominatim fallback for
  Census-unmatchable addresses. Identifying User-Agent and <= 1 req/s
  per the Nominatim usage policy.

:class:`ChainedGeocoder` composes them, and :class:`CachedGeocoder`
persists results in the ``geocode_cache`` table so repeat lookups never
hit the network. Failures NEVER raise out of a geocoder: an explicit
unresolved result (provider="unresolved", lat/lng None) is returned so
signup capture cannot crash because geocoding failed.

Network is stdlib ``urllib`` only -- no new dependencies.
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from lead_ingest.db_compat import IS_POSTGRES
from lead_ingest.models import utc_now_iso

CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = (
    "BentonDronesLeadIngest/1.0 (contact: leads@bentondrones.com)"
)
NOMINATIM_MIN_INTERVAL = 1.0  # seconds -- Nominatim usage policy: max 1 req/s
DEFAULT_TIMEOUT = 10.0

GEOCODE_CACHE_DDL = """
CREATE TABLE IF NOT EXISTS geocode_cache (
    normalized_address TEXT PRIMARY KEY,
    latitude REAL,
    longitude REAL,
    provider TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    precision TEXT DEFAULT '',
    created_at TEXT NOT NULL
)
"""

_ZIP_RE = re.compile(r"\b(\d{5})(?:-(\d{4}))?\b")
_WS_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class GeocodeResult:
    """Result of a geocode attempt.

    ``latitude``/``longitude`` are ``None`` for unresolved results
    (provider="unresolved", precision="none") -- never fabricated.
    """

    latitude: float | None
    longitude: float | None
    provider: str = "mock"
    display_name: str = "Mock geocode result"
    raw: str = "{}"
    precision: str = ""

    @property
    def resolved(self) -> bool:
        return self.latitude is not None and self.longitude is not None


def normalize_address(address: str) -> str:
    """Normalize an address for cache-key use.

    Lowercase, treat commas/semicolons as plain whitespace, collapse
    runs of whitespace, and normalize ZIP+4 to the 5-digit base so
    near-identical inputs hit the same cache key.
    """
    text = address.lower().replace(",", " ").replace(";", " ")
    text = _WS_RE.sub(" ", text).strip()
    return _ZIP_RE.sub(lambda m: m.group(1), text)


def unresolved_result(address: str, raw: str = "{}") -> GeocodeResult:
    """Explicit unresolved result -- no fabricated coordinates."""
    return GeocodeResult(
        latitude=None,
        longitude=None,
        provider="unresolved",
        display_name="",
        raw=raw,
        precision="none",
    )


class MockGeocoder:
    """Deterministic local geocoder for tests/dev. No external calls. Good puppy."""

    def geocode(self, full_address: str) -> GeocodeResult:
        seed = sum(ord(char) for char in full_address)
        lat = 36.372 + (seed % 1000) / 100000
        lng = -94.208 - (seed % 1000) / 100000
        return GeocodeResult(latitude=lat, longitude=lng, display_name=full_address)


def _http_get_json(url: str, user_agent: str, timeout: float) -> dict | list:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class CensusGeocoder:
    """US Census Bureau oneline-address geocoder (free, keyless)."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    def geocode(self, address: str) -> GeocodeResult:
        params = urllib.parse.urlencode(
            {"address": address, "benchmark": "Public_AR_Current", "format": "json"}
        )
        url = f"{CENSUS_URL}?{params}"
        data = _http_get_json(url, NOMINATIM_USER_AGENT, self.timeout)
        matches = data.get("result", {}).get("addressMatches", []) or []
        if not matches:
            return unresolved_result(address, raw=json.dumps(data))
        match = matches[0]
        coords = match["coordinates"]
        precision = "rooftop" if match.get("tigerLine", {}).get("side") else "interpolated"
        return GeocodeResult(
            latitude=float(coords["y"]),
            longitude=float(coords["x"]),
            provider="census",
            display_name=match.get("matchedAddress", address),
            raw=json.dumps(match),
            precision=precision,
        )


class NominatimGeocoder:
    """OpenStreetMap Nominatim geocoder (free, keyless, polite).

    Every request carries an identifying User-Agent and consecutive
    requests are spaced at least :data:`NOMINATIM_MIN_INTERVAL` seconds
    apart per the Nominatim usage policy.
    """

    _last_call_monotonic = 0.0  # module-level: shared across instances

    def __init__(self, timeout: float = DEFAULT_TIMEOUT, sleep=time.sleep):
        self.timeout = timeout
        self._sleep = sleep

    def _wait_for_politeness(self) -> None:
        elapsed = time.monotonic() - NominatimGeocoder._last_call_monotonic
        remaining = NOMINATIM_MIN_INTERVAL - elapsed
        if remaining > 0:
            self._sleep(remaining)

    def geocode(self, address: str) -> GeocodeResult:
        params = urllib.parse.urlencode({"q": address, "format": "json", "limit": 1})
        url = f"{NOMINATIM_URL}?{params}"
        self._wait_for_politeness()
        try:
            data = _http_get_json(url, NOMINATIM_USER_AGENT, self.timeout)
        finally:
            NominatimGeocoder._last_call_monotonic = time.monotonic()
        if not data:
            return unresolved_result(address)
        hit = data[0]
        return GeocodeResult(
            latitude=float(hit["lat"]),
            longitude=float(hit["lon"]),
            provider="nominatim",
            display_name=hit.get("display_name", address),
            raw=json.dumps(hit),
            precision=hit.get("addresstype", hit.get("class", "")),
        )


class ChainedGeocoder:
    """Try each provider in order; first resolved result wins.

    No-match results fall through to the next provider. Provider ERRORS
    (timeout, network, HTTP failure) abort the chain and yield an
    explicit unresolved result -- we don't hammer the fallback when the
    network is down, and we never raise into the signup path.
    """

    def __init__(self, providers: list | None = None):
        self.providers = (
            providers if providers is not None else [CensusGeocoder(), NominatimGeocoder()]
        )

    def geocode(self, address: str) -> GeocodeResult:
        last_result = unresolved_result(address)
        for provider in self.providers:
            try:
                result = provider.geocode(address)
            except Exception as exc:  # never raise into callers
                return GeocodeResult(
                    latitude=None,
                    longitude=None,
                    provider="unresolved",
                    display_name="",
                    raw=json.dumps({"error": str(exc)}),
                    precision="none",
                )
            if result.resolved:
                return result
            last_result = result
        return last_result


class CachedGeocoder:
    """DB-backed cache around a chained geocoder.

    Cache key is the normalized address. Hits are served with ZERO
    network calls. Misses (including unresolved results) are persisted
    so provider results stay stable across restarts.
    """

    def __init__(self, conn, geocoder=None):
        self.conn = conn
        self.geocoder = geocoder if geocoder is not None else ChainedGeocoder()

    def geocode(self, address: str) -> GeocodeResult:
        key = normalize_address(address)
        cached = self.conn.execute(
            "SELECT latitude, longitude, provider, display_name, precision, created_at AS raw "
            "FROM geocode_cache WHERE normalized_address = ?",
            (key,),
        ).fetchone()
        if cached is not None:
            return GeocodeResult(
                latitude=cached["latitude"],
                longitude=cached["longitude"],
                provider=cached["provider"],
                display_name=cached["display_name"],
                raw=cached["raw"],
                precision=cached["precision"],
            )

        result = self.geocoder.geocode(address)
        try:
            self.conn.execute(
                """
                INSERT INTO geocode_cache
                (normalized_address, latitude, longitude, provider, display_name, precision, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    result.latitude,
                    result.longitude,
                    result.provider,
                    result.display_name,
                    result.precision,
                    utc_now_iso(),
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Concurrent insert won the race; cached next time. Roll back so
            # SQLite doesn't hold a stale transaction open.
            try:
                self.conn.rollback()
            except Exception:
                pass
        return result


def get_default_geocoder(mode: str | None = None):
    """Return the geocoder for the requested mode.

    Default is ``mock`` (offline, test-safe). Set ``GEOCODER_MODE=live``
    for the real Census -> Nominatim chain in production.
    """
    mode = (mode or "mock").strip().lower()
    if mode == "live":
        return ChainedGeocoder()
    return MockGeocoder()
