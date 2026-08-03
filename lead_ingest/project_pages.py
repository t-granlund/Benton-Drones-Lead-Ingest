from __future__ import annotations

from lead_ingest.branded_template import LOGO_URL


DEFAULT_SUBTITLE = (
    "Benton Drones lead ingest MVP: Shopify-friendly public signup, owned backend "
    "data, protected admin, exports, and a clear path to production."
)


def shell(title: str, body: str, subtitle: str = DEFAULT_SUBTITLE) -> bytes:
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --olive: #809948;
      --olive-dark: #6f853d;
      --olive-deep: #5a6f30;
      --md-sys-color-primary: #809948;
      --md-sys-color-on-primary: #ffffff;
      --md-sys-color-primary-container: #f0f7f4;
      --md-sys-color-secondary: #6184d8;
      --md-sys-color-tertiary: #0000ff;
      --md-sys-color-surface: #ffffff;
      --md-sys-color-surface-container-low: #fbfbf8;
      --md-sys-color-surface-container: #f5f5f0;
      --md-sys-color-background: #f7f7f3;
      --md-sys-color-on-surface: #1b1b1b;
      --md-sys-color-on-surface-variant: #44464f;
      --md-sys-color-outline: #d7d3c5;
      --md-sys-color-outline-variant: #ede8d8;
      --md-sys-color-error: #b3261e;
      --md-sys-color-error-container: #f9dedc;
      --el-1: 0 1px 2px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.06);
      --el-2: 0 2px 4px rgba(0,0,0,0.05), 0 6px 16px rgba(0,0,0,0.07);
      --md-elevation-1: var(--el-1);
      --md-elevation-2: var(--el-2);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin:0; font-family:'Jost', sans-serif; font-weight:500; letter-spacing:0.02rem;
      color:#1b1b1b; background:var(--md-sys-color-background); line-height:1.65;
      font-size:1.05rem; -webkit-font-smoothing: antialiased;
    }}
    /* Hero — logo, eyebrow, title, subtitle */
    .hero {{
      background:linear-gradient(135deg, var(--olive) 0%, var(--olive-dark) 100%);
      color:#fff; padding:64px 24px 72px; text-align:center;
      box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }}
    .hero-inner {{ max-width:820px; margin:0 auto; }}
    .hero img {{
      height:60px; width:auto; margin-bottom:20px;
      filter:drop-shadow(0 2px 6px rgba(0,0,0,.22));
      transition:transform 0.2s ease, opacity 0.2s ease;
    }}
    .hero img:hover {{ transform:scale(1.03); opacity:0.92; }}
    .hero .eyebrow {{
      display:block; margin-bottom:14px;
      font-size:0.75rem; font-weight:700; text-transform:uppercase;
      letter-spacing:0.14em; opacity:0.82;
    }}
    .hero h1 {{
      margin:0 0 14px; font-size:2.4rem; font-weight:700;
      letter-spacing:0.01rem; line-height:1.15;
    }}
    .hero .subtitle {{
      max-width:740px; margin:0 auto; font-size:1.1rem;
      font-weight:500; opacity:0.92; line-height:1.55;
    }}
    main {{ max-width:1080px; margin:0 auto; padding:48px 24px 80px; }}
    h2 {{
      margin-top:48px; padding-bottom:8px; color:var(--md-sys-color-primary);
      font-size:1.7rem; font-weight:700; letter-spacing:0.01rem; line-height:1.2;
      border-bottom:1px solid var(--md-sys-color-outline);
    }}
    h3 {{ margin-bottom:8px; color:var(--md-sys-color-primary); font-size:1.3rem; font-weight:600; line-height:1.3; }}
    a {{ color:var(--md-sys-color-secondary); text-decoration:none; transition:opacity 0.2s ease; }}
    a:hover {{ text-decoration:underline; opacity:0.88; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:24px; }}
    .card {{
      background:var(--md-sys-color-surface); border:1px solid var(--md-sys-color-outline);
      border-top:4px solid var(--md-sys-color-primary);
      border-radius:16px; padding:28px; box-shadow:var(--el-1);
      transition: transform 0.22s ease, box-shadow 0.22s ease;
    }}
    .card:hover {{ transform:translateY(-2px); box-shadow:var(--el-2); }}
    .button {{
      display:inline-block; margin-top:16px; padding:16px 28px;
      border:none; border-radius:10px;
      background:linear-gradient(180deg, #8ba855 0%, var(--olive) 100%);
      color:var(--md-sys-color-on-primary); text-decoration:none;
      font-weight:600; text-transform:uppercase; font-size:0.82rem; letter-spacing:0.08rem;
      box-shadow: var(--el-1); transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .button:hover {{ transform:translateY(-1px); box-shadow:var(--el-2); text-decoration:none; }}
    .button:active {{ transform:translateY(0); box-shadow:var(--el-1); }}
    .button.secondary {{
      background:transparent; color:var(--md-sys-color-secondary);
      border:1.5px solid var(--md-sys-color-secondary); box-shadow:none;
    }}
    .button.secondary:hover {{ background:#e7ecff; border-color:var(--md-sys-color-secondary); }}
    .button:focus-visible {{ outline:2px solid var(--md-sys-color-primary); outline-offset:2px; }}
    .pill {{
      display:inline-block; padding:6px 14px; border-radius:999px;
      font-weight:700; font-size:0.78rem; letter-spacing:0.08rem;
      text-transform:uppercase; border:1.5px solid;
    }}
    .done {{ color:#3d4d1f; background:var(--md-sys-color-primary-container); border-color:var(--md-sys-color-primary); }}
    .next {{ color:#8a4a00; background:#fffce7; border-color:#e8893a; }}
    .muted {{ color:var(--md-sys-color-on-surface-variant); }}
    table {{
      width:100%; border-collapse:collapse; background:var(--md-sys-color-surface);
      border:1px solid var(--md-sys-color-outline); border-radius:12px; overflow:hidden;
      box-shadow:var(--el-1);
    }}
    th, td {{ padding:16px 18px; border-bottom:1px solid var(--md-sys-color-outline-variant); text-align:left; vertical-align:top; }}
    th {{ background:var(--md-sys-color-surface-container); color:var(--olive-deep); font-weight:700; font-size:0.78rem; letter-spacing:0.08rem; text-transform:uppercase; }}
    tr:last-child td {{ border-bottom:none; }}
    tr:hover td {{ background:var(--md-sys-color-surface-container-low); }}
    code, pre {{ font-family:ui-monospace,SFMono-Regular,Consolas,Menlo,monospace; font-size:0.9rem; letter-spacing:0; }}
    code {{ background:var(--md-sys-color-surface-container-low); border:1px solid var(--md-sys-color-outline); border-radius:6px; padding:2px 6px; }}
    pre {{ background:#1b1b1b; color:#e5e7eb; border-radius:10px; padding:16px; overflow:auto; }}
    ol, ul {{ padding-left:20px; }}
    li {{ margin-bottom:10px; }}
    @media (max-width:600px) {{
      .hero {{ padding:48px 16px 56px; }}
      .hero h1 {{ font-size:1.8rem; }}
      .hero .subtitle {{ font-size:1rem; }}
      main {{ padding:32px 16px 64px; }}
      h2 {{ font-size:1.4rem; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} .card:hover {{ transform:none; }} }}
  </style>
</head>
<body>
<header class="hero"><div class="hero-inner">
  <img src="{LOGO_URL}" alt="Benton Drones logo" loading="lazy">
  <span class="eyebrow">Benton Drones</span>
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>
</div></header>
<main>{body}</main>
</body>
</html>"""
    return html.encode("utf-8")


def shopify_preview_page() -> bytes:
    body = """
<section class="grid">
  <div class="card"><span class="pill done">Easiest launch path</span><h3>Shopify page + owned signup</h3><p>This preview represents the Shopify landing page Benton Drones can build first. The call-to-action sends visitors to the owned signup experience.</p><a class="button" href="/signup/default?source=shopify&campaign=drone-delivery-page&page_url=/pages/drone-delivery-signup">Preview signup CTA</a></div>
  <div class="card"><span class="pill done">Data ownership</span><h3>Owned backend</h3><p>Lead data, addresses, consent, geocoding, clusters, and exports stay in the Benton Drones backend instead of Shopify metafields or Google Sheets.</p><a class="button secondary" href="/overview">View system overview</a></div>
</section>

<h2>What the Shopify page should explain</h2>
<div class="card">
  <ul>
    <li>What the drone delivery simulation program is.</li>
    <li>Why Benton Drones is collecting household/location interest.</li>
    <li>What participants are consenting to.</li>
    <li>That signup does not guarantee service availability.</li>
    <li>How Benton Drones protects and uses the submitted information.</li>
  </ul>
</div>

<h2>Recommended first production URL pattern</h2>
<pre>Shopify SEO page:
https://bentondrones.com/pages/drone-delivery-signup

CTA target:
https://leads.bentondrones.com/signup/default?source=shopify&campaign=drone-delivery-page</pre>

<h2>Why this path first?</h2>
<div class="grid">
  <div class="card"><h3>Lowest risk</h3><p>No Shopify app proxy behavior needs to be solved before launch.</p></div>
  <div class="card"><h3>Fastest launch</h3><p>The storefront page can go live while the backend remains independently hosted and secured.</p></div>
  <div class="card"><h3>Clean upgrade</h3><p>The same backend can later support Shopify App Proxy after real Shopify request signing is verified.</p></div>
</div>
"""
    return shell("Shopify Landing Page Preview", body)


def changelog_page() -> bytes:
    body = """
<h2>Changelog</h2>
<p>A running history of what has been built, fixed, and shipped. Newest entries are at the bottom of the build phase and the top of the release log.</p>

<h3>Build phases</h3>
<table>
  <tr><th>Iteration</th><th>Completed</th><th>Outcome</th></tr>
  <tr><td>0</td><td>Workflow modernization plan</td><td>Defined owned replacement for Google Forms, PDFfiller, Sheets, and manual Google Earth planning.</td></tr>
  <tr><td>1</td><td>Local MVP foundation</td><td>Built Python/SQLite signup, consent, geocoding mock, admin dashboard, exports, and clustering utilities.</td></tr>
  <tr><td>2</td><td>Shopify awareness</td><td>Added Shopify context fields and documentation for Shopify page/app proxy integration.</td></tr>
  <tr><td>3</td><td>Shopify HMAC utilities</td><td>Added signature verification helpers and signed context token handoff for future App Proxy use.</td></tr>
  <tr><td>4</td><td>Admin/export protection</td><td>Protected admin and exports with password login and signed session cookies.</td></tr>
  <tr><td>5</td><td>CSRF + spam resistance</td><td>Added CSRF tokens, honeypot field, and in-memory POST rate limiting.</td></tr>
  <tr><td>6</td><td>Project communication pages</td><td>Added overview, Shopify preview, changelog, and roadmap pages for clear MVP review.</td></tr>
  <tr><td>7</td><td>Waiver + signature + audit trail</td><td>Real waiver text from PDF, typed-name signature capture, and a full consent/signature audit trail.</td></tr>
  <tr><td>8</td><td>Branding + dashboard upgrade</td><td>Material 3 + Benton design system across all pages; admin dashboard with Leaflet map, analytics cards, and breakdowns.</td></tr>
  <tr><td>9</td><td>Production hardening</td><td>Security headers, secret validation, body-size limits, and production-readiness review.</td></tr>
  <tr><td>10</td><td>Hosted deployment</td><td>Dockerfile, Railway config, then Render + Neon PostgreSQL. App live at benton-drones-lead-ingest.onrender.com.</td></tr>
  <tr><td>11</td><td>Real geocoder</td><td>Replaced the mock with US Census primary + Nominatim fallback, cached in the database (<code>geocode_cache</code>), plus a live-gated backfill script. Map pins are real now.</td></tr>
  <tr><td>12</td><td>Persistent rate limiting</td><td>Token-bucket-in-DB limiter shared across processes and restarts, per-route limits, 429 + <code>Retry-After</code>, loud fallback on storage failure.</td></tr>
  <tr><td>13</td><td>JIRA queue replay</td><td>On-read sweep + daemon worker with exponential backoff, dead-letter after 5 attempts, and idempotency keys so ambiguous timeouts never duplicate tickets.</td></tr>
  <tr><td>14</td><td>Email notifications (code)</td><td>stdlib <code>smtplib</code> sender, DB-backed <code>email_queue</code> with backoff + dead-letter, customer confirmation + internal alert templates. Live-send waits on the Workspace SMTP app password.</td></tr>
  <tr><td>15</td><td>Backups &amp; monitoring (code + docs)</td><td>DB-aware <code>/healthz</code> (no DDL on the health path), strictly read-only <code>scripts/verify_backup.py</code>, and a recovery playbook with human placeholders for Neon/monitor evidence.</td></tr>
</table>

<h3>Release log</h3>
<table>
  <tr><th>Type</th><th>Change</th></tr>
  <tr><td><span class="pill done">Feature</span></td><td>Playwright browser-automation E2E suite — 12 real-Chromium tests covering public pages, signup flow, admin journey, and exports. New <code>make test-e2e-browser</code> and <code>make test-e2e-live</code> targets; CI installs Chromium and gates on the count.</td></tr>
  <tr><td><span class="pill done">Feature</span></td><td>CI workflow (GitHub Actions) with pip caching and test-count gates so a deleted test can never silently pass.</td></tr>
  <tr><td><span class="pill next">Fix</span></td><td>Auto-migrate older signups tables by adding missing columns on startup.</td></tr>
  <tr><td><span class="pill next">Fix</span></td><td>Cast text <code>created_at</code> to timestamptz in the Postgres weekly-analytics query.</td></tr>
  <tr><td><span class="pill done">Feature</span></td><td>Render deployment blueprint (<code>render.yaml</code>) + deployment guide; live URL added to README.</td></tr>
  <tr><td><span class="pill done">Feature</span></td><td>Neon PostgreSQL support via <code>DATABASE_URL</code> with automatic SQLite fallback; real waiver extracted from PDF.</td></tr>
  <tr><td><span class="pill done">Docs</span></td><td>Visual before &amp; after architecture page, Anderson plain-language guide, and refreshed training/explainer guides with fully visual SVG diagrams.</td></tr>
  <tr><td><span class="pill done">Feature</span></td><td><strong>Wiggum loop build phase (iterations 11&ndash;15):</strong> real geocoder (Census + Nominatim + DB cache), persistent DB-backed rate limiting, JIRA queue replay worker, email notification queue + templates, and backup/monitoring tooling + playbook. 79 new tests. Full write-up in <code>docs/wiggum-loop-report.md</code>.</td></tr>
</table>

<h2>Current test posture</h2>
<div class="card">
  <p><strong>429 tests, all passing.</strong> 360 unit/integration + 57 HTTP end-to-end + 12 real-browser (Playwright) end-to-end. The suite covers validation, database persistence, consent &amp; signature audit, Shopify context, exports, clustering, authentication, protected routes, CSRF, persistent rate limiting, security headers, geocoding providers + cache, JIRA queue replay, email notification queue, backup verification, production hardening, and the full signup-to-admin-to-export journey in a real browser.</p>
</div>
"""
    return shell("MVP Changelog", body)


def api_preflight_page() -> bytes:
    body = """
<h2>What this checklist is for</h2>
<div class="card">
  <p>This page explains what we need before using command-line tools or APIs to automate Cloudflare DNS, Namecheap registrar checks, Google Workspace email verification, Shopify setup, and backend deployment.</p>
  <p>The rule: automate read-only checks first, then carefully automate writes after records and rollback are verified.</p>
</div>

<h2>Automation priority</h2>
<table>
  <tr><th>Platform</th><th>Automate first?</th><th>Recommended first action</th></tr>
  <tr><td>Cloudflare</td><td><span class="pill done">Yes</span></td><td>Read-only API inventory of zone and DNS records.</td></tr>
  <tr><td>Backend host</td><td><span class="pill done">Yes</span></td><td>Automated deploy/env checks once hosting is chosen.</td></tr>
  <tr><td>Google Workspace</td><td><span class="pill next">Partial</span></td><td>Automate DNS verification; keep admin writes manual first.</td></tr>
  <tr><td>Shopify</td><td><span class="pill next">Partial</span></td><td>Manual page/domain setup first; CLI/API later for themes/app proxy.</td></tr>
  <tr><td>Namecheap</td><td><span class="pill next">Read-only first</span></td><td>Export current DNS/nameserver state before any cutover.</td></tr>
</table>

<h2>Secrets we may need</h2>
<pre>CLOUDFLARE_API_TOKEN=
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
CSRF_SECRET=</pre>

<h2>Safe first scripts to build</h2>
<table>
  <tr><th>Script</th><th>Purpose</th><th>Risk</th></tr>
  <tr><td><code>scripts/check_dns.py</code></td><td>Verify DNS records resolve as expected.</td><td>Low: read-only</td></tr>
  <tr><td><code>scripts/check_email_auth.py</code></td><td>Verify MX, SPF, DKIM, DMARC DNS records.</td><td>Low: read-only</td></tr>
  <tr><td><code>scripts/check_cloudflare_zone.py</code></td><td>Use Cloudflare API to inventory DNS records.</td><td>Low if token is read-only</td></tr>
  <tr><td><code>scripts/preflight_report.py</code></td><td>Create a plain-English readiness report.</td><td>Low: read-only</td></tr>
</table>

<h2>Do not automate yet</h2>
<div class="card">
  <ul>
    <li>Namecheap nameserver cutover</li>
    <li>Deleting DNS records</li>
    <li>Changing MX records</li>
    <li>Changing SPF/DKIM/DMARC records</li>
    <li>Switching Shopify App Proxy to production</li>
  </ul>
</div>

<h2>Definition of ready</h2>
<div class="card">
  <ol>
    <li>Cloudflare read-only API token exists.</li>
    <li>Cloudflare zone ID for <code>bentondrones.com</code> is known.</li>
    <li>Namecheap DNS and nameservers are screenshotted/exported.</li>
    <li>Google Workspace MX/SPF/DKIM/DMARC records are confirmed.</li>
    <li>Shopify A/CNAME requirements are confirmed.</li>
    <li>Backend hosting provider is selected.</li>
    <li>Production target for <code>leads.bentondrones.com</code> is known.</li>
    <li>Secrets storage approach is chosen.</li>
  </ol>
</div>

<p><a class="button" href="/domain-setup">Domain Setup</a> <a class="button secondary" href="/roadmap">Roadmap</a></p>
"""
    return shell("API & CLI Automation Preflight", body)


def domain_setup_page() -> bytes:
    body = """
<h2>Recommended Domain Architecture</h2>
<div class="card">
  <p>Keep Namecheap as the registrar, move authoritative DNS to Cloudflare, keep Google Workspace for email, keep Shopify as the storefront, and host the lead ingest backend at <code>leads.bentondrones.com</code>.</p>
</div>

<table>
  <tr><th>Service</th><th>Recommended role</th><th>Status</th></tr>
  <tr><td>Namecheap</td><td>Domain registrar only</td><td><span class="pill done">Keep</span></td></tr>
  <tr><td>Cloudflare</td><td>Authoritative DNS, TLS/security/CDN options</td><td><span class="pill next">Set up</span></td></tr>
  <tr><td>Google Workspace</td><td>Email for <code>@bentondrones.com</code></td><td><span class="pill done">Preserve</span></td></tr>
  <tr><td>Shopify</td><td>Main storefront at <code>bentondrones.com</code></td><td><span class="pill done">Preserve</span></td></tr>
  <tr><td>Lead backend</td><td>Owned app at <code>leads.bentondrones.com</code></td><td><span class="pill next">Deploy next</span></td></tr>
</table>

<h2>Launch Subdomains</h2>
<table>
  <tr><th>Subdomain</th><th>Purpose</th><th>When</th></tr>
  <tr><td><code>leads.bentondrones.com</code></td><td>Signup, admin login, exports</td><td>Now</td></tr>
  <tr><td><code>staging.bentondrones.com</code></td><td>Pre-production testing</td><td>Soon</td></tr>
  <tr><td><code>admin.bentondrones.com</code></td><td>Dedicated admin UI</td><td>Later</td></tr>
  <tr><td><code>api.bentondrones.com</code></td><td>Dedicated API</td><td>Later</td></tr>
</table>

<h2>Preflight Checklist</h2>
<div class="grid">
  <div class="card"><h3>Namecheap</h3><ul><li>Screenshot current nameservers</li><li>Screenshot all DNS records</li><li>Check advanced DNS and email sections</li><li>Record current A and CNAME values</li></ul></div>
  <div class="card"><h3>Google Workspace</h3><ul><li>Confirm MX records</li><li>Confirm SPF</li><li>Generate/confirm DKIM</li><li>Add DMARC in monitor mode</li><li>Test send/receive before cutover</li></ul></div>
  <div class="card"><h3>Shopify</h3><ul><li>Confirm required A/CNAME</li><li>Check domain health</li><li>Check SSL status</li><li>Keep Shopify records DNS-only initially</li></ul></div>
  <div class="card"><h3>Cloudflare</h3><ul><li>Add site</li><li>Verify imported records</li><li>Add missing MX/TXT</li><li>Add leads record after backend host exists</li><li>Only then change Namecheap nameservers</li></ul></div>
</div>

<h2>Initial DNS Template</h2>
<pre>A     @       VERIFY_SHOPIFY_OR_CURRENT_IP       DNS only
CNAME www     VERIFY_SHOPIFY_TARGET              DNS only
CNAME leads   VERIFY_BACKEND_HOST_TARGET         DNS only

MX    @       VERIFY_GOOGLE_MX
TXT   @       v=spf1 include:_spf.google.com ~all
TXT   google._domainkey  VERIFY_FROM_GOOGLE_ADMIN
TXT   _dmarc  v=DMARC1; p=none; rua=mailto:admin@bentondrones.com; adkim=s; aspf=s</pre>

<h2>Brand/Design Preflight</h2>
<div class="card">
  <p>No Benton Drones logo/theme files are currently in this repo. Before final styling, capture the current Shopify design system:</p>
  <ul><li>logo and favicon</li><li>brand colors</li><li>fonts</li><li>button styles</li><li>header/footer screenshots</li><li>current marketing tone and copy</li></ul>
</div>

<p><a class="button" href="/roadmap">View Roadmap</a> <a class="button secondary" href="/shopify-preview">View Shopify Preview</a></p>
"""
    return shell("Domain & DNS Setup Plan", body)


def current_state_page() -> bytes:
    body = """
<h2>Current state at a glance</h2>
<div class="grid">
  <div class="card"><h3>Built</h3><ul><li>Signup + admin dashboard, live on Render + Neon</li><li>Consent capture + CSV/GeoJSON/KML exports</li><li>Real geocoder (Census + Nominatim + DB cache)</li><li>Persistent DB-backed rate limiting</li><li>JIRA queue replay with backoff + dead-letter</li><li>Email notification code + queue (creds pending)</li><li>Backup/restore tooling + recovery playbook</li><li>Browser automation (Playwright)</li></ul><p><span class="pill done">429 tests pass</span></p></div>
  <div class="card"><h3>Ready to go</h3><ul><li>Browser QA can run anytime</li><li>DNS checks run anytime</li><li>Shopify CTA path is designed</li><li>Cloudflare check waits on token</li><li>Email + backups activate the moment credentials land</li></ul></div>
  <div class="card"><h3>Blocked / waiting (one human session)</h3><ul><li>Cloudflare token for read-only zone inventory</li><li>Namecheap DNS/nameserver screenshots</li><li>Google Workspace MX/SPF/DKIM/DMARC + SMTP app password</li><li>Shopify A/CNAME + myshopify domain</li><li>Neon console backup/retention values + uptime monitor account</li></ul></div>
  <div class="card"><h3>Not built yet</h3><ul><li>Production cutover at leads.bentondrones.com (needs the human session)</li><li>Shopify App Proxy production (post-launch)</li><li>Internal map UI beyond the admin preview (post-launch)</li></ul></div>
</div>

<h2>What you should do next</h2>
<div class="card">
  <ol>
    <li>Open the full status doc: <code>docs/current-state-and-next-steps.md</code>.</li>
    <li>Capture Namecheap, Google Workspace, and Shopify platform state.</li>
    <li>Create a Cloudflare read-only API token and run <code>python scripts/check_cloudflare_zone.py</code>.</li>
    <li>Add the <code>leads.bentondrones.com</code> custom domain on the Render service.</li>
    <li>Create the Shopify landing page CTA.</li>
    <li>Only then migrate DNS to Cloudflare.</li>
  </ol>
</div>

<p><a class="button" href="/overview">Overview</a> <a class="button" href="/goals">Goals</a> <a class="button secondary" href="/judges">Judges</a></p>
"""
    return shell("Current State & Next Steps", body)


def goals_page() -> bytes:
    body = """
<h2>Goal stack</h2>
<div class="card"><p>These goals define the end-to-end Benton Drones Lead-Ingest implementation plan: local MVP, domains, Shopify, Google Workspace, deployment, design system, QA, and BDS/Dolt-style tracking.</p></div>
<table>
  <tr><th>Area</th><th>Goal file</th><th>Status</th></tr>
  <tr><td>Local MVP</td><td><code>goals/lead-ingest-local-mvp.md</code></td><td><span class="pill done">In progress</span></td></tr>
  <tr><td>Domains / DNS / Cloudflare</td><td><code>goals/domain-dns-cloudflare-goal.md</code></td><td><span class="pill next">Needs platform snapshots</span></td></tr>
  <tr><td>Namecheap preflight</td><td><code>goals/namecheap-preflight-goal.md</code></td><td><span class="pill next">Manual capture needed</span></td></tr>
  <tr><td>Google Workspace</td><td><code>goals/google-workspace-email-auth-goal.md</code></td><td><span class="pill next">Manual verification needed</span></td></tr>
  <tr><td>Shopify landing page</td><td><code>goals/shopify-landing-page-goal.md</code></td><td><span class="pill next">Next</span></td></tr>
  <tr><td>Backend deployment</td><td><code>goals/backend-deployment-goal.md</code></td><td><span class="pill done">Live on Render + Neon</span></td></tr>
  <tr><td>Design system</td><td><code>goals/design-system-capture-goal.md</code></td><td><span class="pill next">Needs capture</span></td></tr>
  <tr><td>BDS/Dolt tracking</td><td><code>goals/bds-dolt-tracking-goal.md</code></td><td><span class="pill done">CSV layer created</span></td></tr>
  <tr><td>Real geocoding</td><td><code>goals/geocoding-provider-goal.md</code></td><td><span class="pill done">Built &mdash; Census + Nominatim + cache</span></td></tr>
  <tr><td>Email notifications</td><td><code>goals/email-notifications-goal.md</code></td><td><span class="pill next">Code built &mdash; needs SMTP app password</span></td></tr>
  <tr><td>Backups / monitoring</td><td><code>goals/backups-monitoring-goal.md</code></td><td><span class="pill next">Code+docs built &mdash; needs Neon/monitor session</span></td></tr>
  <tr><td>Persistent rate limiting</td><td><code>goals/persistent-rate-limiting-goal.md</code></td><td><span class="pill done">Built &mdash; token-bucket-in-DB</span></td></tr>
  <tr><td>JIRA queue replay</td><td><code>goals/jira-queue-replay-goal.md</code></td><td><span class="pill done">Built &mdash; sweep + daemon + dead-letter</span></td></tr>
  <tr><td>Internal map UI</td><td><code>goals/internal-map-ui-goal.md</code></td><td><span class="pill next">Post-launch</span></td></tr>
</table>
<p><a class="button" href="/judges">View Judges</a> <a class="button secondary" href="/api-preflight">API/CLI Preflight</a></p>
"""
    return shell("Implementation Goals", body)


def judges_page() -> bytes:
    body = """
<h2>Judge stack</h2>
<div class="card"><p>Judges define PASS/FAIL/BLOCKED/DEFERRED criteria. No production claim counts unless it is tied to evidence in <code>tracking/evidence.csv</code>. Mean? Yes. Useful? Also yes.</p></div>
<table>
  <tr><th>Area</th><th>Judge file</th><th>Current result</th></tr>
  <tr><td>Local MVP</td><td><code>judges/local-mvp-judge.md</code></td><td><span class="pill next">Ready</span></td></tr>
  <tr><td>Domains / DNS / Cloudflare</td><td><code>judges/domain-dns-cloudflare-judge.md</code></td><td><span class="pill next">Not ready</span></td></tr>
  <tr><td>Namecheap</td><td><code>judges/namecheap-preflight-judge.md</code></td><td><span class="pill next">Not ready</span></td></tr>
  <tr><td>Google Workspace</td><td><code>judges/google-workspace-email-auth-judge.md</code></td><td><span class="pill next">Not ready</span></td></tr>
  <tr><td>Shopify landing page</td><td><code>judges/shopify-landing-page-judge.md</code></td><td><span class="pill next">Not ready</span></td></tr>
  <tr><td>Browser QA</td><td><code>judges/browser-qa-judge.md</code></td><td><span class="pill done">PASS smoke</span></td></tr>
  <tr><td>Read-only scripts</td><td><code>judges/readonly-preflight-scripts-judge.md</code></td><td><span class="pill done">PASS</span></td></tr>
  <tr><td>BDS/Dolt tracking</td><td><code>judges/bds-dolt-tracking-judge.md</code></td><td><span class="pill next">Ready</span></td></tr>
  <tr><td>Real geocoding</td><td><code>judges/geocoding-provider-judge.md</code></td><td><span class="pill done">PASS &middot; EVID-GEO-001</span></td></tr>
  <tr><td>Email notifications</td><td><code>judges/email-notifications-judge.md</code></td><td><span class="pill next">Code PASS / live-send BLOCKED (SMTP app password)</span></td></tr>
  <tr><td>Backups / monitoring</td><td><code>judges/backups-monitoring-judge.md</code></td><td><span class="pill next">Code+docs PASS / Neon+monitor evidence BLOCKED</span></td></tr>
  <tr><td>Persistent rate limiting</td><td><code>judges/persistent-rate-limiting-judge.md</code></td><td><span class="pill done">PASS &middot; EVID-RATELIMIT-001</span></td></tr>
  <tr><td>JIRA queue replay</td><td><code>judges/jira-queue-replay-judge.md</code></td><td><span class="pill done">PASS &middot; EVID-JIRA-002</span></td></tr>
  <tr><td>Internal map UI</td><td><code>judges/internal-map-ui-judge.md</code></td><td><span class="pill next">Post-launch &mdash; unblocked now that real geocoding shipped</span></td></tr>
</table>
<h2>Evidence tables</h2>
<div class="card"><p>Tracking lives in <code>tracking/requirements.csv</code>, <code>tracking/tasks.csv</code>, <code>tracking/judges.csv</code>, <code>tracking/evidence.csv</code>, <code>tracking/decisions.csv</code>, <code>tracking/platform_snapshots.csv</code>, and <code>tracking/status_log.csv</code>.</p></div>
<p><a class="button" href="/goals">View Goals</a> <a class="button secondary" href="/roadmap">Roadmap</a></p>
"""
    return shell("Implementation Judges", body)


def roadmap_page() -> bytes:
    body = """
<h2>Where We Are</h2>
<div class="card">
  <p><strong>429 tests green</strong> (360 unit + 57 HTTP E2E + 12 browser). The app is live on Render and the autonomous build phase is COMPLETE: real geocoder, persistent rate limiting, JIRA queue replay, email notification code, and backup tooling are all built and judged.</p>
  <p><strong>The critical path to launch is ONE human session for account access &mdash; not more engineering.</strong> This page is the single visual index for the plan: the gaps, the order, the decisions, and where every artifact lives.</p>
  <p><span class="pill done">5 gaps built &amp; judged</span> <span class="pill next">2 gaps need one credential each to go live</span> <span class="pill" style="color:var(--md-sys-color-error); background:var(--md-sys-color-error-container); border-color:var(--md-sys-color-error);">1 gap human-gated</span> <span class="pill muted">2 gaps post-launch</span></p>
  <p><a class="button" href="/goals">Goals</a> <a class="button" href="/judges">Judges</a> <a class="button secondary" href="/prd">PRD &amp; UAT Plan</a> <a class="button secondary" href="/completion-guide">Completion Guide</a></p>
</div>

<h2>The 8 Production Gaps &mdash; Status Board</h2>
<p>Autonomy is the hero: green means an agent builds it with zero human help, red means only you can do it, split means the agent writes the code and you drop in one credential.</p>
<div class="grid">
  <div class="card">
    <p><span class="pill next">P0</span> <span class="pill done">DONE &mdash; judge PASS</span></p>
    <h3>G1 &mdash; Real Geocoder</h3>
    <p>US Census primary + Nominatim fallback, cached in <code>geocode_cache</code>, live-verified against real APIs. Mock kept for offline tests.</p>
    <p class="muted"><code>REQ-GEO-001</code> &middot; <code>EVID-GEO-001</code></p>
  </div>
  <div class="card" style="border-top-color:var(--md-sys-color-error);">
    <p><span class="pill next">P0</span> <span class="pill" style="color:var(--md-sys-color-error); background:var(--md-sys-color-error-container); border-color:var(--md-sys-color-error);">Needs you</span></p>
    <h3>G2 &mdash; Custom Domain</h3>
    <p><code>leads.bentondrones.com</code> not live. Cloudflare DNS cutover + Render custom domain + TLS, preserving Google Workspace email.</p>
    <p class="muted">Maps to existing <code>REQ-DEPLOY-001</code> / <code>REQ-DNS-001</code></p>
  </div>
  <div class="card" style="border-top-color:var(--md-sys-color-secondary);">
    <p><span class="pill next">P0</span> <span class="pill" style="color:#ffffff; background:linear-gradient(90deg, var(--olive) 50%, var(--md-sys-color-error) 50%); border-color:var(--md-sys-color-on-surface-variant);">Agent codes / you credential</span></p>
    <h3>G3 &mdash; Email Notifications</h3>
    <p><strong>Code complete:</strong> stdlib <code>smtplib</code>, DB-backed <code>email_queue</code> with backoff + dead-letter, customer + internal templates. Live-send waits on the Workspace SMTP app password.</p>
    <p class="muted"><code>REQ-NOTIFY-001</code> &middot; <code>EVID-NOTIFY-001</code> &middot; live-send BLOCKED</p>
  </div>
  <div class="card" style="border-top-color:var(--md-sys-color-secondary);">
    <p><span class="pill next">P1</span> <span class="pill" style="color:#ffffff; background:linear-gradient(90deg, var(--olive) 50%, var(--md-sys-color-error) 50%); border-color:var(--md-sys-color-on-surface-variant);">Agent codes / you credential</span></p>
    <h3>G4 &mdash; Backups &amp; Monitoring</h3>
    <p><strong>Code+docs complete:</strong> DB-aware <code>/healthz</code>, read-only <code>verify_backup.py</code>, recovery playbook. Neon console values + monitor account are the remaining evidence.</p>
    <p class="muted"><code>REQ-BACKUP-001</code> &middot; <code>EVID-BACKUP-001</code> &middot; console evidence BLOCKED</p>
  </div>
  <div class="card">
    <p><span class="pill next">P1</span> <span class="pill done">DONE &mdash; judge PASS</span></p>
    <h3>G5 &mdash; Persistent Rate Limiting</h3>
    <p>Token-bucket-in-DB with atomic compare-and-set, per-route limits, 429 + <code>Retry-After</code>, loud in-memory fallback. No Redis.</p>
    <p class="muted"><code>REQ-RATELIMIT-001</code> &middot; <code>EVID-RATELIMIT-001</code></p>
  </div>
  <div class="card">
    <p><span class="pill next">P1</span> <span class="pill done">DONE &mdash; judge PASS</span></p>
    <h3>G6 &mdash; JIRA Queue Replay</h3>
    <p>On-read sweep + daemon worker, exponential backoff, dead-letter after 5 attempts, idempotency keys kill duplicate tickets.</p>
    <p class="muted"><code>REQ-JIRA-002</code> &middot; <code>EVID-JIRA-002</code></p>
  </div>
  <div class="card" style="border-top-color:var(--md-sys-color-secondary);">
    <p><span class="pill muted">P2</span> <span class="pill" style="color:#ffffff; background:linear-gradient(90deg, var(--olive) 50%, var(--md-sys-color-error) 50%); border-color:var(--md-sys-color-on-surface-variant);">Agent codes / you credential</span></p>
    <h3>G7 &mdash; Shopify App Proxy</h3>
    <p>App Proxy not validated for production. Verify real Shopify request signing before enabling the <code>/apps/...</code> path.</p>
    <p class="muted">Maps to existing <code>REQ-SHOP-002</code> &middot; post-launch</p>
  </div>
  <div class="card">
    <p><span class="pill muted">P2</span> <span class="pill done">Agent builds it</span></p>
    <h3>G8 &mdash; Internal Map UI</h3>
    <p>Map beyond the admin preview: leads, clusters, and service zones for day-to-day planning.</p>
    <p class="muted">Maps to <code>REQ-MAPUI-001</code> &middot; post-launch</p>
  </div>
</div>

<h2>Execution Order</h2>
<p><strong>Everything before the red gate is DONE</strong> (built and judged in the wiggum loop, iterations 11&ndash;15). Everything after it unblocks the moment the human session happens.</p>
<div style="display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin:20px 0;">
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G1 Geocoder</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G5 Rate Limit</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G6 JIRA Replay</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G3 Email Code</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G4 Backup Code</span>
  <span style="color:#b3261e; font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-error-container); color:var(--md-sys-color-error); border:2px solid var(--md-sys-color-error); border-radius:10px; padding:10px 16px; font-weight:700; font-size:0.85rem; letter-spacing:0.05rem; text-transform:uppercase;">Human Session</span>
  <span style="color:#b3261e; font-weight:700;">&rarr;</span>
  <span style="background:#fffce7; color:#8a4a00; border:1.5px solid #e8893a; border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G2 Domain</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:#fffce7; color:#8a4a00; border:1.5px solid #e8893a; border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G3/G4 Credentials</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:linear-gradient(135deg, var(--olive) 0%, var(--olive-dark) 100%); color:#ffffff; border:2px solid var(--olive-deep); border-radius:10px; padding:10px 16px; font-weight:700; font-size:0.85rem; letter-spacing:0.05rem; text-transform:uppercase;">Launch</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-surface-container); color:var(--md-sys-color-on-surface-variant); border:1.5px solid var(--md-sys-color-outline); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G7 Shopify Proxy</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-surface-container); color:var(--md-sys-color-on-surface-variant); border:1.5px solid var(--md-sys-color-outline); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G8 Map UI</span>
</div>
<p><span class="pill done">Agents build</span> green &nbsp; <span class="pill next">Needs human input</span> amber &nbsp; <span class="pill" style="color:var(--md-sys-color-error); background:var(--md-sys-color-error-container); border-color:var(--md-sys-color-error);">Human gate</span> red &nbsp; <span class="pill muted">Post-launch</span> grey</p>

<h2>Where the Tracking Lives</h2>
<p>Every requirement has a goal file (what to build), a judge file (how we prove it), and tasks in the BDS tracking layer. CSVs in <code>tracking/</code> are canonical.</p>
<table>
  <tr><th>Requirement</th><th>Goal file</th><th>Judge file</th><th>Judge status</th><th>Tasks</th></tr>
  <tr><td><code>REQ-GEO-001</code></td><td><code>goals/geocoding-provider-goal.md</code></td><td><code>judges/geocoding-provider-judge.md</code></td><td><span class="pill done">PASS</span></td><td><code>TASK-GEO-001</code>, <code>TASK-GEO-002</code></td></tr>
  <tr><td><code>REQ-NOTIFY-001</code></td><td><code>goals/email-notifications-goal.md</code></td><td><code>judges/email-notifications-judge.md</code></td><td><span class="pill next">Code PASS / live-send BLOCKED</span></td><td><code>TASK-NOTIFY-001</code>, <code>TASK-NOTIFY-002</code></td></tr>
  <tr><td><code>REQ-BACKUP-001</code></td><td><code>goals/backups-monitoring-goal.md</code></td><td><code>judges/backups-monitoring-judge.md</code></td><td><span class="pill next">Code+docs PASS / evidence BLOCKED</span></td><td><code>TASK-BACKUP-001</code>, <code>TASK-BACKUP-002</code></td></tr>
  <tr><td><code>REQ-RATELIMIT-001</code></td><td><code>goals/persistent-rate-limiting-goal.md</code></td><td><code>judges/persistent-rate-limiting-judge.md</code></td><td><span class="pill done">PASS</span></td><td><code>TASK-RATELIMIT-001</code></td></tr>
  <tr><td><code>REQ-JIRA-002</code></td><td><code>goals/jira-queue-replay-goal.md</code></td><td><code>judges/jira-queue-replay-judge.md</code></td><td><span class="pill done">PASS</span></td><td><code>TASK-JIRA-002</code></td></tr>
  <tr><td><code>REQ-MAPUI-001</code></td><td><code>goals/internal-map-ui-goal.md</code></td><td><code>judges/internal-map-ui-judge.md</code></td><td><span class="pill next">Not ready</span></td><td><code>TASK-MAPUI-001</code></td></tr>
</table>

<h2>Architecture Decisions</h2>
<table>
  <tr><th>ID</th><th>Decision</th><th>Why</th></tr>
  <tr><td><code>DEC-GEO-001</code></td><td>US Census Geocoder primary + Nominatim fallback + DB response cache.</td><td>Both free, keyless, public; Census has the best US street-address coverage; caching avoids repeat calls and respects usage policies.</td></tr>
  <tr><td><code>DEC-NOTIFY-001</code></td><td>stdlib <code>smtplib</code> over Google Workspace SMTP with an app password + DB send queue; SMS deferred.</td><td>Zero new dependencies or paid services; reuses the existing mailbox; the queue guarantees no signup is lost or blocked by an email failure.</td></tr>
  <tr><td><code>DEC-RATELIMIT-001</code></td><td>Token-bucket-in-DB with atomic updates for cross-process shared limits; no Redis.</td><td>The existing database provides the atomicity multi-process correctness needs; survives restarts; no new infrastructure for a single-host deployment.</td></tr>
  <tr><td><code>DEC-JIRA-001</code></td><td>On-read sweep + optional daemon replay with exponential backoff, dead-letter, and idempotency keys.</td><td>The sweep guarantees progress without a running worker; the daemon adds timeliness; backoff + dead-letter prevents poison-message loops; idempotency makes at-least-once delivery safe.</td></tr>
</table>

<h2>Production Readiness Checklist</h2>
<div class="grid">
  <div class="card"><h3>Must do</h3><ul><li>HTTPS</li><li>Production secrets</li><li>Backups</li><li>Privacy/consent legal review</li><li>Shopify landing page copy</li></ul></div>
  <div class="card"><h3>Should do</h3><ul><li><s>Real geocoder</s> shipped</li><li><s>PostgreSQL migration</s> shipped (Neon)</li><li><s>Shared rate limiting</s> shipped</li><li>Monitoring/logging (external monitor account pending)</li><li>Brand-matched styling</li></ul></div>
  <div class="card"><h3>Later</h3><ul><li>Shopify App Proxy</li><li>Map dashboard</li><li>Cluster editing UI</li><li>Email/SMS automations</li><li>Advanced reporting</li></ul></div>
</div>
"""
    return shell(
        "Project Tracking & Detail",
        body,
        subtitle="MVP Roadmap evolved: the 8 production gaps, execution order, architecture decisions, and the index into goals/, judges/, and tracking/.",
    )


def prd_uat_plan_page() -> bytes:
    body = """
<h2>Executive Summary</h2>
<div class="card">
  <p><strong>Lead-Ingest is a complete, well-tested (429 passing tests), self-hosted Python-stdlib app, live on Render &mdash; and the autonomous build phase is finished.</strong> The geocoder is real (Census + Nominatim + cache, live-verified), rate limiting is persistent in the DB, the JIRA queue replays itself, email notification code is queued and ready, and backup tooling + a recovery playbook exist. The remaining blockers are human: the branded domain <code>leads.bentondrones.com</code>, the Workspace SMTP app password, and Neon/monitor console values.</p>
  <p><strong>All 6 agent-buildable gaps are built.</strong> The critical path to launch is human account access, not code.</p>
  <p><span class="pill done">429 tests passing</span> <span class="pill done">5 gaps closed by agents</span> <span class="pill next">2 gaps await credentials</span> <span class="pill next">1 human session required</span></p>
</div>

<h2>Current Test Posture</h2>
<table>
  <tr><th>Layer</th><th>Tests</th><th>Command</th><th>Notes</th></tr>
  <tr><td>Unit / Integration</td><td><strong>341</strong></td><td><code>make test</code></td><td>Validation, DB persistence, consent &amp; signature audit, exports, clustering, auth, CSRF, persistent rate limiting, security headers, geocoding providers + cache, JIRA replay, email queue, backup verification, production hardening. UAT (19) rides along here: 341 + 19 = <strong>360</strong> gated.</td></tr>
  <tr><td>UAT (scenario classes)</td><td><strong>19</strong> (8 scenarios)</td><td><code>make test</code></td><td>End-to-end business flows through the real server; all 8 scenarios pass.</td></tr>
  <tr><td>HTTP End-to-End</td><td><strong>57</strong></td><td><code>make test-e2e</code></td><td>Real HTTP against a live in-process server: public pages, signup flow, admin auth, dashboard, exports, security, CLI.</td></tr>
  <tr><td>Browser End-to-End (Playwright)</td><td><strong>12</strong></td><td><code>make test-e2e-browser</code></td><td>Real Chromium: public pages, full signup flow, admin journey, exports.</td></tr>
  <tr><td><strong>Total</strong></td><td><strong>429</strong></td><td><code>make test-all</code></td><td>CI gates on minimum counts: 360 unit/integration + 57 HTTP E2E + 12 browser E2E. A deleted test can never silently pass.</td></tr>
</table>

<h2>Production Gaps &amp; Requirements</h2>
<table>
  <tr><th>ID</th><th>Gap</th><th>Requirement</th><th>Priority</th><th>Effort</th><th>Autonomy</th></tr>
  <tr><td><strong>G1</strong></td><td><s>Mock geocoder returns fake coordinates</s> &mdash; CLOSED. Census primary + Nominatim fallback, DB-cached, live-verified.</td><td>Shipped behind the stable <code>GeocodeResult</code> interface; <code>GEOCODER_MODE=live</code> enables it.</td><td><span class="pill next">P0</span></td><td>M</td><td><span class="pill done">DONE &mdash; judge PASS</span></td></tr>
  <tr><td><strong>G2</strong></td><td>Branded domain <code>leads.bentondrones.com</code> not live.</td><td>Cloudflare DNS cutover + Render custom domain + TLS, preserving Google Workspace email.</td><td><span class="pill next">P0</span></td><td>S</td><td><span class="pill next">Human-gated</span></td></tr>
  <tr><td><strong>G3</strong></td><td>No email/SMS notifications &mdash; customers get silence after signup.</td><td>stdlib <code>smtplib</code> + DB-backed send queue with backoff/dead-letter &mdash; <strong>code shipped</strong>; SMS deferred.</td><td><span class="pill next">P0</span></td><td>M</td><td><span class="pill next">Code DONE / live-send needs SMTP app password</span></td></tr>
  <tr><td><strong>G4</strong></td><td>No documented backups or uptime monitoring.</td><td>DB-aware <code>/healthz</code>, read-only <code>verify_backup.py</code>, recovery playbook &mdash; <strong>code+docs shipped</strong>.</td><td><span class="pill next">P1</span></td><td>S</td><td><span class="pill next">Code DONE / evidence needs Neon + monitor</span></td></tr>
  <tr><td><strong>G5</strong></td><td><s>Rate limiting is in-memory only</s> &mdash; CLOSED. Token-bucket-in-DB, atomic CAS, shared across processes and restarts.</td><td>Shipped; per-route limits env-overridable; 429 sends <code>Retry-After</code>.</td><td><span class="pill next">P1</span></td><td>S</td><td><span class="pill done">DONE &mdash; judge PASS</span></td></tr>
  <tr><td><strong>G6</strong></td><td><s><code>jira_queue</code> failures sit forever</s> &mdash; CLOSED. On-read sweep + daemon, backoff, dead-letter, idempotency.</td><td>Shipped; admin dashboard shows pending/created/dead metrics.</td><td><span class="pill next">P1</span></td><td>S</td><td><span class="pill done">DONE &mdash; judge PASS</span></td></tr>
  <tr><td><strong>G7</strong></td><td>Shopify App Proxy not validated for production.</td><td>Prototype + verify real Shopify request signing before enabling <code>/apps/...</code> path.</td><td><span class="pill next">P2</span></td><td>S</td><td><span class="pill next">Code-autonomous + human credential</span></td></tr>
  <tr><td><strong>G8</strong></td><td>Map UI beyond the admin dashboard preview.</td><td>Internal map for leads, clusters, and service zones (post-launch polish).</td><td><span class="pill next">P2</span></td><td>L</td><td><span class="pill done">Fully autonomous</span></td></tr>
</table>

<h2>Recommended Phases</h2>
<div class="grid">
  <div class="card"><span class="pill done">DONE</span><h3>Phase 0 &mdash; Stop Lying </h3><p><strong>G1, G6, G5.</strong> Real geocoding, JIRA queue replay, persistent rate limiting &mdash; all built, judged PASS, and verified 3&times; green.</p></div>
  <div class="card"><span class="pill done">Code DONE</span><h3>Phase 1 &mdash; Close the Loop </h3><p><strong>G3, G4.</strong> Notification and backup/monitoring code shipped; one Google Workspace SMTP credential + Neon/monitor console values activate them.</p></div>
  <div class="card"><span class="pill next">Human session</span><h3>Phase 2 &mdash; Human Gate Sprint</h3><p><strong>G2 + credential drops.</strong> One 60&ndash;90 minute human session: Namecheap/Cloudflare/Google Workspace/Shopify logins, DNS cutover, custom domain, drop the SMTP credential.</p></div>
  <div class="card"><span class="pill done">After launch</span><h3>Phase 3 &mdash; Post-Launch Polish</h3><p><strong>G7, G8.</strong> Shopify App Proxy validation and the full map UI, once real leads are flowing.</p></div>
</div>
<h2>Build Order</h2>
<pre>G1  &rarr; G6  &rarr; G5  &rarr; G3(code)  &rarr; G4(code)  &rarr; [human session] &rarr; G2 &rarr; launch &rarr; G7 &rarr; G8</pre>
<p class="muted">Wiggum loop iterations 11&ndash;15 in <code>docs/wiggum-loop-report.md</code> document each build with judge verdicts and evidence IDs.</p>

<h2>Architecture Decisions</h2>
<div class="grid">
  <div class="card"><h3>ADR-1 &mdash; Geocoder</h3><p>US Census Geocoder primary, Nominatim fallback, results cached in DB, all behind the existing <code>GeocodeResult</code> interface so callers don&rsquo;t change. Free, no API keys, US-address-optimized.</p></div>
  <div class="card"><h3>ADR-2 &mdash; Notifications</h3><p>Stdlib <code>smtplib</code> + Google Workspace SMTP app password; sends queued in the DB so failures retry. SMS deferred &mdash; email covers launch.</p></div>
  <div class="card"><h3>ADR-3 &mdash; Rate Limiting</h3><p>Token-bucket-in-DB (works on SQLite and Postgres), shared across processes and restarts. No Redis, no new infrastructure.</p></div>
  <div class="card"><h3>ADR-4 &mdash; JIRA Replay</h3><p>On-read sweep (admin dashboard visit drains the queue) + daemon thread, exponential backoff, dead-letter after max attempts, idempotent on <code>lead_id</code> to avoid duplicate tickets.</p></div>
</div>

<h2>UAT Scenarios</h2>
<h3>Current suite &mdash; 8 scenarios, 19 tests, all passing</h3>
<table>
  <tr><th>Scenario</th><th>Covers</th><th>Status</th></tr>
  <tr><td><code>TestCompleteLeadCaptureFlow</code></td><td>Signup &rarr; validation &rarr; DB &rarr; consent/signature audit trail</td><td><span class="pill done"> Pass</span></td></tr>
  <tr><td><code>TestAdminReviewFlow</code></td><td>Login &rarr; dashboard &rarr; lead detail &rarr; print</td><td><span class="pill done"> Pass</span></td></tr>
  <tr><td><code>TestExportFlow</code></td><td>CSV / GeoJSON / KML exports contain the lead</td><td><span class="pill done"> Pass</span></td></tr>
  <tr><td><code>TestJiraFallbackFlow</code></td><td>JIRA down &rarr; lead still saved, ticket queued</td><td><span class="pill done"> Pass</span></td></tr>
  <tr><td><code>TestJiraSuccessFlow</code></td><td>JIRA up &rarr; ticket created and linked</td><td><span class="pill done"> Pass</span></td></tr>
  <tr><td><code>TestVariantTrackingFlow</code></td><td>Signup slugs, source/campaign attribution</td><td><span class="pill done"> Pass</span></td></tr>
  <tr><td><code>TestSecurityAbuseFlow</code></td><td>Honeypot, CSRF, rate limit, body-size abuse rejection</td><td><span class="pill done"> Pass</span></td></tr>
  <tr><td><code>TestPdfFallbackFlow</code></td><td>PDF render + HTML fallback when fpdf2 absent</td><td><span class="pill done"> Pass</span></td></tr>
</table>
<h3>Proposed new scenarios (post-gap-closure)</h3>
<table>
  <tr><th>ID</th><th>Scenario</th><th>Validates</th><th>Depends on</th></tr>
  <tr><td><strong>U9</strong></td><td>Real geocoding</td><td>Known address returns plausible lat/lng; cache hit on repeat; fallback provider engages</td><td>G1</td></tr>
  <tr><td><strong>U10</strong></td><td>Notification delivery</td><td>Signup triggers queued email; retry on SMTP failure</td><td>G3</td></tr>
  <tr><td><strong>U11</strong></td><td>JIRA queue replay</td><td>Queued failure retries with backoff; dead-letters after max attempts; no duplicates</td><td>G6</td></tr>
  <tr><td><strong>U12</strong></td><td>Backup &amp; restore</td><td>Documented restore procedure actually restores leads</td><td>G4</td></tr>
  <tr><td><strong>U13</strong></td><td>Shared rate limiting</td><td>429s persist across process restarts</td><td>G5</td></tr>
  <tr><td><strong>U14</strong></td><td>Custom domain (live)</td><td><code>leads.bentondrones.com</code> serves HTTPS signup end-to-end</td><td>G2</td></tr>
  <tr><td><strong>U15</strong></td><td>Map UI</td><td>Real geocoded pins render on the internal map</td><td>G1 + G8</td></tr>
</table>

<h2>Risks</h2>
<table>
  <tr><th>ID</th><th>Risk</th><th>Likelihood</th><th>Impact</th></tr>
  <tr><td><strong>R1</strong></td><td>Human gate session slips &mdash; domain and credentials stay blocked.</td><td><span class="pill next">High</span></td><td><span class="pill next">High</span></td></tr>
  <tr><td><strong>R2</strong></td><td>DNS cutover breaks Google Workspace email if MX/SPF/DKIM aren&rsquo;t preserved exactly.</td><td><span class="pill next">Medium</span></td><td><span class="pill next">High</span></td></tr>
  <tr><td><strong>R3</strong></td><td>Real geocoder fails on rural / PO-box addresses common in the service area.</td><td><span class="pill next">Medium</span></td><td><span class="pill done">Medium</span></td></tr>
  <tr><td><strong>R4</strong></td><td>PII exposure via third parties (email provider, JIRA ticket contents).</td><td><span class="pill next">Medium</span></td><td><span class="pill next">High</span></td></tr>
  <tr><td><strong>R5</strong></td><td>SQLite-on-Render data loss if <code>DATABASE_URL</code>/Neon isn&rsquo;t configured in production.</td><td><span class="pill next">Medium</span></td><td><span class="pill next">High</span></td></tr>
  <tr><td><strong>R6</strong></td><td>Replay worker creates duplicate JIRA tickets without idempotency.</td><td><span class="pill next">Medium</span></td><td><span class="pill done">Medium</span></td></tr>
  <tr><td><strong>R7</strong></td><td>SMTP app password stored insecurely or revoked, silently killing notifications.</td><td><span class="pill done">Low</span></td><td><span class="pill done">Medium</span></td></tr>
  <tr><td><strong>R8</strong></td><td>Map UI scope creep delays post-launch polish.</td><td><span class="pill next">Medium</span></td><td><span class="pill done">Low</span></td></tr>
</table>

<h2>Open Questions for Human</h2>
<div class="card">
  <ol>
    <li>Datastore decision: keep SQLite or commit to Neon Postgres for launch?</li>
    <li>When can we schedule the 60&ndash;90 minute human gate session (Namecheap / Cloudflare / Google Workspace / Shopify)?</li>
    <li>Notification sender identity: which <code>@bentondrones.com</code> address sends customer confirmations?</li>
    <li>SMS: in or out for launch? (Recommendation: out; email only.)</li>
    <li>Waiver legal review &mdash; confirm policy URLs are real and decide whether to bump <code>WAIVER_VERSION</code>.</li>
    <li>Domain cutover timing: before or after first real marketing push?</li>
    <li>Neon / Render tier: free tier acceptable for launch, or paid from day one?</li>
    <li>Map UI priority: is G8 a launch blocker for Anderson&rsquo;s planning workflow, or true post-launch polish?</li>
  </ol>
</div>

<h2>Next Actions</h2>
<div class="card">
  <ol>
    <li>Build <strong>G1</strong> (real geocoder), <strong>G6</strong> (JIRA replay), <strong>G5</strong> (DB rate limiting) autonomously &mdash; Phase 0.</li>
    <li>Write code for <strong>G3</strong> (notifications) and <strong>G4</strong> (backups/monitoring) so they&rsquo;re credential-ready.</li>
    <li>Schedule the human gate session; capture the SMTP credential; execute the <strong>G2</strong> DNS cutover.</li>
    <li>Launch on <code>leads.bentondrones.com</code>, then tackle <strong>G7</strong>/<strong>G8</strong> as post-launch polish.</li>
  </ol>
</div>

<p><a class="button" href="/roadmap">Roadmap</a> <a class="button secondary" href="/current-state">Current State</a></p>
"""
    return shell(
        "PRD & UAT Plan",
        body,
        subtitle="Production readiness for the Benton Drones lead ingest app: what\u2019s tested, what\u2019s missing, and the exact path to launch.",
    )


def completion_guide_page() -> bytes:
    body = """
<h2>Where We Are &mdash; The Big Picture</h2>
<div class="card">
  <p><strong>429 tests green</strong> (360 unit/integration + 57 HTTP E2E + 12 real-browser Playwright). The app is live on Render, and the agent-buildable engineering is DONE: real geocoder, persistent rate limiting, JIRA queue replay, email notification code, and backup tooling &mdash; on top of the signup/consent/dashboard/export/JIRA MVP.</p>
  <p><strong>The critical path to launch is ONE human session for account access &mdash; not more engineering.</strong> All six agent-buildable gaps are closed. The rest only need your logins and a few decisions.</p>
  <p><span class="pill done">Agent engineering done</span> <span class="pill next">One human session left</span> <span class="pill next">3 gaps to close (G2, G3 creds, G4 creds)</span></p>
</div>

<h2>The Road to Launch</h2>
<p>Build order, left to right. Everything before the human gate is DONE ( -marked); everything after it unblocks the moment the session happens.</p>
<div style="display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin:20px 0;">
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G1 Geocoder </span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G6 JIRA Replay </span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G5 Rate Limit </span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G3 Email Code </span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-primary-container); color:#3d4d1f; border:1.5px solid var(--olive); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G4 Backup Code </span>
  <span style="color:#b3261e; font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-error-container); color:var(--md-sys-color-error); border:2px solid var(--md-sys-color-error); border-radius:10px; padding:10px 16px; font-weight:700; font-size:0.85rem; letter-spacing:0.05rem; text-transform:uppercase;">Human Session</span>
  <span style="color:#b3261e; font-weight:700;">&rarr;</span>
  <span style="background:#fffce7; color:#8a4a00; border:1.5px solid #e8893a; border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G2 Domain</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:#fffce7; color:#8a4a00; border:1.5px solid #e8893a; border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G3/G4 Credentials</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:linear-gradient(135deg, var(--olive) 0%, var(--olive-dark) 100%); color:#ffffff; border:2px solid var(--olive-deep); border-radius:10px; padding:10px 16px; font-weight:700; font-size:0.85rem; letter-spacing:0.05rem; text-transform:uppercase;">Launch</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-surface-container); color:var(--md-sys-color-on-surface-variant); border:1.5px solid var(--md-sys-color-outline); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G7 Shopify Proxy</span>
  <span style="color:var(--olive-deep); font-weight:700;">&rarr;</span>
  <span style="background:var(--md-sys-color-surface-container); color:var(--md-sys-color-on-surface-variant); border:1.5px solid var(--md-sys-color-outline); border-radius:10px; padding:10px 14px; font-weight:600; font-size:0.85rem;">G8 Map UI</span>
</div>
<p><span class="pill done">Agents build</span> green &nbsp; <span class="pill next">Needs human input</span> amber &nbsp; <span class="pill" style="color:var(--md-sys-color-error); background:var(--md-sys-color-error-container); border-color:var(--md-sys-color-error);">Human gate</span> red &nbsp; <span class="pill muted">Post-launch</span> grey</p>

<h2>What YOU Need to Do</h2>
<p>Six steps, roughly 70&ndash;90 minutes total, doable in one sitting. An agent can ride along on a call or screenshare and do the technical parts live &mdash; you just provide the logins.</p>
<table>
  <tr><th>#</th><th>What to do</th><th>Where</th><th>Time</th><th>What it unblocks</th></tr>
  <tr><td><strong>1</strong></td><td>Create a read-only API token scoped to <code>bentondrones.com</code> with Zone read + DNS read permissions.</td><td>Cloudflare dashboard &rarr; My Profile &rarr; API Tokens</td><td>~10 min</td><td>DNS automation preflight (<code>scripts/check_cloudflare_zone.py</code>)</td></tr>
  <tr><td><strong>2</strong></td><td>Screenshot the current nameservers and every DNS record exactly as they exist today.</td><td>Namecheap &rarr; Domain List &rarr; Advanced DNS</td><td>~10 min</td><td>Safe DNS cutover with a rollback reference</td></tr>
  <tr><td><strong>3</strong></td><td>Confirm the MX / SPF / DKIM / DMARC records, and create an SMTP app password for the notification sender (set as <code>SMTP_USER</code> + <code>SMTP_PASSWORD</code> on Render).</td><td>Google Admin console</td><td>~20 min</td><td>G3 email notifications go live + preserves email through the DNS cutover</td></tr>
  <tr><td><strong>4</strong></td><td>Note the <code>myshopify.com</code> domain and the A/CNAME requirements; draft the landing page with a CTA linking to the signup.</td><td>Shopify Admin</td><td>~20 min</td><td>Shopify landing page + future App Proxy (G7)</td></tr>
  <tr><td><strong>5</strong></td><td>Add <code>leads.bentondrones.com</code> as a custom domain on the Render service.</td><td>Render dashboard &rarr; service &rarr; Settings &rarr; Custom Domains</td><td>~10 min</td><td>G2 domain cutover + TLS certificate</td></tr>
  <tr><td><strong>6</strong></td><td>Fill the <code>&lt;&lt;HUMAN:&gt;&gt;</code> placeholders in <code>docs/backup-recovery-playbook.md</code> (Neon retention + project values) and create a free external uptime monitor (UptimeRobot/BetterStack) pointed at <code>/healthz</code>.</td><td>Neon console + monitor signup</td><td>~15 min</td><td>G4 backups evidence + alerting</td></tr>
  <tr><td><strong>7</strong></td><td>Decide the open legal/business questions (listed below).</td><td>Anywhere &mdash; just answers</td><td>Varies</td><td>Final go/no-go</td></tr>
</table>
<div class="card">
  <h3>Open questions to decide (step 6)</h3>
  <ul>
    <li>Final waiver legal text sign-off (confirm policy URLs are real; decide whether to bump <code>WAIVER_VERSION</code>).</li>
    <li>Notification sender identity: which <code>@bentondrones.com</code> from-address sends customer confirmations (<code>NOTIFY_FROM</code> / <code>NOTIFY_INTERNAL_TO</code>).</li>
    <li>Domain cutover timing: before or after the first real marketing push.</li>
  </ul>
  <p class="muted">Total human time: ~90 minutes. One sitting. Agents do everything else. (Production database is already Neon Postgres &mdash; that decision is made.)</p>
</div>

<h2>What the AGENTS Will Do</h2>
<p>The autonomous build phase is complete &mdash; G1, G5, G6, G3(code), and G4(code) all shipped in wiggum loop iterations 11&ndash;15 with judge verdicts recorded. What remains for agents is the credential-gated activation during/after your session, then post-launch work.</p>
<table>
  <tr><th>ID</th><th>What we built / will do</th><th>Effort</th><th>Status</th></tr>
  <tr><td><strong>G1</strong></td><td>Real geocoder: US Census primary + Nominatim fallback, DB cache, backfill script. <code>GEOCODER_MODE=live</code> activates it on Render.</td><td>M</td><td><span class="pill done">DONE &mdash; judge PASS</span></td></tr>
  <tr><td><strong>G5</strong></td><td>Persistent token-bucket-in-DB rate limiting, shared across processes and restarts.</td><td>S</td><td><span class="pill done">DONE &mdash; judge PASS</span></td></tr>
  <tr><td><strong>G6</strong></td><td>JIRA queue replay worker: on-read sweep + daemon, exponential backoff, dead-letter, idempotency keys.</td><td>S</td><td><span class="pill done">DONE &mdash; judge PASS</span></td></tr>
  <tr><td><strong>G3</strong> (code)</td><td><code>smtplib</code> email notifications + DB-backed queue + templates. Agents flip it live the moment <code>SMTP_USER</code>/<code>SMTP_PASSWORD</code> exist.</td><td>M</td><td><span class="pill done">Code DONE</span> <span class="pill next">live-send waits on credential</span></td></tr>
  <tr><td><strong>G4</strong> (code)</td><td>DB-aware <code>/healthz</code>, read-only <code>verify_backup.py</code>, recovery playbook. Agents wire the monitor once the account exists.</td><td>S</td><td><span class="pill done">Code+docs DONE</span> <span class="pill next">evidence waits on console</span></td></tr>
  <tr><td><strong>G2</strong></td><td>Domain cutover: Cloudflare DNS + Render custom domain + TLS, executed live during your session with rollback ready.</td><td>S</td><td><span class="pill next">During human session</span></td></tr>
  <tr><td><strong>G7</strong></td><td>Shopify App Proxy signature verification against real Shopify requests (post-launch).</td><td>S</td><td><span class="pill next">Post-launch</span></td></tr>
  <tr><td><strong>G8</strong></td><td>Internal map UI for leads, clusters, and service zones (post-launch polish).</td><td>L</td><td><span class="pill next">Post-launch</span></td></tr>
</table>

<h2>How We&rsquo;ll Work Together</h2>
<div class="grid">
  <div class="card" style="border-top-color:var(--md-sys-color-error);">
    <span class="pill" style="color:var(--md-sys-color-error); background:var(--md-sys-color-error-container); border-color:var(--md-sys-color-error);">You &mdash; the human</span>
    <ul>
      <li>Account logins: Cloudflare, Namecheap, Google Workspace, Shopify, Render.</li>
      <li>Legal sign-off on the final waiver text.</li>
      <li>The final go/no-go call before cutover and launch.</li>
    </ul>
  </div>
  <div class="card">
    <span class="pill done">The agents</span>
    <ul>
      <li>All code, tests, and documentation.</li>
      <li>Deployment configuration and verification.</li>
      <li>DNS record creation once the Cloudflare token exists.</li>
      <li>Cutover execution during your session, with rollback ready.</li>
    </ul>
  </div>
</div>
<div class="card" style="margin-top:24px;">
  <p><strong>The rule:</strong> agents never touch production DNS or email, and never deploy to the branded domain, without your explicit go. You hold the keys; we do the typing.</p>
</div>

<h2>Definition of Done &mdash; Launch Checklist</h2>
<div class="card">
  <ol>
    <li>All 8 production gaps (G1&ndash;G8) closed or consciously deferred. (G1, G5, G6 already closed; G3/G4 code-complete awaiting credentials.)</li>
    <li>Test suite still 429+ green across unit, HTTP E2E, and browser E2E.</li>
    <li><code>leads.bentondrones.com</code> live with valid TLS.</li>
    <li>First real signup tested end-to-end on the custom domain: signup &rarr; consent audit &rarr; email notification &rarr; admin dashboard &rarr; exports &rarr; JIRA ticket.</li>
    <li>Anderson trained on the admin workflow.</li>
  </ol>
</div>

<p><a class="button" href="/prd">PRD &amp; UAT Plan</a> <a class="button secondary" href="/current-state">Current State</a> <a class="button secondary" href="/roadmap">Roadmap</a></p>
"""
    return shell(
        "Project Completion Guide",
        body,
        subtitle="The exact path to launch: what you need to do, what the agents will build, and how we split the work.",
    )
