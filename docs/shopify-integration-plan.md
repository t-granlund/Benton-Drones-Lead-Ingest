# Shopify Integration Plan

Benton Drones will be implemented into an existing Shopify infrastructure. The lead ingest system should therefore behave like an owned backend that can be surfaced inside Shopify without forcing sensitive planning data into Shopify itself.

## Recommended architecture

```text
Shopify storefront page / theme section / app proxy
        |
        v
Benton Drones lead ingest backend
        |
        v
Owned database: signups, consent, geocodes, clusters
        |
        v
Internal admin, exports, maps, planning tools
```

## Standalone landing page

The project includes a standalone branded landing page at `static/landing-page.html`. It can be served at `/landing-page.html` by the lead ingest backend, or hosted independently as a static file.

To surface it inside a Shopify page:

- **CTA link**: Add a link in a Shopify page or theme section pointing to `https://leads.bentondrones.com/landing-page.html` (or directly to `/signup`).
- **iframe embed**: Add an iframe in a Shopify page pointing to the landing page URL. Be mindful of iframe styling and tracking.

```html
<!-- CTA link approach -->
<a href="https://leads.bentondrones.com/signup">Sign up for updates</a>

<!-- iframe approach -->
<iframe src="https://leads.bentondrones.com/landing-page.html" style="width:100%;border:0;min-height:600px"></iframe>
```

The landing page is a single flat HTML file — no build step, no dependencies.

## Integration options

### Option 1: Shopify page links to hosted signup app

Use a Shopify page or theme section with a CTA linking to:

```txt
https://leads.bentondrones.com/signup/<variant>
```

Pros:
- simplest
- clean separation
- fastest to launch

Cons:
- user leaves the Shopify-rendered page

### Option 2: Shopify page embeds signup app

Use an iframe or embedded section pointing to the owned signup app.

Pros:
- feels integrated inside the store
- backend remains owned

Cons:
- iframe styling/tracking quirks
- consent/security headers need care

### Option 3: Shopify app proxy

Use Shopify app proxy so storefront URLs can map to the owned backend, e.g.

```txt
https://bentondrones.com/apps/drone-signup
```

Pros:
- best storefront-native URL pattern
- can receive Shopify context like shop and logged-in customer ID

Cons:
- requires Shopify app setup
- requests must validate Shopify signatures/HMAC in production

## Local MVP behavior

The local MVP supports Shopify context fields:

- `shopify_shop_domain`
- `shopify_customer_id`
- `shopify_page_url`

For local testing, these can be passed as query params:

```txt
http://127.0.0.1:8000/signup/default?shop=bentondrones.myshopify.com&logged_in_customer_id=123&page_url=/pages/drone-delivery
```

The public form stores these values with the signup record.

## Production security requirements

Before production Shopify app proxy use:

1. Validate Shopify app proxy signatures/HMAC using `lead_ingest.shopify_security`.
2. Set `SHOPIFY_APP_SECRET` in the production environment.
3. Do not trust raw `logged_in_customer_id` without verification.
3. Keep consent and lead PII in the owned database, not theme metafields.
4. Use HTTPS only.
5. Protect admin/export routes.
6. Add rate limiting and bot protection.
7. Keep Shopify permissions minimal.

## App proxy validation behavior

The local backend includes a Shopify security utility that:

- builds a canonical query string excluding `hmac` and `signature`
- calculates an HMAC-SHA256 digest using the app secret
- compares signatures using constant-time comparison
- signs verified Shopify context into a short-lived form handoff token pattern

Local unsigned demo URLs still work when `SHOPIFY_APP_SECRET` is not set. In production, set:

```bash
SHOPIFY_APP_SECRET=your-shopify-app-secret
```

When that secret exists, Shopify context query params must include a valid `hmac` or `signature` before the backend will carry Shopify context into the form POST.

Important: verify the canonicalization rules against current Shopify app proxy documentation before launch. Shopify is the raccoon king of tiny integration details.

## Data ownership principle

Shopify should provide storefront presentation and optional customer context. The owned lead ingest backend should remain the system of record for:

- lead data
- addresses
- consent records
- geocoding
- planning clusters
- operational reports
