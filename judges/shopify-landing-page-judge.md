# Judge: Shopify Landing Page

## Pass criteria

PASS if:

- Shopify landing page exists or draft is ready.
- Page includes clear Benton Drones CTA.
- CTA links to `https://leads.bentondrones.com/signup/default` or local equivalent during development.
- Optional source/campaign params are included.
- Page communicates trust, purpose, and next steps.
- Lead PII and consent are not stored in Shopify by default.
- User can navigate from Shopify page to signup.

## Fail criteria

FAIL if:

- CTA points to wrong domain.
- CTA relies on Google Forms/PDFfiller workflow.
- Sensitive lead/consent data is stored in Shopify metafields without explicit decision.
- Shopify is treated as system of record.
