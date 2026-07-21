# Shopify Long-Term Integration Recommendation

## Recommendation

Use a phased hybrid strategy:

1. Launch first with a Shopify landing page that links to the owned hosted signup experience.
2. Keep the owned backend as the system of record for leads, consent, addresses, geocoding, clusters, reports, and exports.
3. Prototype Shopify App Proxy after the hosted experience is stable.
4. Move the public signup experience to Shopify App Proxy only after real Shopify request signing, POST behavior, redirects, cookies, and response behavior are verified.
5. Keep the hosted signup URL as a fallback even if App Proxy becomes the primary public route.

## Best immediate path

Create a Shopify page such as:

```txt
https://bentondrones.com/pages/drone-delivery-signup
```

That page explains the program and links to:

```txt
https://leads.bentondrones.com/signup/default
```

or another owned backend URL.

This is the lowest-risk and fastest path to replace Google Forms/PDFfiller/Sheets while preserving data ownership.

## Best long-term public signup path

Once production hosting is stable, use Shopify App Proxy for a storefront-native URL such as:

```txt
https://bentondrones.com/apps/drone-signup
```

The proxy points to the owned backend, but Shopify remains only the storefront/context layer.

## Why not iframe/theme embed as the main strategy?

Iframes or remote embedded theme sections can work as a bridge, but they create long-term friction:

- mobile sizing issues
- styling mismatch
- analytics attribution quirks
- accessibility issues
- Content Security Policy complications
- cookie/session restrictions
- awkward debugging

Use iframe/theme embedding only if a visually embedded short-term demo is needed.

## What must stay owned

Do not use Shopify as the system of record for:

- lead PII
- addresses
- consent records
- signatures
- geocoding results
- clusters
- internal planning reports
- CSV/GeoJSON/KML exports

Shopify should provide storefront presentation and optional verified context only.

## App Proxy verification checklist

Before production App Proxy use, verify current Shopify behavior for:

1. App proxy availability on the current store/plan.
2. Custom app/app proxy configuration access.
3. Exact signature/HMAC validation rules.
4. Whether the parameter is `signature`, `hmac`, or both in the relevant flow.
5. Canonical query string sorting and encoding rules.
6. Repeated query parameter behavior.
7. Whether `logged_in_customer_id` is included and under what conditions.
8. Whether app proxy supports direct POST form submissions reliably.
9. Request body size limits.
10. Redirect behavior.
11. Header limitations.
12. Set-Cookie behavior.
13. Cache behavior.
14. Full HTML response support.
15. Whether proxy content is indexable or if SEO should remain on the Shopify landing page.

## Recommended production architecture

```txt
bentondrones.com Shopify storefront
        |
        | Phase 1: CTA link
        | Phase 2: App Proxy URL
        v
Owned Benton Drones lead ingest backend
        |
        v
Owned database: leads, consent, geocoding, clusters
        |
        v
Internal admin, exports, maps, reports
```

## Admin/export guidance

Do not proxy internal admin/export tools through Shopify.

Keep these under an owned internal route such as:

```txt
https://leads.bentondrones.com/admin
https://leads.bentondrones.com/export/csv
https://leads.bentondrones.com/export/geojson
https://leads.bentondrones.com/export/kml
```

Admin/export routes must remain authenticated and should not be public storefront routes.

## Bottom line

The best long-term destination is Shopify App Proxy for the public signup experience, but the best immediate production move is a Shopify landing page linking to the hosted owned backend.

This gives Benton Drones:

- fastest launch
- lowest operational risk
- clean data ownership
- fewer Shopify dependencies early
- an upgrade path to a polished native `bentondrones.com/apps/...` experience later
