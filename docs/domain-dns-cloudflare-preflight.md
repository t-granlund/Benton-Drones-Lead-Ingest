# Domain, DNS, Cloudflare, Google Workspace Preflight Plan

## Recommended setup

Use this ownership model:

```txt
Registrar:       Namecheap
Authoritative DNS: Cloudflare
Email:           Google Workspace Business
Storefront:      Shopify at bentondrones.com / www
Lead backend:    leads.bentondrones.com
Admin MVP:       leads.bentondrones.com/admin-login
Future staging:  staging.bentondrones.com
```

Do not move DNS to Google/Squarespace Domains unless there is a strong reason. Since the Cloudflare account already exists and Namecheap is already the registrar, the cleanest path is to keep registration at Namecheap and move authoritative DNS to Cloudflare.

## Immediate production URL goal

```txt
https://leads.bentondrones.com/signup/default?source=shopify&campaign=drone-delivery-page
```

The Shopify page should live at something like:

```txt
https://bentondrones.com/pages/drone-delivery-signup
```

That page links to the owned lead backend.

## Subdomain plan

| Subdomain | Purpose | Build now? |
|---|---|---|
| `leads.bentondrones.com` | Public signup, admin login, protected exports | Yes |
| `staging.bentondrones.com` | Test future releases before production | Soon |
| `admin.bentondrones.com` | Separate admin interface | Later |
| `api.bentondrones.com` | Dedicated API if frontend/backend split | Later |
| `assets.bentondrones.com` | Static assets/CDN | Later |

For MVP, keep admin under:

```txt
https://leads.bentondrones.com/admin-login
```

Do not proxy admin/export routes through Shopify.

## Critical preflight before nameserver changes

Before changing anything, capture screenshots/exports of:

1. Current Namecheap nameservers.
2. Current Namecheap DNS records.
3. Current A record.
4. Current CNAME record.
5. Any hidden Namecheap email/MX settings.
6. Any TXT records for Google verification/SPF/DKIM/DMARC.
7. Shopify Admin domain requirements/status.
8. Google Workspace MX/DKIM/SPF status.

Namecheap sometimes separates email records from general host records, so do not assume that only seeing one A record and one CNAME means email records do not exist.

## Likely Shopify records

Verify these in Shopify Admin before copying:

```txt
Type    Name    Value                 Proxy
A       @       23.227.38.65           DNS only initially
CNAME   www     shops.myshopify.com    DNS only initially
```

Do not assume these are correct until Shopify Admin confirms them.

## Google Workspace records to preserve

Google Workspace email usually needs MX records like:

```txt
MX @ 1  ASPMX.L.GOOGLE.COM
MX @ 5  ALT1.ASPMX.L.GOOGLE.COM
MX @ 5  ALT2.ASPMX.L.GOOGLE.COM
MX @ 10 ALT3.ASPMX.L.GOOGLE.COM
MX @ 10 ALT4.ASPMX.L.GOOGLE.COM
```

Some newer setups use:

```txt
MX @ 1 SMTP.GOOGLE.COM
```

Use the exact values shown by Google Admin.

SPF usually:

```txt
TXT @ v=spf1 include:_spf.google.com ~all
```

DKIM must come from Google Admin:

```txt
TXT google._domainkey v=DKIM1; k=rsa; p=...
```

Start DMARC in monitoring mode:

```txt
TXT _dmarc v=DMARC1; p=none; rua=mailto:admin@bentondrones.com; adkim=s; aspf=s
```

Use a monitored mailbox for `rua`.

## Cloudflare setup before cutover

1. Add `bentondrones.com` to Cloudflare.
2. Let Cloudflare scan existing DNS.
3. Compare imported records to Namecheap screenshots.
4. Add any missing Shopify records.
5. Add Google Workspace MX/TXT/DKIM/DMARC records.
6. Add `leads` record once backend hosting target is known.
7. Keep `@`, `www`, and `leads` as DNS only initially.
8. Confirm there is only one SPF record at `@`.
9. Do not change Namecheap nameservers until Cloudflare DNS is complete.

## Initial Cloudflare records template

Values marked `VERIFY` must be confirmed from Shopify, Google, or backend hosting.

```txt
Type    Name                  Value / Target                         Proxy
A       @                     VERIFY_SHOPIFY_OR_CURRENT_IP            DNS only
CNAME   www                   VERIFY_SHOPIFY_TARGET                   DNS only
CNAME   leads                 VERIFY_BACKEND_HOST_TARGET              DNS only

MX      @                     VERIFY_GOOGLE_MX                        n/a
TXT     @                     v=spf1 include:_spf.google.com ~all     n/a
TXT     google._domainkey     VERIFY_FROM_GOOGLE_ADMIN                n/a
TXT     _dmarc                v=DMARC1; p=none; rua=mailto:admin@bentondrones.com; adkim=s; aspf=s
```

If backend hosting provides an IP instead of CNAME:

```txt
A       leads                 BACKEND_IP                              DNS only
```

## Nameserver cutover

In Namecheap:

```txt
Domain List → bentondrones.com → Manage → Nameservers → Custom DNS
```

Enter the two Cloudflare nameservers assigned to the zone.

After saving, monitor:

```txt
bentondrones.com
www.bentondrones.com
leads.bentondrones.com
MX records
TXT records
Google Workspace email
Shopify domain health
```

## Verification commands

Windows:

```powershell
nslookup bentondrones.com
nslookup www.bentondrones.com
nslookup -type=mx bentondrones.com
nslookup -type=txt bentondrones.com
nslookup -type=txt _dmarc.bentondrones.com
nslookup leads.bentondrones.com
```

Mac/Linux:

```bash
dig bentondrones.com
dig www.bentondrones.com
dig bentondrones.com MX
dig bentondrones.com TXT
dig _dmarc.bentondrones.com TXT
dig leads.bentondrones.com
```

## Post-cutover checks

### Shopify

- `https://bentondrones.com` loads.
- `https://www.bentondrones.com` loads/redirects correctly.
- Shopify Admin → Settings → Domains shows healthy/connected.
- SSL is active.
- Checkout still works if relevant.

### Google Workspace

- External email can send to `user@bentondrones.com`.
- `user@bentondrones.com` can send to external Gmail/Outlook.
- Message headers show SPF/DKIM/DMARC pass.

### Lead backend

- `https://leads.bentondrones.com/signup/default` loads.
- Signup submits.
- Admin login works.
- Export routes are protected.
- Shopify CTA query params are captured.

## Rollback

Rollback requires knowing previous Namecheap nameservers and records.

If storefront/email breaks and cannot be corrected quickly:

1. Log into Namecheap.
2. Restore previous nameservers.
3. Wait for propagation.
4. Verify storefront and email.

Do not begin cutover without screenshots of current nameservers and DNS records.

## Brand/design preflight

No Benton Drones logo or Shopify theme assets are currently present in this repo.

Before final styling, capture from Shopify/theme:

- logo files
- favicon
- brand colors
- fonts
- button styles
- heading/body typography
- screenshots of key Shopify pages
- footer/header navigation patterns
- tone of current marketing copy

Use those assets to style:

- hosted signup page
- confirmation page
- admin login page
- Shopify landing page preview
- future production pages
