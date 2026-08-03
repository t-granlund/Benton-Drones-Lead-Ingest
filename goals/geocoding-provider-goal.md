# Goal: Real Geocoding Provider

## Primary goal

Replace placeholder coordinates with real address geocoding so every stored address becomes a reliable latitude/longitude suitable for clustering, exports, and the future map UI.

## Autonomy

FULLY AUTONOMOUS. An agent builds, tests, and wires this end-to-end. No human action, account, or paid API key is required: both providers are free, keyless public services.

## Required capabilities

1. Provider chain: US Census Bureau Geocoder is the primary provider for US street addresses; Nominatim (OpenStreetMap) is the fallback when Census returns no match (non-US addresses, PO boxes, rural routes).
2. Provider abstraction behind a single `geocode(address) -> (lat, lon, provider, precision)` interface so providers can be swapped or extended without touching callers.
3. Response cache persisted in the local database, keyed by normalized address string, so repeat lookups never hit the network and provider results are stable across restarts.
4. Address normalization (case, whitespace, ZIP normalization) before cache lookup to maximize cache hit rate.
5. Respectful usage: Nominatim requests carry an identifying User-Agent and are rate-limited to at most 1 request/second per its usage policy.
6. Failure handling: provider timeout or no-match returns an explicit unresolved status rather than raising into the signup path; signup capture never fails because geocoding did.
7. Signup integration: new signups are geocoded (synchronously or via the queue) and existing un-geocoded records can be backfilled by a script/command.
8. Tests: mocked-provider unit tests for Census, Nominatim, fallback ordering, cache hits/misses, normalization, and failure paths.

## Non-goals

- Paid geocoding providers (Google, Mapbox, SmartyStreets)
- Batch/bulk Census API submission of the full historical dataset
- Rooftop-precision guarantees or manual address correction UI
- Geocoding at form-render time (pre-submit autocomplete)
