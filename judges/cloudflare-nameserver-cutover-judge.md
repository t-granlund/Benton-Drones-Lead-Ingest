# Judge: Cloudflare Nameserver Cutover

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Pass criteria

PASS if:

- Namecheap current nameservers and DNS records were captured before cutover (SNAP-NC-001, SNAP-NC-002).
- Cloudflare zone for `bentondrones.com` was added and records imported/verified.
- Cloudflare records match required Shopify records (A/CNAME for @ and www).
- Cloudflare records preserve Google Workspace MX/SPF/DKIM/DMARC.
- No `AAAA` records remain for the Render-bound host.
- Namecheap nameservers changed to the two Cloudflare-assigned nameservers.
- Post-cutover: `bentondrones.com` and `www.bentondrones.com` resolve correctly (Shopify loads).
- Post-cutover: Google Workspace inbound and outbound email work (SPF/DKIM/DMARC pass).
- Post-cutover: `leads.bentondrones.com` resolves (once CNAME is added).
- Rollback path is documented (previous Namecheap nameservers recorded).

## Fail criteria

FAIL if:

- Nameservers changed without capturing the pre-cutover state.
- Shopify storefront or Google Workspace email breaks after cutover.
- MX/SPF/DKIM/DMARC records are missing or incorrect.
- More than one SPF record exists at root.
- AAAA records remain for the Render-bound host (Render is IPv4 only).
- No rollback path is documented.

## Evidence

- Namecheap pre-cutover screenshots (nameservers + DNS records)
- Cloudflare zone DNS export
- Post-cutover dig/nslookup output for all hostnames and record types
- Google Workspace email send/receive test with SPF/DKIM/DMARC header verification
- Shopify Admin domain health check
