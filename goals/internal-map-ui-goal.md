# Goal: Internal Map UI

## Primary goal

Give the operator an internal, authenticated map view of geocoded leads, proximity clusters, and service zones — replacing the manual Google Earth workflow for day-to-day planning.

## Autonomy

FULLY AUTONOMOUS (post-launch). An agent builds this after launch using the existing geocoded data and admin auth. No human action or paid tile/API account is required; the map uses free OpenStreetMap tiles.

## Required capabilities

1. Authenticated internal map page (admin-only, same protection as existing admin/export routes) rendering geocoded leads as markers on an interactive map.
2. Marker data served from the existing database as GeoJSON (reusing the export pipeline), including lead recency and cluster assignment in marker popups.
3. Cluster visualization: proximity clusters displayed distinctly (color or layer) from unclustered leads, consistent with the existing clustering utility.
4. Service-zone overlay: at least one definable polygon/radius layer representing a service zone, sourced from data (not hardcoded pixels), persisted in the database.
5. Filtering: basic filters on the map view (date range, cluster, campaign/source) without page reload.
6. Free basemap: Leaflet (or equivalent lightweight stdlib-friendly approach) with OpenStreetMap tiles and proper attribution — no paid map API keys.
7. Degrades gracefully: leads without coordinates are listed in an un-geocoded side panel rather than silently dropped.
8. Tests: unit/integration tests for the map data endpoint (auth required, GeoJSON shape, filters, un-geocoded handling) and a browser-level smoke check that the map page renders.

## Non-goals

- Public/customer-facing maps
- Turn-by-turn routing or drone flight-path optimization
- Real-time live location tracking
- Custom tile hosting or offline maps
