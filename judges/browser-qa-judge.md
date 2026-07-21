# Judge: Browser QA

## Pass criteria

PASS if browser QA verifies:

- `/overview`
- `/shopify-preview`
- `/changelog`
- `/roadmap`
- `/domain-setup`
- `/api-preflight`
- `/signup`
- `/signup/default`
- Shopify preview CTA to signup
- valid signup flow
- invalid signup rejection
- admin login flow
- authenticated admin dashboard
- protected exports

## Fail criteria

FAIL if:

- Any key page returns 500.
- CTA links are broken.
- Signup form cannot submit valid data.
- Invalid signup appears successful.
- Admin login is inaccessible.
- Protected exports are public.
