from __future__ import annotations

from lead_ingest.branded_template import LOGO_URL


def shell(title: str, body: str) -> bytes:
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
  <p class="subtitle">Benton Drones lead ingest MVP: Shopify-friendly public signup, owned backend data, protected admin, exports, and a clear path to production.</p>
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
<table>
  <tr><th>Iteration</th><th>Completed</th><th>Outcome</th></tr>
  <tr><td>0</td><td>Workflow modernization plan</td><td>Defined owned replacement for Google Forms, PDFfiller, Sheets, and manual Google Earth planning.</td></tr>
  <tr><td>1</td><td>Local MVP foundation</td><td>Built Python/SQLite signup, consent, geocoding mock, admin dashboard, exports, and clustering utilities.</td></tr>
  <tr><td>2</td><td>Shopify awareness</td><td>Added Shopify context fields and documentation for Shopify page/app proxy integration.</td></tr>
  <tr><td>3</td><td>Shopify HMAC utilities</td><td>Added signature verification helpers and signed context token handoff for future App Proxy use.</td></tr>
  <tr><td>4</td><td>Admin/export protection</td><td>Protected admin and exports with password login and signed session cookies.</td></tr>
  <tr><td>5</td><td>CSRF + spam resistance</td><td>Added CSRF tokens, honeypot field, and in-memory POST rate limiting.</td></tr>
  <tr><td>6</td><td>Project communication pages</td><td>Added overview, Shopify preview, changelog, and roadmap pages for clear MVP review.</td></tr>
</table>

<h2>Current test posture</h2>
<div class="card">
  <p>The suite covers validation, database persistence, consent persistence, Shopify context, exports, clustering, authentication, protected routes, CSRF, rate limiting, Shopify security helpers, and local page availability.</p>
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
  <div class="card"><h3>Built</h3><ul><li>Local signup + admin dashboard</li><li>Consent capture + exports</li><li>Shopify context/HMAC utilities</li><li>Goals, judges, BDS/Dolt tracking</li><li>Read-only preflight scripts</li><li>Browser automation (Playwright)</li></ul><p><span class="pill done">56 tests pass</span></p></div>
  <div class="card"><h3>Ready to go</h3><ul><li>Browser QA can run anytime</li><li>DNS checks run anytime</li><li>Shopify CTA path is designed</li><li>Cloudflare check waits on token</li></ul></div>
  <div class="card"><h3>Blocked / waiting</h3><ul><li>Cloudflare token for read-only zone inventory</li><li>Namecheap DNS/nameserver screenshots</li><li>Google Workspace MX/SPF/DKIM/DMARC</li><li>Shopify A/CNAME + myshopify domain</li><li>Backend host selection</li></ul></div>
  <div class="card"><h3>Not built yet</h3><ul><li>Production deployment at leads.bentondrones.com</li><li>Real geocoding + map UI</li><li>Shopify App Proxy production</li><li>Design system capture</li><li>Backups/monitoring</li></ul></div>
</div>

<h2>What you should do next</h2>
<div class="card">
  <ol>
    <li>Open the full status doc: <code>docs/current-state-and-next-steps.md</code>.</li>
    <li>Capture Namecheap, Google Workspace, and Shopify platform state.</li>
    <li>Create a Cloudflare read-only API token and run <code>python scripts/check_cloudflare_zone.py</code>.</li>
    <li>Pick a backend host for <code>leads.bentondrones.com</code>.</li>
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
  <tr><td>Backend deployment</td><td><code>goals/backend-deployment-goal.md</code></td><td><span class="pill next">Blocked on host choice</span></td></tr>
  <tr><td>Design system</td><td><code>goals/design-system-capture-goal.md</code></td><td><span class="pill next">Needs capture</span></td></tr>
  <tr><td>BDS/Dolt tracking</td><td><code>goals/bds-dolt-tracking-goal.md</code></td><td><span class="pill done">CSV layer created</span></td></tr>
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
</table>
<h2>Evidence tables</h2>
<div class="card"><p>Tracking lives in <code>tracking/requirements.csv</code>, <code>tracking/tasks.csv</code>, <code>tracking/judges.csv</code>, <code>tracking/evidence.csv</code>, <code>tracking/decisions.csv</code>, <code>tracking/platform_snapshots.csv</code>, and <code>tracking/status_log.csv</code>.</p></div>
<p><a class="button" href="/goals">View Goals</a> <a class="button secondary" href="/roadmap">Roadmap</a></p>
"""
    return shell("Implementation Judges", body)


def roadmap_page() -> bytes:
    body = """
<h2>Roadmap</h2>
<table>
  <tr><th>Phase</th><th>Description</th><th>Status</th><th>Why it matters</th></tr>
  <tr><td>Local MVP</td><td>Signup, consent, database, admin, exports, Shopify context, tests.</td><td><span class="pill done">Built</span></td><td>Proves the workflow end-to-end without paid services.</td></tr>
  <tr><td>Shopify page launch</td><td>Create a real Shopify landing page and link to the owned hosted signup experience.</td><td><span class="pill next">Next</span></td><td>Fastest path to replacing the current Google Forms flow.</td></tr>
  <tr><td>Production hosting</td><td>Deploy backend to HTTPS, likely under <code>leads.bentondrones.com</code>.</td><td><span class="pill next">Next</span></td><td>Makes the MVP usable by real customers.</td></tr>
  <tr><td>Production database</td><td>Move from SQLite to PostgreSQL/PostGIS when volume and mapping needs justify it.</td><td><span class="pill next">Planned</span></td><td>Improves scale, backups, and geospatial analysis.</td></tr>
  <tr><td>Real geocoding</td><td>Add Nominatim, Census Geocoder, or another provider with caching.</td><td><span class="pill next">Planned</span></td><td>Converts addresses into reliable map points.</td></tr>
  <tr><td>Map UI</td><td>Add internal map view for leads, clusters, and service zones.</td><td><span class="pill next">Planned</span></td><td>Replaces manual Google Earth project creation over time.</td></tr>
  <tr><td>Shopify App Proxy</td><td>Prototype and validate native <code>bentondrones.com/apps/...</code> signup path.</td><td><span class="pill next">Later</span></td><td>Polishes UX after the simpler hosted path works.</td></tr>
  <tr><td>Notifications</td><td>Email/SMS confirmations and internal alerts.</td><td><span class="pill next">Optional</span></td><td>Improves customer communication and ops follow-up.</td></tr>
</table>

<h2>Production readiness checklist</h2>
<div class="grid">
  <div class="card"><h3>Must do</h3><ul><li>HTTPS</li><li>Production secrets</li><li>Backups</li><li>Privacy/consent legal review</li><li>Shopify landing page copy</li></ul></div>
  <div class="card"><h3>Should do</h3><ul><li>Real geocoder</li><li>PostgreSQL migration</li><li>Shared rate limiting</li><li>Monitoring/logging</li><li>Brand-matched styling</li></ul></div>
  <div class="card"><h3>Later</h3><ul><li>Shopify App Proxy</li><li>Map dashboard</li><li>Cluster editing UI</li><li>Email/SMS automations</li><li>Advanced reporting</li></ul></div>
</div>
"""
    return shell("MVP Roadmap", body)
