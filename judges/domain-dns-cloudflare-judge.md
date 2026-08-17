# Judge: Domains, DNS, and Cloudflare

> **Updated by:** planning-agent-083bcd on 2026-08-17

## Pass criteria

PASS if:

- Current Namecheap DNS state has been captured.
- Cloudflare zone exists for `bentondrones.com`.
- Cloudflare records match required Shopify records.
- Cloudflare records preserve Google Workspace MX/SPF/DKIM/DMARC.
- `leads.bentondrones.com` target is defined (CNAME to benton-drones-lead-ingest.onrender.com).
- `admin.bentondrones.com` is configured for Cloudflare Pages (auto-provisioned DNS, per ADR-001).
- No `AAAA` records remain for the Render-bound host (Render is IPv4 only).
- No destructive DNS automation has been used.
- Rollback path is documented.

## Fail criteria

FAIL if:

- Nameservers are changed without Namecheap snapshot.
- MX records are missing or changed without verification.
- Shopify records are unverified.
- More than one SPF record exists at root.
- `leads.bentondrones.com` is marked complete without resolving.
- `admin.bentondrones.com` is marked complete without the Pages project existing.
- AAAA records remain for the Render-bound host.
- DNS scripts make unauthorized write changes.

## Evidence

- Cloudflare DNS export or screenshot
- Namecheap snapshot
- DNS command output
- Shopify domain status
- Google Workspace email auth records
- dig/nslookup output for `leads.bentondrones.com` and `admin.bentondrones.com`
