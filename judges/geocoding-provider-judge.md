# Judge: Real Geocoding Provider

## Pass criteria

PASS if, with evidence attached in `tracking/evidence.csv`:

1. A single geocode interface exists and returns `(lat, lon, provider, precision)` or an explicit unresolved result.
2. A known-good US street address resolves via US Census as provider; a Census-unmatchable address resolves via Nominatim fallback — both demonstrated by test or script output captured as evidence.
3. Repeating a lookup for an already-geocoded address produces zero outbound HTTP calls (cache hit proven by mocked-provider test counting calls).
4. Nominatim requests carry an identifying User-Agent and the fallback path is rate-limited to <= 1 request/second.
5. A simulated provider timeout/no-match leaves signup capture working and records an unresolved status (no exception reaches the signup path).
6. A backfill path exists and geocodes previously un-geocoded stored records.
7. The full test suite passes including the new geocoder tests, 1 run minimum at this gate (3 consecutive runs only required if this gate is used as pre-handoff evidence).

## Fail criteria

FAIL if:

- Signup can crash or reject because a geocoding provider is down
- Cache is in-memory only (lost on restart) or keyed on un-normalized addresses
- Nominatim is hit without User-Agent or faster than its usage policy
- Any paid/keyed provider is required for the feature to work
- Coordinates are fabricated when providers fail instead of an explicit unresolved status

## Blocked criteria

BLOCKED only if both free providers are unreachable from the dev environment for reasons outside the agent's control (network egress blocked); document the egress failure as evidence. Missing credentials is NOT a blocker — none are required.
