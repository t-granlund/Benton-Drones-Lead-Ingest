# Goal: Cloudflare Nameserver Cutover

> **Architectural decision:** `research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md` (Step 1)
> **Updated by:** planning-agent-083bcd on 2026-08-17

## Objective

Move authoritative DNS for `bentondrones.com` from Namecheap to Cloudflare after full preflight verification, preserving Shopify storefront and Google Workspace email throughout.

## Autonomy

HUMAN ONLY. Nameserver cutover is a manual, high-risk DNS operation that must be performed by a human with access to Namecheap and Cloudflare dashboards. No agent may automate this step.

## Required outcomes

1. **Full DNS export before cutover** — capture every existing record (A, CNAME, MX, TXT/SPF, DKIM, DMARC, URL redirects) from the current authoritative DNS provider.
2. **Cloudflare zone scan and record verification** — add `bentondrones.com` to Cloudflare, let it scan existing records, compare imported records to the captured snapshots, add any missing Shopify/Google Workspace/leads records.
3. **Verify no `AAAA` records** remain for the Render-bound host (Render is IPv4 only).
4. **Nameserver change** — in Namecheap: Domain List -> `bentondrones.com` -> Manage -> Nameservers -> Custom DNS -> enter the two Cloudflare-assigned nameservers.
5. **Post-cutover verification** — confirm `bentondrones.com`, `www.bentondrones.com`, `leads.bentondrones.com`, MX records, TXT records, Google Workspace email, and Shopify domain health all resolve correctly.
6. **Rollback documented** — previous Namecheap nameservers and DNS records are captured so cutover can be reversed if storefront or email breaks.

## Dependencies

- REQ-NC-001 (Namecheap preflight snapshot) must be captured first.
- REQ-GW-001 (Google Workspace records verified) must be confirmed first.
- REQ-DNS-001 (Cloudflare DNS readiness) must have the zone imported and records verified.
- REQ-SHOP-001 (Shopify records confirmed) must be verified first.

## Non-goals

- Blind cutover without preflight snapshots.
- Changing email provider or MX records.
- Deleting records during cutover.
- Automating the nameserver change.
