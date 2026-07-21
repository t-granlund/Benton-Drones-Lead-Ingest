# Goal: Domains, DNS, and Cloudflare Readiness

## Objective

Prepare `bentondrones.com`, `www.bentondrones.com`, and `leads.bentondrones.com` for safe production use while preserving Shopify storefront access and Google Workspace email.

## Required outcomes

- Keep Namecheap as registrar unless migration is explicitly approved.
- Use Cloudflare as authoritative DNS after preflight verification.
- Preserve Shopify root and `www` records.
- Preserve Google Workspace MX/SPF/DKIM/DMARC records.
- Add `leads.bentondrones.com` after backend host target is selected.
- Use DNS-only mode initially for root, `www`, and `leads`.
- Avoid destructive DNS automation until rollback state is captured.

## Required records to verify

- Root domain Shopify record
- `www` Shopify record
- Google Workspace MX records
- SPF TXT record
- DKIM TXT record
- DMARC TXT record
- `leads` A/CNAME backend record

## Non-goals

- Blind nameserver cutover
- Automated DNS deletion
- Automated MX replacement
- Production proxying before SSL and app health are verified
