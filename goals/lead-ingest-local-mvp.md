# Goals: Benton Drones Local Lead Ingest MVP

## Primary goal

Build a local-first, Shopify-aware, self-owned lead ingest system that replaces the current Google Forms + PDFfiller + Google Sheets + manual Google Earth workflow while fitting into the existing Shopify storefront infrastructure.

## Required capabilities

1. Public signup form collects:
   - first name
   - last name
   - email
   - phone
   - street address
   - city
   - state
   - ZIP/postal code
   - optional notes
   - campaign/source/variant metadata
   - optional Shopify context metadata

2. Consent capture stores:
   - consent accepted flag
   - consent version
   - exact consent text
   - timestamp
   - IP address if available
   - user agent if available

3. Data storage:
   - local SQLite database
   - signup records
   - consent records
   - landing page variants
   - cluster records
   - Shopify context fields when provided by storefront/app proxy

4. Admin/reporting:
   - admin dashboard
   - lead count
   - recent leads
   - export links

5. Planning/export:
   - CSV export
   - GeoJSON export
   - KML export
   - proximity clustering utility

6. Shopify compatibility:
   - local signup URLs can receive Shopify-style context query params
   - Shopify context is stored with the signup
   - PII and consent remain in the owned database rather than relying on Shopify metafields

7. Testing:
   - validation tests
   - database tests
   - export tests
   - clustering tests
   - full test suite must pass 3 consecutive times before handoff

## Non-goals for this local MVP

- Full Shopify app installation/configuration
- Production authentication
- Real e-signature provider integration
- Paid geocoding provider integration
- Complex drone routing optimization
- Multi-user role management
- Replacing legal review for consent language
