# Judge: Shopify App Proxy Future Readiness

## Pass criteria

PASS if:

- App Proxy integration is documented.
- HMAC/signature validation utility exists.
- Tests cover valid signatures.
- Tests cover invalid/tampered signatures.
- Raw Shopify query params are not trusted in production.
- Verified Shopify context can be handed to signup flow safely.
- Production docs state required `SHOPIFY_APP_SECRET`.

## Fail criteria

FAIL if:

- Production App Proxy is marked complete without HMAC/signature validation.
- `logged_in_customer_id` is trusted from unsigned query params.
- Shopify context is stored without validation in production mode.
- Tests do not cover signature validation.
