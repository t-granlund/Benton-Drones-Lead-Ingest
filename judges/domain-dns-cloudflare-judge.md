# Judge: Domains, DNS, and Cloudflare

## Pass criteria

PASS if:

- Current Namecheap DNS state has been captured.
- Cloudflare zone exists for `bentondrones.com`.
- Cloudflare records match required Shopify records.
- Cloudflare records preserve Google Workspace MX/SPF/DKIM/DMARC.
- `leads.bentondrones.com` target is defined or explicitly pending backend host selection.
- No destructive DNS automation has been used.
- Rollback path is documented.

## Fail criteria

FAIL if:

- Nameservers are changed without Namecheap snapshot.
- MX records are missing or changed without verification.
- Shopify records are unverified.
- More than one SPF record exists at root.
- `leads.bentondrones.com` is marked complete without resolving.
- DNS scripts make unauthorized write changes.

## Evidence

- Cloudflare DNS export or screenshot
- Namecheap snapshot
- DNS command output
- Shopify domain status
- Google Workspace email auth records
