# Benton Drones Lead-Ingest Goals

This directory defines implementation goals for the Benton Drones Lead-Ingest system.

The project replaces the current Google Forms + PDFfiller + Google Sheets + manual Google Earth workflow with a Shopify-aware, self-owned lead ingest backend.

## System ownership model

- **Shopify**: storefront, landing page, CTA, optional verified customer context later
- **Owned backend**: lead PII, consent, geocoding, clustering, reports, exports, admin
- **Cloudflare**: authoritative DNS and future DNS/API automation
- **Namecheap**: registrar and current-state rollback source
- **Google Workspace**: Benton Drones email
- **`leads.bentondrones.com`**: production backend hostname

## Goal files

| Goal | File |
|---|---|
| Local MVP | `lead-ingest-local-mvp.md` |
| Domains/DNS/Cloudflare | `domain-dns-cloudflare-goal.md` |
| Namecheap preflight | `namecheap-preflight-goal.md` |
| Google Workspace email auth | `google-workspace-email-auth-goal.md` |
| Shopify landing page | `shopify-landing-page-goal.md` |
| Future Shopify App Proxy | `shopify-app-proxy-future-goal.md` |
| Backend deployment | `backend-deployment-goal.md` |
| Design system capture | `design-system-capture-goal.md` |
| Production hardening | `production-hardening-goal.md` |
| Browser QA | `browser-qa-goal.md` |
| Read-only preflight scripts | `readonly-preflight-scripts-goal.md` |
| BDS/Dolt-style tracking | `bds-dolt-tracking-goal.md` |

## Definition of done

The project is not production-ready until each relevant judge passes or is explicitly marked deferred with a reason.

No DNS, email, or production routing change is considered complete without evidence in `tracking/evidence.csv` or a referenced doc artifact.
