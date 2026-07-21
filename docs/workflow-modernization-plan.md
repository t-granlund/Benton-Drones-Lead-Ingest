# Benton Drones Lead Ingest Modernization Plan

## Current workflow

1. Customer signs up through Google Forms.
2. Consent is handled separately through PDFfiller.
3. Signup data lands in Google Sheets.
4. Address data is manually used to build Google Earth projects.
5. Homes are grouped manually based on proximity.

## Target workflow

1. Visitor lands on a Benton Drones signup experience surfaced through the existing Shopify storefront.
2. Landing page copy and tracking can vary by campaign, neighborhood, partner, or experiment using Shopify pages/theme sections plus backend variants.
3. Visitor submits contact, address, and consent data through one owned form.
4. Data is validated server-side and stored in a database.
5. Consent is versioned, timestamped, and stored with audit metadata.
6. Address is geocoded and cached.
7. Internal dashboard shows leads, maps, geocode status, consent status, and clusters.
8. Leads can be exported as CSV, GeoJSON, and KML during migration away from Google Sheets / Google Earth.
9. Internal planning tools use stored data for proximity grouping and reporting.

## Recommended MVP stack

- Storefront integration: existing Shopify infrastructure
- Owned backend: Shopify app proxy / hosted app endpoint
- App: Next.js + TypeScript later, Python stdlib local MVP now
- Styling: Tailwind CSS
- Validation: Zod
- Database ORM: Prisma
- Local database: SQLite
- Production database: PostgreSQL, ideally with PostGIS later
- Maps: Leaflet / React Leaflet with OpenStreetMap tiles
- Geocoding MVP: OpenStreetMap Nominatim with caching and rate limiting
- Deployment options:
  - Fastest: Vercel + Neon/Supabase Postgres
  - Most self-owned: Dockerized app + Postgres on a small VPS with Caddy/Nginx

## MVP features

### Public signup

- `/signup`
- `/signup/[variant]`
- Shopify-friendly links or app proxy paths
- Campaign/source tracking
- Optional Shopify context capture: shop domain, logged-in customer ID, page URL
- Required contact fields
- Required address fields
- Required consent acceptance
- Mobile-friendly layout

### Consent tracking

Store:

- Consent version
- Exact consent text or immutable reference
- Accepted flag
- Timestamp
- IP address, where appropriate
- User agent, where appropriate
- Related signup ID

Important: this is a technical capture pattern, not legal advice. Consent language, privacy policy, e-signature requirements, and retention should be reviewed by qualified counsel before production use.

### Database records

Initial entities:

- Signup
- ConsentRecord
- LandingPageVariant
- Cluster
- ClusterMember

### Geocoding

- Normalize address into a full address string.
- Geocode after signup or via admin retry.
- Store latitude, longitude, provider, status, confidence/display name, and raw response.
- Never repeatedly geocode the same unchanged address.

### Admin dashboard

- Password-protected MVP admin area
- Signup list
- Recent leads
- Campaign/source summary
- Geocode status summary
- Consent status summary
- CSV export
- GeoJSON export
- KML export

### Planning tools

- Map all geocoded signups.
- Color/filter markers by campaign, status, and cluster.
- Generate simple radius-based clusters.
- Allow manual cluster review and export.

## Suggested phased build

### Phase 1: Local foundation

- Scaffold Next.js app.
- Add Prisma + SQLite.
- Define schema.
- Add `.env.example`.
- Add seed data for local development.

### Phase 2: Signup and consent MVP

- Build signup page.
- Add server-side validation.
- Store signup and consent in one transaction.
- Add success/error states.

### Phase 3: Admin MVP

- Add basic admin auth.
- Add lead table and summary cards.
- Add CSV export.

### Phase 4: Geocoding

- Add geocoding abstraction.
- Implement Nominatim provider.
- Add caching/status handling.
- Add admin retry.

### Phase 5: Mapping and exports

- Add Leaflet map.
- Add GeoJSON export.
- Add KML export for Google Earth compatibility.

### Phase 6: Clustering

- Add Haversine distance utility.
- Generate simple proximity clusters by configurable radius.
- Add manual cluster management.

### Phase 7: Shopify integration and production hardening

- Decide between Shopify page link, embedded iframe/theme section, or Shopify app proxy.
- Prefer app proxy for storefront-native URLs once production app setup is ready.
- Validate Shopify proxy signatures/HMAC before trusting Shopify context.
- Keep lead PII, consent records, geocoding, and planning data in the owned backend database.
- Avoid storing sensitive lead/consent payloads in Shopify metafields unless there is a very specific, reviewed reason.

### Phase 8: Production hardening

- Choose deployment target.
- Move production DB to Postgres.
- Add HTTPS-only production setup.
- Add rate limiting and bot protection.
- Add backups.
- Add stronger auth if needed.
- Add Shopify app proxy HMAC validation if using app proxy.

## Low/no-cost tool research priorities

A dedicated `web-puppy` research agent should investigate:

1. Consent/e-signature self-hosted options such as Documenso, OpenSign, Docuseal, Signature Pad, and PDF generation approaches.
2. Geocoding providers including Nominatim, US Census Geocoder, Mapbox, Google Maps, HERE, and geocodio-style providers.
3. Mapping replacements for Google Earth including Leaflet, MapLibre, GeoJSON, KML export, QGIS, uMap, and Kepler.gl.
4. Reporting options including custom admin pages, Metabase, Evidence.dev, Grafana, and Superset.
5. Hosting options including VPS + Docker, Vercel + managed Postgres, Cloudflare, and Supabase/Neon.
6. Shopify integration options: theme section, iframe embed, app proxy, custom app, customer context handling, app proxy HMAC validation, and minimal-permission Shopify app setup.

## Security principles

- Treat names, emails, phone numbers, addresses, signatures, and consent records as sensitive PII.
- Use HTTPS in production.
- Keep admin routes private.
- Validate all input server-side.
- Store secrets in environment variables.
- Minimize third-party sharing of address data.
- Cache geocoding responses to avoid unnecessary repeated external calls.
- Maintain regular database backups.
- Keep export endpoints protected.

## Open questions

1. Confirm Shopify store details: Shopify plan, theme, and whether custom app/app proxy setup is available.
2. Should signup live as a Shopify page link, embedded section/iframe, or Shopify app proxy URL?
3. Do customers need a drawn signature, typed name, checkbox consent, generated PDF, or a third-party e-sign flow?
4. What exact consent language and versioning policy should be used?
5. Are drone simulation participants only in Arkansas, or multiple states?
6. Do you need SMS/email follow-up in the MVP, or later?
7. Should the internal admin be single-user first or multi-user from day one?
8. What export format is most important initially: CSV, KML, or GeoJSON?
