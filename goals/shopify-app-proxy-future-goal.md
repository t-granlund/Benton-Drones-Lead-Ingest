# Goal: Future Shopify App Proxy Integration

## Objective

Prepare for a future Shopify-native App Proxy path while keeping the owned backend as system of record.

## Required outcomes

- Support Shopify App Proxy URLs later.
- Validate Shopify HMAC/signature before trusting Shopify context.
- Never trust raw query params in production.
- Store only verified Shopify context with lead records.
- Keep PII and consent in owned backend.
- Document expected Shopify params and validation flow.

## Required verified context examples

- `shop`
- `logged_in_customer_id`
- `timestamp`
- `path_prefix`
- `signature` or `hmac`

## Non-goals

- Declaring production Shopify integration complete without signature tests
- Requiring Shopify App Proxy for first launch
