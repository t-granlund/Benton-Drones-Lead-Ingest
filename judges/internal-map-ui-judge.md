# Judge: Internal Map UI

## Pass criteria

PASS if, with evidence attached in `tracking/evidence.csv`:

1. The map page requires admin auth; an unauthenticated request is rejected (test evidence).
2. The marker data endpoint returns valid GeoJSON built from the database, including cluster assignment and lead recency fields.
3. Clusters render visually distinct from unclustered leads; service-zone overlay renders from database-persisted zone data, not hardcoded coordinates.
4. Date/cluster/campaign filters change the returned marker set without a full page reload (test on the filtered endpoint).
5. Leads without coordinates appear in an un-geocoded panel count/list and are not silently omitted (test with a coordinate-less record).
6. The basemap uses free OSM tiles with attribution; no paid map API key exists anywhere in config.
7. A browser-level smoke check shows the map page rendering markers (screenshot attached as evidence).
8. Test suite passes including data-endpoint, auth, filter, and un-geocoded tests.

## Fail criteria

FAIL if:

- The map or its data endpoint is reachable without admin auth
- Marker data is hardcoded fixtures rather than database-derived
- A paid map provider key is required
- Un-geocoded leads are silently dropped with no visibility

## Blocked criteria

BLOCKED until REQ-GEO-001 passes (real coordinates are the input) and production launch has occurred (post-launch requirement per PRD). Dev-environment geocoded seed data may satisfy criteria 2-5 earlier, but final PASS requires real data.
