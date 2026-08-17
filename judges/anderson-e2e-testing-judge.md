# Judge: Anderson End-to-End Testing Against Live Stack

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Pass criteria

PASS if Anderson personally completes and confirms:

1. A test signup submitted at the live URL with consent and typed-name signature succeeds (branded confirmation page).
2. The test lead appears on the admin dashboard map with a correct GPS pin.
3. The test lead appears in the recent leads table with all submitted data.
4. The lead detail page shows the full consent/waiver audit trail.
5. The printable consent form and/or PDF downloads correctly.
6. CSV, GeoJSON, and KML exports each contain the test lead.
7. KML opens in Google Earth Pro with the correct pin location.
8. `/healthz` returns status ok and db ok.
9. (If email credentialed) Customer confirmation and internal alert emails arrive.
10. No 500 errors or unexpected failures during the journey.
11. Data persists after navigating away and back.

## Fail criteria

FAIL if:

- Signup fails or returns a server error.
- The test lead does not appear on the dashboard or in exports.
- Exports are empty or contain incorrect data.
- The health check fails.
- Any step in the journey produces an unexpected error.
- Data does not persist.

## Blocked criteria

BLOCKED if the custom domain `leads.bentondrones.com` is not yet live (Anderson can test against the onrender.com URL in the meantime). BLOCKED on email steps if SMTP credentials are not yet set.

## Evidence

- Anderson's confirmation (screenshots or written sign-off)
- Test lead ID and timestamp
- Export file samples (CSV/GeoJSON/KML) with test data visible
- Health check response
