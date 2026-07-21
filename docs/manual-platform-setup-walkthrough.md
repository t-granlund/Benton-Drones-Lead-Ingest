# Manual Platform Setup Walkthrough

This is the step-by-step browser walkthrough for preparing Benton Drones Lead-Ingest domain/API setup.

## Goal

Prepare the infrastructure needed for:

- Cloudflare authoritative DNS
- Google Workspace email preservation
- Shopify storefront preservation
- `leads.bentondrones.com` backend subdomain
- future CLI/API automation

## Rule

Do not change Namecheap nameservers until Cloudflare DNS has been fully prepared and checked.

## Browser tabs to open

1. Cloudflare dashboard
   - https://dash.cloudflare.com/

2. Namecheap domain list
   - https://ap.www.namecheap.com/domains/list/

3. Google Admin Console
   - https://admin.google.com/

4. Shopify Admin domains
   - https://admin.shopify.com/

5. Local MVP domain setup page
   - http://127.0.0.1:8000/domain-setup

6. Local API/CLI preflight page
   - http://127.0.0.1:8000/api-preflight

## Phase 1: Capture current state

### Namecheap

Capture:

- current nameservers
- all Advanced DNS host records
- A record for `@`
- CNAME for `www`
- any MX records
- any TXT records
- any URL redirects or email forwarding settings

Do not change anything yet.

### Google Workspace

Capture:

- MX records Google expects
- DKIM status and selector/value
- SPF recommendation
- whether DMARC already exists
- current admin email used for Workspace

### Shopify

Capture:

- Shopify store domain, e.g. `something.myshopify.com`
- domain status for `bentondrones.com`
- required A record
- required CNAME record
- SSL status
- primary domain setting

### Cloudflare

Capture:

- whether `bentondrones.com` is already added
- assigned Cloudflare nameservers if added
- imported DNS records if added

## Phase 2: Prepare Cloudflare DNS

Add or verify records for:

```txt
A/CNAME @      Shopify/current root target
CNAME   www    Shopify/current www target
MX      @      Google Workspace
TXT     @      SPF
TXT     google._domainkey DKIM
TXT     _dmarc DMARC monitor policy
CNAME/A leads  backend host target once known
```

Keep `@`, `www`, and `leads` DNS-only initially.

## Phase 3: Only after verification

Change Namecheap nameservers to the Cloudflare-assigned nameservers.

## Phase 4: Post-cutover checks

Verify:

- `https://bentondrones.com`
- `https://www.bentondrones.com`
- Google Workspace inbound/outbound email
- SPF/DKIM/DMARC pass
- `leads.bentondrones.com` once backend exists

## Values to paste back to Code Puppy

Paste these values back when captured:

```txt
Namecheap current nameservers:

Namecheap A @ record:

Namecheap CNAME www record:

Any Namecheap MX records:

Any Namecheap TXT records:

Shopify required A record:

Shopify required CNAME record:

Shopify myshopify domain:

Google Workspace MX records:

Google Workspace DKIM selector/value status:

Existing SPF record:

Existing DMARC record:

Cloudflare assigned nameservers:

Cloudflare imported DNS records:
```
