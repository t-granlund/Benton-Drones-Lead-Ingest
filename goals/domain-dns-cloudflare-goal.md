# Goal: Domains, DNS, and Cloudflare Readiness

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Objective

Prepare `bentondrones.com`, `www.bentondrones.com`, `leads.bentondrones.com`, and `admin.bentondrones.com` for safe production use while preserving Shopify storefront access and Google Workspace email.

## Required outcomes

- Keep Namecheap as registrar unless migration is explicitly approved.
- Use Cloudflare as authoritative DNS after preflight verification (see `goals/cloudflare-nameserver-cutover-goal.md`).
- Preserve Shopify root and `www` records.
- Preserve Google Workspace MX/SPF/DKIM/DMARC records.
- Add `leads.bentondrones.com` after backend host target is selected (CNAME to Render).
- Add `admin.bentondrones.com` for the Cloudflare Pages admin UI (auto-provisioned DNS, per ADR-001).
- Use DNS-only mode initially for root, `www`, and `leads`.
- Avoid destructive DNS automation until rollback state is captured.
- Verify no `AAAA` records remain for the Render-bound host (Render is IPv4 only).

## Required records to verify

- Root domain Shopify record
- `www` Shopify record
- Google Workspace MX records
- SPF TXT record
- DKIM TXT record
- DMARC TXT record
- `leads` A/CNAME backend record (CNAME to benton-drones-lead-ingest.onrender.com)
- `admin` CNAME for Cloudflare Pages (auto-provisioned within the same Cloudflare account)

## Architectural context

Per `research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md` (Option B):
- `admin.bentondrones.com` hosts the static admin UI on Cloudflare Pages (gated by Cloudflare Access).
- `leads.bentondrones.com` is the Render API backend (CNAME, orange-cloud proxied).
- The `onrender.com` subdomain is disabled after the custom domain is verified.
- SSL/TLS mode is Full (strict).

## Non-goals

- Blind nameserver cutover
- Automated DNS deletion
- Automated MX replacement
- Production proxying before SSL and app health are verified
