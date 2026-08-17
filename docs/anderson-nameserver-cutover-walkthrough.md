# Anderson's Nameserver Cutover Walkthrough — Namecheap → Cloudflare

> **Companion:** `docs/anderson-launch-briefing.html` (what's live) · `docs/domain-dns-cloudflare-preflight.md` (technical reference) · `docs/manual-platform-setup-walkthrough.md` (platform screenshots checklist)
> **Status:** READY — follow this when you're ready to move DNS. **Do not do step 4 yet** (nameserver change) until preflight capture is done.

## What you're doing and why

Right now `bentondrones.com` DNS is managed at **Namecheap**. We're moving DNS *management* to **Cloudflare** (free) so that later we can:

- Put the admin dashboard on **Cloudflare Pages** (fast, free, instant load)
- Gate it behind **Cloudflare Access** (Google login — no shared password)
- Control DNS/checks from anywhere, with API automation for future
- Get free DDoS protection + CDN

**Namecheap stays** as the company you pay for the domain registration. **Cloudflare becomes** where DNS records live. Email (Google Workspace) **does not change** — the records just copy from Namecheap to Cloudflare.

## The golden rule

**Email can only break if MX/SPF/DKIM/DMARC records are wrong.** Before touching anything in step 4, we capture the current records (step 1–3) and recreate them exactly in Cloudflare. Then when the cutover happens, email keeps flowing.

---

## BEFORE the cutover (steps 1–3): Capture current state

> These steps require logins. Do them in one sitting (~30–45 min). Take screenshots of everything.

### Step 1: Capture Namecheap DNS (~10 min)

1. Log into [namecheap.com](https://namecheap.com) → **Account** → **Domain List**
2. Click **Manage** next to `bentondrones.com`
3. Go to **Advanced DNS** tab
4. Take a **screenshot of the whole page** (all host records visible)
5. Note specifically:
   - **Nameservers** (top, or under a "Nameservers" section) — are they Namecheap BasicDNS or something else?
   - **A record** for `@` (probably points to Shopify `23.227.38.65`)
   - **CNAME record** for `www` (probably `shops.myshopify.com`)
   - **All MX records** (there will be several for Google Workspace — record every one exactly)
   - **All TXT records** (there will be SPF and probably DKIM — copy the long text values exactly)
   - **Any `_dmarc` TXT record** (if it doesn't exist, we'll add it correctly in Cloudflare)
6. Save screenshots somewhere safe (iCloud Drive, Dropbox, etc.) — these are the "undo" instructions.

### Step 2: Capture Google Workspace email config (~5 min)

1. Log into [admin.google.com](https://admin.google.com) (use the Google admin account for bentondrones.com)
2. Navigate to **Apps** → **Google Workspace** → **Gmail** → **Authenticate email**
3. Note what it says is configured:
   - **SPF**: usually "Enabled" — record the value shown if visible (typically `v=spf1 include:_spf.google.com ~all`)
   - **DKIM**: record the **selector** (usually `google`) and whether it says "Authenticating email"
   - **DMARC**: note if it says "Not set" (expected) — we'll add this in Cloudflare in monitoring mode
4. You should not need to *change* anything here — just capture what Google expects.

### Step 3: Capture Shopify domain config (~5 min)

1. Log into [shopify.com/admin](https://shopify.com/admin) → **Settings** → **Domains**
2. Click `bentondrones.com` — note:
   - **Status** (should say "Connected" or similar)
   - **Primary domain** (should be `bentondrones.com` or `www.bentondrones.com`)
   - **SSL status** (should show active/pending)
3. Tap **DNS settings** or "Verify DNS" — note the exact **A record** and **CNAME record** that Shopify shows as required.

**You now have everything needed to recreate DNS perfectly in Cloudflare. Stop here if not continuing today.**

---

## THE CUTEOVER (step 4): Add Cloudflare + verify

> Only proceed if: (a) you have the screenshots from steps 1–3, (b) you have ~30 min uninterrupted, (c) it's a time when a brief email blip won't kill a deal (low likelihood, but possible during propagation).

### Step 4: Set up Cloudflare zone (~20 min)

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com/) — create free account if not exists
2. Click **Add a domain** → enter `bentondrones.com` → click through the setup
3. **Choose the Free plan** ($0) — you don't need Pro for any of this
4. Cloudflare will **scan** existing DNS. Wait for it to finish, then click through to **Review DNS records**
5. **Critical:** Compare what Cloudflare found against your Namecheap screenshots:
   -  **A record for `@`**: should match Namecheap exactly. **Change proxy setting to "DNS only" (gray cloud)** by clicking the orange cloud.
   -  **CNAME for `www`**: should match exactly. **Change to "DNS only" (gray cloud)**.
   -  **MX records**: every MX from Namecheap should be listed. Add any that are missing.
   -  **TXT records**: SPF, DKIM, and any other TXT from Namecheap should be listed. Add missing ones.
   -  **DMARC**: if not present, **add new TXT record**: Name `_dmarc`, Value `v=DMARC1; p=none; rua=mailto:admin@bentondrones.com; adkim=s; aspf=s`
6. When records match Namecheap exactly (plus DMARC if missing), click **Continue**
7. Cloudflare shows you **two nameservers** (something like `greg.ns.cloudflare.com` and `sara.ns.cloudflare.com`). **Copy these down** — you need them in step 6.

### Step 5: Double-check email records in Cloudflare (~5 min)

Before changing nameservers, verify the email records are perfect:

1. In Cloudflare DNS settings, confirm:
   - **5 MX records** matching Google's exact values (the ones from Namecheap)
   - **SPF TXT** record: `v=spf1 include:_spf.google.com ~all` (or whatever was at Namecheap)
   - **DKIM TXT** record at name `google._domainkey` (long string starting with `v=DKIM1; k=rsa; p=...`)
   - **DMARC TXT** record at name `_dmarc` (the one you added or copied)
2. If anything is missing or different from Namecheap, fix it now.

### Step 6: Change nameservers in Namecheap (~5 min + propagation)

> ⏸ **POINT OF NO RETURN** — after this, DNS is on Cloudflare.

1. Back in Namecheap: Domain List → **Manage** on `bentondrones.com`
2. Find the **Nameservers** section
3. Change from "Namecheap BasicDNS" to **Custom DNS**
4. Enter the **two Cloudflare nameservers** from step 4
5. Save. Namecheap warns that DNS changes can take up to 48 hours — that's the worst case; usually it's minutes.

---

## AFTER the cutover (steps 7–8): Verify everything still works

### Step 7: Verify immediately (~5 min)

1. In a terminal, run (Mac/Linux):
   ```bash
   dig bentondrones.com
   dig www.bentondrones.com
   dig bentondrones.com MX
   dig bentondrones.com TXT
   ```
   (Or on Windows, use `nslookup bentondrones.com`, `nslookup -type=mx bentondrones.com`, etc.)
2. Confirm the Shopify A record resolves, MX points to Google, TXT records appear.
3. **Test email:** send an email FROM Anderson's Benton Drones address TO a personal Gmail, and reply back. Both should work 100%.
4. **Test storefront:** open [bentondrones.com](https://bentondrones.com) — should load the Shopify store.
5. **Check SSL:** click the lock icon in the browser — should show a valid cert.

### Step 8: Add the leads record (~5 min)

> This can wait until after everything above is verified. Not urgent.

In Cloudflare DNS settings, add:

```
Type:   CNAME
Name:   leads
Content: benton-drones-lead-ingest.onrender.com
Proxy:  DNS only (gray cloud)
TTL:    Auto
```

This makes `leads.bentondrones.com` resolve to the Render app. Combined with Render's "Add Custom Domain" step (in the [Anderson briefing](docs/anderson-launch-briefing.html) section 4), this is what turns the branded URL on.

---

## Rollback (if something breaks)

If email or the storefront stops working:

1. In Namecheap: Domain List → Manage → Nameservers → change back to **Namecheap BasicDNS**
2. Verify DNS matches your screenshots from step 1 (putting the records back exactly)
3. Wait ~15 min, then re-test email + storefront
4. Call Tyler — we'll sort it

The screenshots from step 1 are your insurance policy. **Do not skip step 1.**

---

## What's after the cutover: Pages Admin Dashboard

Once DNS is on Cloudflare, the next phase (not urgent, future work) is:

1. Building a **static admin dashboard** hosted on **Cloudflare Pages** at `admin.bentondrones.com`
2. Gating it behind **Cloudflare Access** (Google OAuth or email one-time PIN — you log in with your Google account instead of a shared password)
3. Removing the Render password login entirely

All of this is zero additional cost (Cloudflare Free + Pages Free), **much faster** (no cold start), and **more secure** (identity-based auth with MFA). This is described in detail in the [ADR-001 architecture doc](../research/cloudflare-pages-admin/ADR-001-cloudflare-pages-admin-dashboard.md).

**You don't need to do anything about this today.** Just getting the DNS onto Cloudflare enables it.

---

## The email records reference

For convenience, here's what Google Workspace MX should look like (but **always trust your screenshots** over this doc):

| Type | Host | Value | Priority |
|------|------|-------|----------|
| MX | `@` | ASPMX.L.GOOGLE.COM | 1 |
| MX | `@` | ALT1.ASPMX.L.GOOGLE.COM | 5 |
| MX | `@` | ALT2.ASPMX.L.GOOGLE.COM | 5 |
| MX | `@` | ALT3.ASPMX.L.GOOGLE.COM | 10 |
| MX | `@` | ALT4.ASPMX.L.GOOGLE.COM | 10 |

(Newer setups may use `SMTP.GOOGLE.COM` as a single MX at priority 1 — again, match what Google Admin shows.)

SPF TXT:
```
v=spf1 include:_spf.google.com ~all
```

If **anything differs between your screenshots and this doc, your screenshots win.**

---

*Last updated: 2026-08-17. Designed to be followed without needing to read any other doc first.*
