# API / CLI Automation Preflight Checklist

## Purpose

This checklist defines what Benton Drones needs before we automate backend/domain/platform setup from the command line or APIs.

The goal is to avoid click-click-pray operations and move toward repeatable, auditable setup for:

- Cloudflare DNS
- Namecheap registrar data
- Google Workspace email/domain authentication
- Shopify storefront/domain/app configuration
- production backend hosting
- deployment secrets
- DNS and email verification

## Core principle

Automate what is safe and repeatable. Manually verify anything that can break storefront, email, billing, legal consent, or domain ownership.

Do not automate destructive DNS or nameserver changes until records have been exported, reviewed, and backed up.

## Recommended automation priority

| Platform | Automate now? | Why |
|---|---:|---|
| Cloudflare DNS | Yes, after manual export/review | Best API support for DNS records and zone checks |
| Backend deployment host | Yes, after host is chosen | Needed for repeatable production deploys |
| Google Workspace DNS verification | Partially | CLI can verify DNS; Admin changes require careful scopes |
| Shopify | Partially | CLI/API useful for theme/app work; domain changes should be verified manually |
| Namecheap | Mostly read-only initially | Registrar/nameserver changes are high risk |

## Required local tools

Install only when needed. Keep credentials out of git.

### General

```bash
python --version
curl --version
git --version
```

Optional but useful:

```bash
jq --version
```

Windows alternatives:

```powershell
Resolve-DnsName bentondrones.com
Invoke-RestMethod
```

### Cloudflare

Options:

1. Use Cloudflare API with `curl` / Python.
2. Use Terraform with Cloudflare provider later.
3. Use Wrangler only if Cloudflare Workers/Pages become part of hosting.

Recommended first automation path:

```txt
Python or curl scripts that read Cloudflare zone/DNS records and verify expected values.
```

### Shopify

Potential tools:

```bash
shopify version
```

Shopify CLI is useful for theme/app work, but not required for the first hosted-link MVP.

Use Shopify Admin UI manually for first domain/page setup unless/until we decide to manage theme/app code through CLI.

### Google Workspace

Options:

- Google Admin Console for manual setup
- Google Admin SDK for automation
- GAMADV-XTD3 for admin CLI automation
- `gcloud` for Google Cloud/IAM, not all Workspace admin tasks

Recommended first step:

```txt
Manually verify MX/SPF/DKIM/DMARC in Google Admin, then automate DNS verification from CLI.
```

### Namecheap

Namecheap has an API, but registrar/nameserver changes should not be automated first.

Recommended first step:

```txt
Manually export/screenshot current DNS and nameservers.
Only automate read/check operations until Cloudflare migration is proven.
```

## Secrets needed

Create a local `.env` or password manager entries. Do not commit real values.

```bash
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_ZONE_ID=
SHOPIFY_STORE_DOMAIN=
SHOPIFY_ADMIN_ACCESS_TOKEN=
SHOPIFY_APP_SECRET=
GOOGLE_WORKSPACE_ADMIN_EMAIL=
GOOGLE_WORKSPACE_CUSTOMER_ID=
NAMECHEAP_API_USER=
NAMECHEAP_API_KEY=
NAMECHEAP_USERNAME=
NAMECHEAP_CLIENT_IP=
BACKEND_HOST_API_TOKEN=
ADMIN_PASSWORD=
ADMIN_SESSION_SECRET=
CSRF_SECRET=
```

Only create tokens that are needed for the next step.

## Cloudflare API preflight

### Token permissions

Create a Cloudflare API token with least privilege.

For DNS automation:

```txt
Zone → DNS → Read
Zone → Zone → Read
```

Only add write later:

```txt
Zone → DNS → Edit
```

Scope token to:

```txt
bentondrones.com only
```

### Read-only checks first

Before editing DNS, automation should verify:

- zone exists
- zone status
- current nameservers assigned by Cloudflare
- all DNS records in Cloudflare
- whether `@`, `www`, MX, SPF, DKIM, DMARC exist
- whether `leads` exists

Example API checks:

```bash
curl -s \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=bentondrones.com"
```

```bash
curl -s \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/dns_records"
```

### Cloudflare automation guardrails

Do not automate nameserver cutover from Namecheap until:

- Cloudflare DNS records match expected values
- Google Workspace MX/TXT records are present
- Shopify A/CNAME records are present
- rollback records are documented

For first write automation, prefer adding only:

```txt
leads.bentondrones.com
```

Do not modify `@`, `www`, MX, SPF, DKIM, or DMARC until reviewed.

## Namecheap API preflight

Namecheap API can manage domain DNS/nameservers, but use cautiously.

Required items:

```txt
API access enabled in Namecheap
API key
API username
whitelisted client IP
domain: bentondrones.com
```

Namecheap requires the calling client IP to be whitelisted. If your IP changes often, this is annoying. Congratulations, API security found a way to be both useful and irritating.

Recommended first use:

- read current hosts
- read current nameservers
- export results to file

Avoid automating nameserver changes until the Cloudflare zone is fully verified.

## Google Workspace preflight

### Manual first

In Google Admin Console, verify:

- MX records
- SPF record
- DKIM selector and TXT value
- DKIM enabled status
- DMARC policy
- admin mailbox for DMARC reports

### CLI/API automation candidates

Automate DNS verification rather than Workspace changes first:

```bash
nslookup -type=mx bentondrones.com
nslookup -type=txt bentondrones.com
nslookup -type=txt google._domainkey.bentondrones.com
nslookup -type=txt _dmarc.bentondrones.com
```

Later, if needed, use Admin SDK/GAM for:

- user/group audits
- domain verification status
- Gmail settings inventory

Be conservative with Workspace write scopes.

## Shopify preflight

### Current easiest path

No Shopify API is required for the first production MVP if we launch with:

```txt
Shopify page → CTA link → https://leads.bentondrones.com/signup/default
```

Do these manually first:

- create Shopify page
- add CTA link
- verify domain settings
- capture design system assets

### Shopify CLI/API useful later

Use Shopify CLI/API if we need to:

- manage theme code
- add a custom section/snippet
- build a Shopify app
- configure App Proxy
- validate app proxy requests
- pull theme assets for styling

Potential env vars:

```bash
SHOPIFY_STORE_DOMAIN=bentondrones.myshopify.com
SHOPIFY_ADMIN_ACCESS_TOKEN=
SHOPIFY_APP_SECRET=
```

### Shopify App Proxy caution

Do not claim App Proxy is production-ready until:

- app proxy is configured in Shopify
- real signed Shopify requests are captured
- HMAC/signature canonicalization is verified
- POST behavior is tested
- redirects/cookies/headers are tested

## Backend hosting preflight

We still need to choose production hosting.

Whatever host is selected must provide:

- HTTPS for `leads.bentondrones.com`
- persistent environment variables
- logs
- backups or persistent storage
- Python runtime or container support
- background-safe process management
- database option or external Postgres support

Required production env vars:

```bash
ADMIN_PASSWORD=
ADMIN_SESSION_SECRET=
CSRF_SECRET=
SHOPIFY_APP_SECRET=
DATABASE_URL=
GEOCODER_PROVIDER=
GEOCODER_API_KEY=
```

For the current MVP, SQLite is fine locally. For production, prefer Postgres once leads become operationally important.

## DNS verification scripts we should build next

Recommended next automation scripts:

```txt
scripts/check_dns.py
scripts/check_cloudflare_zone.py
scripts/export_namecheap_dns.py
scripts/check_email_auth.py
scripts/preflight_report.py
```

### `scripts/check_dns.py`

Should verify:

- `bentondrones.com` resolves
- `www.bentondrones.com` resolves
- MX records exist
- SPF TXT exists
- DMARC TXT exists
- `leads.bentondrones.com` resolves after backend DNS exists

### `scripts/check_cloudflare_zone.py`

Should verify:

- Cloudflare token works
- zone exists
- zone ID matches env
- expected records exist
- proxy status is expected

### `scripts/check_email_auth.py`

Should verify:

- MX records
- SPF record
- DKIM record if selector is known
- DMARC record

### `scripts/preflight_report.py`

Should produce a readable local report with pass/fail/warn statuses.

## Manual vs automated checklist

### Manual before automation

- Namecheap screenshots
- Google Workspace admin verification
- Shopify domain verification
- Shopify design asset capture
- Cloudflare account access confirmation
- backend hosting provider decision

### Safe to automate first

- DNS lookups
- Cloudflare read-only zone inventory
- email auth DNS checks
- local preflight report generation
- backend environment variable validation

### Automate later with caution

- creating `leads` DNS record
- updating Cloudflare proxy status
- deploying backend
- creating staging DNS

### Do not automate yet

- Namecheap nameserver cutover
- deleting DNS records
- changing MX records
- changing SPF/DKIM/DMARC
- Shopify app proxy production switch

## Definition of ready for backend CLI/API implementation

We are ready to build automation scripts when we have:

1. Cloudflare API token with read-only DNS access.
2. Cloudflare zone ID for `bentondrones.com`.
3. Current Namecheap DNS/nameserver screenshots.
4. Google Workspace MX/SPF/DKIM/DMARC confirmed.
5. Shopify expected A/CNAME records confirmed.
6. Backend hosting provider selected.
7. Production target for `leads.bentondrones.com` known.
8. Secret storage approach chosen.

## Recommended next build task

Build read-only preflight scripts first:

```txt
scripts/check_dns.py
scripts/preflight_report.py
```

These should not require Cloudflare/Namecheap write access and should safely report current readiness.

After that, add Cloudflare read-only API inventory.

Only after the reports are trusted should we add write operations for DNS records.
