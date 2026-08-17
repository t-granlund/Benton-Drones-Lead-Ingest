# Goal: Anderson End-to-End Testing Against Live Stack

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Objective

Anderson performs a full end-to-end verification of the lead ingest system against the live Render + Neon production stack, confirming the complete customer journey works from signup through admin dashboard to exports.

## Autonomy

HUMAN ONLY. Anderson must personally execute the test journey to confirm the system is usable and trustworthy. An agent prepares the test checklist and expected outcomes; Anderson performs the clicks and confirms the results.

## Required test journey

1. **Signup** — open the live signup URL (leads.bentondrones.com/signup or the onrender.com URL if the custom domain is not yet live), submit a test lead with consent and typed-name signature using a real Bentonville address.
2. **Confirmation** — confirm the branded confirmation page appears.
3. **Admin login** — open the admin login page, log in, confirm the dashboard loads.
4. **Dashboard** — confirm the test lead appears on the map (correct GPS pin) and in the recent leads table.
5. **Lead detail** — click View, confirm the lead detail page shows all submitted data and the consent/waiver audit trail.
6. **Print/PDF** — open the printable consent form and/or download the PDF.
7. **Exports** — download CSV, GeoJSON, and KML; confirm each contains the test lead; open KML in Google Earth Pro.
8. **Health check** — open `/healthz`, confirm status ok and db ok.
9. **Email (if credentialed)** — submit a signup with a real email and confirm the customer confirmation and internal alert arrive.
10. **JIRA (if credentialed)** — confirm a JIRA ticket is created or queued.

## Pass criteria

- Every step above completes successfully against the live stack.
- No 500 errors or unexpected failures.
- Data persists (the test lead is visible after navigating away and back).
- Exports contain the correct test data.

## Non-goals

- Load testing or performance benchmarking.
- Security penetration testing (covered by production-hardening judge and ADR-001 fitness functions).
- Testing against a staging environment (this is against production).
