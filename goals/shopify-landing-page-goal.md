# Goal: Shopify Landing Page Integration

## Objective

Use Shopify as storefront and presentation layer while routing lead capture to the owned backend.

## Required outcomes

- Create or identify a Shopify landing page for drone delivery/signup interest.
- Add clear CTA to the backend signup URL.
- Use production target:

```txt
https://leads.bentondrones.com/signup/default
```

- Include campaign/source params when useful.
- Do not store sensitive lead/consent data in Shopify metafields by default.
- Make the Shopify-to-backend transition feel trustworthy and branded.

## Recommended CTA URL

```txt
https://leads.bentondrones.com/signup/default?source=shopify&campaign=drone-delivery-page
```

## Non-goals

- Full Shopify app installation for first launch
- Shopify as lead database
- Consent records stored in Shopify
