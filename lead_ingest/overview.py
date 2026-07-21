from __future__ import annotations

from lead_ingest.branded_template import LOGO_URL


def overview_page() -> bytes:
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Benton Drones Lead Ingest MVP Overview</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --olive: #809948;
      --olive-dark: #6f853d;
      --olive-deep: #5a6f30;
      --md-sys-color-primary: #809948;
      --md-sys-color-on-primary: #ffffff;
      --md-sys-color-primary-container: #f0f7f4;
      --md-sys-color-secondary: #6184d8;
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
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin:0; font-family:'Jost',sans-serif; font-weight:500; letter-spacing:0.02rem;
      color:#1b1b1b; background:var(--md-sys-color-background); line-height:1.65;
      font-size:1.05rem; -webkit-font-smoothing:antialiased;
    }
    /* Hero — logo, eyebrow, title, subtitle */
    .hero {
      background:linear-gradient(135deg, var(--olive) 0%, var(--olive-dark) 100%);
      color:#fff; padding:64px 24px 72px; text-align:center;
      box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }
    .hero-inner { max-width:860px; margin:0 auto; }
    .hero img {
      height:60px; width:auto; margin-bottom:20px;
      filter:drop-shadow(0 2px 6px rgba(0,0,0,.22));
      transition:transform 0.2s ease, opacity 0.2s ease;
    }
    .hero img:hover { transform:scale(1.03); opacity:0.92; }
    .hero .eyebrow {
      display:block; margin-bottom:14px;
      font-size:0.75rem; font-weight:700; text-transform:uppercase;
      letter-spacing:0.14em; opacity:0.82;
    }
    .hero h1 { margin:0 0 14px; font-size:2.4rem; font-weight:700; letter-spacing:0.01rem; line-height:1.15; }
    .hero .subtitle { max-width:780px; margin:0 auto; font-size:1.1rem; font-weight:500; opacity:0.92; line-height:1.55; }
    main { max-width:1080px; margin:0 auto; padding:48px 24px 80px; }
    h2 {
      margin-top:48px; padding-bottom:8px; color:var(--md-sys-color-primary);
      font-size:1.7rem; font-weight:700; letter-spacing:0.01rem; line-height:1.2;
      border-bottom:1px solid var(--md-sys-color-outline);
    }
    h3 { margin-bottom:8px; color:var(--md-sys-color-primary); font-size:1.3rem; font-weight:600; line-height:1.3; }
    a { color:var(--md-sys-color-secondary); text-decoration:none; transition:opacity 0.2s ease; }
    a:hover { text-decoration:underline; opacity:0.88; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:24px; }
    .card {
      background:var(--md-sys-color-surface); border:1px solid var(--md-sys-color-outline);
      border-top:4px solid var(--md-sys-color-primary);
      border-radius:16px; padding:28px; box-shadow:var(--el-1);
      transition:transform 0.22s ease, box-shadow 0.22s ease;
    }
    .card:hover { transform:translateY(-2px); box-shadow:var(--el-2); }
    .status { display:inline-block; border-radius:999px; padding:6px 14px; font-weight:700; font-size:0.78rem; letter-spacing:0.08rem; text-transform:uppercase; border:1.5px solid; }
    .done { color:#3d4d1f; background:var(--md-sys-color-primary-container); border-color:var(--md-sys-color-primary); }
    .next { color:#8a4a00; background:#fffce7; border-color:#e8893a; }
    .risk { color:#8e1c1c; background:var(--md-sys-color-error-container); border-color:var(--md-sys-color-error); }
    .info { color:#1a2a5a; background:#e7ecff; border-color:var(--md-sys-color-secondary); }
    code, pre { font-family:ui-monospace,SFMono-Regular,Consolas,Menlo,monospace; font-size:0.9rem; letter-spacing:0; }
    code { background:var(--md-sys-color-surface-container-low); border:1px solid var(--md-sys-color-outline); border-radius:6px; padding:2px 6px; }
    pre { background:#1b1b1b; color:#e5e7eb; border-radius:10px; padding:16px; overflow:auto; }
    table { width:100%; border-collapse:collapse; background:var(--md-sys-color-surface); border:1px solid var(--md-sys-color-outline); border-radius:12px; overflow:hidden; box-shadow:var(--el-1); }
    th, td { padding:16px 18px; border-bottom:1px solid var(--md-sys-color-outline-variant); text-align:left; vertical-align:top; }
    th { background:var(--md-sys-color-surface-container); color:var(--olive-deep); font-weight:700; font-size:0.78rem; letter-spacing:0.08rem; text-transform:uppercase; }
    tr:last-child td { border-bottom:none; }
    tr:hover td { background:var(--md-sys-color-surface-container-low); }
    .flow { font-family:ui-monospace,SFMono-Regular,Consolas,monospace; white-space:pre-wrap; }
    .small { color:var(--md-sys-color-on-surface-variant); font-size:0.95rem; }
    ul, ol { padding-left:20px; }
    li { margin-bottom:10px; }
    @media (max-width:600px) {
      .hero { padding:48px 16px 56px; }
      .hero h1 { font-size:1.8rem; }
      .hero .subtitle { font-size:1rem; }
      main { padding:32px 16px 64px; }
      h2 { font-size:1.4rem; }
    }
    @media (prefers-reduced-motion: reduce) { * { transition:none !important; animation:none !important; } .card:hover { transform:none; } }
  </style>
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <img src="__LOGO__" alt="Benton Drones logo" loading="lazy">
    <span class="eyebrow">Benton Drones</span>
    <h1>Lead Ingest MVP</h1>
    <p class="subtitle">A Shopify-aware, self-owned local system for collecting drone delivery simulation signups, consent, addresses, exports, and planning data without depending on Google Forms, PDFfiller, Sheets, or manual Google Earth workflows.</p>
  </div>
</header>
<main>
  <section class="grid">
    <div class="card"><span class="status info">Review pages</span><h3>Project cockpit</h3><p>Use these local pages to review the MVP, easiest Shopify launch path, change history, and roadmap.</p><p><strong><a href="/current-state">Current State & Next Steps</a></strong></p><p><a href="/shopify-preview">Shopify Preview</a> &middot; <a href="/domain-setup">Domain Setup</a> &middot; <a href="/api-preflight">API/CLI Preflight</a> &middot; <a href="/goals">Goals</a> &middot; <a href="/judges">Judges</a> &middot; <a href="/changelog">Changelog</a> &middot; <a href="/roadmap">Roadmap</a></p></div>
    <div class="card"><span class="status done">Built</span><h3>Signup + Consent</h3><p>Public signup form stores contact, address, campaign, Shopify context, and versioned consent records in SQLite.</p></div>
    <div class="card"><span class="status done">Built</span><h3>Shopify-Aware</h3><p>Can capture Shopify storefront context and includes HMAC/signature utilities for app proxy validation.</p></div>
    <div class="card"><span class="status done">Built</span><h3>Admin Protection</h3><p>Admin and export routes require password login and signed session cookies.</p></div>
    <div class="card"><span class="status done">Built</span><h3>Exports</h3><p>CSV, GeoJSON, and KML exports support spreadsheet, mapping, and Google Earth migration workflows.</p></div>
  </section>

  <h2>Executive Summary</h2>
  <div class="card">
    <p>This MVP proves the core owned workflow: a visitor signs up, consent is captured, the address is geocoded locally with a mock provider, data is stored in an owned SQLite database, and internal users can view/export leads after admin login.</p>
    <p>Shopify remains the storefront/presentation layer. The owned backend remains the source of truth for sensitive lead, consent, address, geospatial, and planning data.</p>
  </div>

  <h2>How the System Works</h2>
  <div class="card flow">Shopify page / app proxy / signup link
        |
        v
Public signup form with consent + CSRF + honeypot
        |
        v
Server-side validation
        |
        v
SQLite database
  |----------------------|----------------------|
  v                      v                      v
Signup record       Consent record        Geocode status
        |
        v
Admin dashboard + protected exports
  |--------------|--------------|
  v              v              v
CSV          GeoJSON          KML</div>

  <h2>Local Routes</h2>
  <table>
    <tr><th>Route</th><th>Audience</th><th>Purpose</th><th>Status</th></tr>
    <tr><td><code>/overview</code></td><td>Internal/project</td><td>This plain-English system overview.</td><td><span class="status done">Built</span></td></tr>
    <tr><td><code>/signup</code></td><td>Public</td><td>Default signup page.</td><td><span class="status done">Built</span></td></tr>
    <tr><td><code>/signup/&lt;variant&gt;</code></td><td>Public</td><td>Campaign/neighborhood/partner signup variant.</td><td><span class="status done">Built</span></td></tr>
    <tr><td><code>/admin-login</code></td><td>Internal</td><td>Password login for protected admin/export access.</td><td><span class="status done">Built</span></td></tr>
    <tr><td><code>/admin</code></td><td>Internal</td><td>Lead dashboard and export links.</td><td><span class="status done">Built</span></td></tr>
    <tr><td><code>/export/csv</code></td><td>Internal</td><td>Spreadsheet-style export.</td><td><span class="status done">Built</span></td></tr>
    <tr><td><code>/export/geojson</code></td><td>Internal</td><td>Modern web map/GIS export.</td><td><span class="status done">Built</span></td></tr>
    <tr><td><code>/export/kml</code></td><td>Internal</td><td>Google Earth compatible export.</td><td><span class="status done">Built</span></td></tr>
  </table>

  <h2>What Is Built</h2>
  <div class="grid">
    <div class="card"><h3>Data Ownership</h3><ul><li>SQLite database</li><li>Signup records</li><li>Consent records</li><li>Shopify context fields</li><li>Cluster tables ready</li></ul></div>
    <div class="card"><h3>Security Basics</h3><ul><li>Server-side validation</li><li>Required consent</li><li>Admin password login</li><li>Signed session cookies</li><li>CSRF tokens</li><li>Honeypot spam trap</li></ul></div>
    <div class="card"><h3>Planning Data</h3><ul><li>Mock local geocoder</li><li>Latitude/longitude fields</li><li>Haversine distance utility</li><li>Radius clustering utility</li><li>CSV/GeoJSON/KML exports</li></ul></div>
    <div class="card"><h3>Shopify Fit</h3><ul><li>Shop domain capture</li><li>Customer ID capture</li><li>Page URL capture</li><li>App proxy HMAC helpers</li><li>Signed context token handoff</li></ul></div>
  </div>

  <h2>Current Local Setup</h2>
  <pre>python scripts/init_db.py
ADMIN_PASSWORD=change-me ADMIN_SESSION_SECRET=change-me-too python -m lead_ingest.server</pre>
  <p class="small">On Windows PowerShell, set environment variables with <code>$env:ADMIN_PASSWORD='change-me'</code> and <code>$env:ADMIN_SESSION_SECRET='change-me-too'</code> before starting the server.</p>

  <h2>Roadmap</h2>
  <table>
    <tr><th>Phase</th><th>What It Means</th><th>Status</th></tr>
    <tr><td>Local MVP</td><td>Owned signup, consent, admin, exports, Shopify context, and tests.</td><td><span class="status done">Mostly complete</span></td></tr>
    <tr><td>Production Shopify Integration</td><td>Choose Shopify page link, iframe/theme section, or app proxy. Validate exact Shopify app proxy signing rules against current Shopify docs.</td><td><span class="status next">Next</span></td></tr>
    <tr><td>Real Geocoding</td><td>Replace mock geocoding with Nominatim, US Census Geocoder, or another provider using caching and provider abstraction.</td><td><span class="status next">Next</span></td></tr>
    <tr><td>Mapping UI</td><td>Add a visual map for leads and clusters using Leaflet/MapLibre or future frontend stack.</td><td><span class="status next">Planned</span></td></tr>
    <tr><td>Production Database</td><td>Move from SQLite to PostgreSQL/PostGIS when deployed beyond local MVP.</td><td><span class="status next">Planned</span></td></tr>
    <tr><td>Notifications</td><td>Email/SMS confirmations and internal alerts after signup.</td><td><span class="status next">Optional</span></td></tr>
  </table>

  <h2>Known Production Risks</h2>
  <div class="card">
    <ul>
      <li><strong>HTTPS is required</strong> before production cookies or Shopify app proxy use.</li>
      <li><strong>Secure cookie flag</strong> should be enabled behind HTTPS.</li>
      <li><strong>Rate limiting is local-memory only</strong> and should be upgraded for multi-process/cloud deployments.</li>
      <li><strong>Consent language needs legal review.</strong> The software stores audit data; it does not provide legal advice.</li>
      <li><strong>Shopify app proxy HMAC canonicalization</strong> should be verified against current Shopify docs before launch.</li>
    </ul>
  </div>

  <h2>Plain-English Bottom Line</h2>
  <div class="card">
    <p>The MVP now demonstrates the end-to-end workflow Benton Drones needs: collect leads, capture consent, store data in an owned database, preserve Shopify compatibility, protect internal data, and export planning data for operational use.</p>
    <p>The next leap is not more random features. The next leap is choosing the Shopify integration mode and deploying a hardened version with HTTPS, production secrets, real geocoding, and a production database.</p>
  </div>
</main>
</body>
</html>"""
    return html.replace("__LOGO__", LOGO_URL).encode("utf-8")
