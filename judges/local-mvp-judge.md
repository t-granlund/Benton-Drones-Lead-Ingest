# Judge: Local MVP Acceptance Criteria

Use this judge to evaluate whether the local Benton Drones Shopify-aware lead ingest MVP is ready for end-to-end review.

## Pass criteria

The implementation passes if:

1. The local app starts with:

```bash
python scripts/init_db.py
python -m lead_ingest.server
```

2. The signup route exists:

```txt
GET /signup
GET /signup/<variant>
```

3. A valid signup submission creates:
   - one signup record
   - one linked consent record
   - Shopify context fields when provided

4. Invalid signup data is rejected server-side.

5. Consent is required and versioned.

6. Admin dashboard exists at:

```txt
/admin
```

7. Exports exist at:

```txt
/export/csv
/export/geojson
/export/kml
```

8. Proximity clustering can group geocoded signups by radius.

9. Shopify context can be passed locally using query params such as:

```txt
/signup/default?shop=bentondrones.myshopify.com&logged_in_customer_id=123&page_url=/pages/drone-delivery
```

10. The test suite passes 3 consecutive runs:

```bash
python -m unittest discover -s tests
python -m unittest discover -s tests
python -m unittest discover -s tests
```

## Fail criteria

Fail if:

- lead data is stored without consent
- consent text/version is missing
- exports expose malformed data
- tests are missing for validation/database/export/clustering
- the app requires paid/external services to run locally
- Shopify context is trusted in production without signature/HMAC validation
- the implementation requires storing sensitive lead/consent data in Shopify metafields
