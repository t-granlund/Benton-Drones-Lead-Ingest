# ADR-001: Host the Benton Drones Lead-Ingest admin dashboard as static assets on Cloudflare Pages, gated by Cloudflare Access, with the dynamic API on Render

- **Status:** Proposed
- **Date:** 2026-08-17
- **Decider:** solutions-architect (for Pack Leader / Anderson sign-off)
- **Stakeholders to co-sign:** Security Auditor (STRIDE), Experience Architect (API contract/UX), Husky (implementation)

## Context and Problem Statement

Benton Drones Lead-Ingest currently runs as a single Python web service on Render
(`https://benton-drones-lead-ingest.onrender.com`), serving both the public signup form
and a password-login admin dashboard at `/admin-login` and `/admin`. Static docs/training
live separately on GitHub Pages (`t-granlund.github.io/Benton-Drones-Lead-Ingest`). The
team is moving nameserver control for `bentondrones.com` from Namecheap to Cloudflare.

Anderson needs the admin dashboard to be **non-indexed** and **login-protected**, and the
proposal is to host the admin UI as static assets on Cloudflare Pages while keeping the
dynamic Python API on Render.

### Primary evidence gathered (firsthand + authoritative docs)

- **Render is already fronted by Cloudflare.** Live response headers show
  `server: cloudflare`, `cf-ray`, `cf-cache-status: DYNAMIC`; Render's own docs confirm
  Cloudflare is Render's DDoS-protection provider.
- **The backend is a lightweight Python stdlib server** — `x-render-origin-server:
  BaseHTTP/0.6 Python/3.11.15`, and the 404 body is the stock `http.server` error template.
  There is no web framework, so CORS / CSRF / JWT validation must be hand-rolled.
- **No de-indexing today.** `/robots.txt` returns 404 and there is **no `X-Robots-Tag`
  header** on `/admin-login`; the admin surface is currently crawlable/indexable.
- **Render free-tier cold start observed firsthand:** ~14 s interstitial
  (request 10:07:56 → instance starting 10:08:10) before the app responds.
- **Render auto-issues and auto-renews TLS certs** (Let's Encrypt / Google Trust Services)
  for custom domains; Hobby plan includes 2 custom domains; the **onrender.com subdomain
  can be disabled** so the origin is reachable only via the custom domain (requests to the
  subdomain then 404 and never reach the service).
- **Cloudflare Access issues a signed JWT** in the `Cf-Access-Jwt-Assertion` header (and
  `CF_Authorization` cookie for browsers). Public keys live at
  `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs` (JWK `keys[]` + PEM
  `public_certs[]`); the signing key rotates every ~6 weeks (previous key valid 7 days);
  each app has an `AUD` tag validated via the `aud` claim, and `iss` =
  `https://<team>.cloudflareaccess.com`. A backend can verify this JWT to enforce the gate
  server-side (Cloudflare's own example uses the `jose` library; the Python equivalent is
  `PyJWT` with the JWKS).
- **Cloudflare SSL/TLS mode** governs both the visitor↔Cloudflare and Cloudflare↔origin
  legs. Cloudflare "strongly recommends Full or Full (strict)". Flexible encrypts only the
  first leg and leaves Cloudflare↔origin in plaintext (insecure). Full (strict) validates
  the origin certificate — valid here because Render presents a valid cert.
- **Cloudflare Pages `_headers`** can set `X-Robots-Tag: noindex` on static asset responses
  (the docs use exactly this as an example), **but `_headers` rules do NOT apply to
  responses from Pages Functions / advanced-mode `_worker.js`** — those must set headers
  in worker code.

## Decision Drivers

1. Anderson must have a **login-protected, non-indexed** admin dashboard (privacy is a
   hard requirement, not a "nice to have").
2. Minimize operational cost — the team is on Render Hobby (free) + GitHub Pages (free);
   Cloudflare Pages and Cloudflare Access (Zero Trust Free) are free for a small team.
3. Preserve the existing Python API and Neon Postgres pipeline; avoid a backend rewrite.
4. Reduce the cold-start penalty on admin UX (the UI shell should load instantly).
5. Keep the architecture auditable: one Cloudflare zone (`bentondrones.com`) for DNS,
   Pages, Access, and the proxied Render origin.
6. Defense in depth: the auth gate must hold even if a URL leaks or the origin is hit
   directly.

## Considered Options

### Option A — Status quo (admin UI + API on Render, password login)
- Pros: zero migration; nothing new.
- Cons: admin UI inherits ~14 s cold starts; password login is a shared secret (phishable,
  no MFA, no SSO); no `X-Robots-Tag`/`robots.txt` today (indexable); no edge logging/SSO.
- Score: 2/5.

### Option B — Static admin UI on Cloudflare Pages + Cloudflare Access gate + Render API validates Access JWT (RECOMMENDED)
- The admin UI ships as static assets (HTML/CSS/JS) on Pages at `admin.bentondrones.com`
  (or `dashboard.bentondrones.com`), built from the same repo. Pages serves the shell
  globally with no cold start. The UI calls the Python API at `leads.bentondrones.com`
  (CNAME → Render, orange-cloud proxied). Cloudflare Access protects the Pages hostname
  AND the API hostname. The Render API additionally validates the `Cf-Access-Jwt-Assertion`
  JWT server-side. The `onrender.com` subdomain is disabled so the origin is reachable only
  via the Cloudflare-fronted custom domain.
- Pros: instant UI (no cold start for the shell); Access replaces the password with
  Google OAuth / one-time PIN (MFA-capable, audited); JWT verification gives defense in
  depth; noindex is trivial via `_headers`; single Cloudflare zone; free tier.
- Cons: introduces cross-origin (CORS) between the Pages UI and the Render API; requires
  a cookie/session strategy that survives cross-subdomain + CSRF protection; needs JWT
  verification code added to the minimal Python server; Access key rotation must be
  handled (fetch JWKS, don't hardcode).
- Score: 4.5/5.

### Option C — Static admin UI on Cloudflare Pages + keep password login on Render (no Access)
- Split UI/API but leave the existing password login in place on the API.
- Pros: avoids introducing Access/JWT; still gets instant UI.
- Cons: keeps a phishable shared-secret login; the password page itself still cold-starts
  on Render; no SSO/MFA; weakest privacy posture of the split options.
- Score: 3/5.

### Option D — Don't split: keep the monolith on Render, put Cloudflare Access in front of the proxied origin
- CNAME `admin.bentondrones.com` → Render (orange cloud), put an Access application on that
  hostname, disable the `onrender.com` subdomain, verify the Access JWT server-side, add
  `X-Robots-Tag` noindex via Cloudflare Transform Rules or in the Python app.
- Pros: **no CORS, no cookie cross-origin, no UI/API split** — simplest correct answer;
  Access still replaces the password and the JWT still verifies server-side.
- Cons: the admin HTML shell still loads from Render, so the first authenticated load
  still cold-starts (~14 s) — worse admin UX than Option B.
- Score: 4/5 (best "low-effort" alternative; pick this if you want to avoid CORS entirely).

## Decision Outcome

**Adopt Option B** (static UI on Pages + Access + server-side JWT validation on Render),
with **Option D documented as the fallback** if the team prefers to avoid CORS/cookie
complexity. The UI/API split is justified primarily by (a) instant admin shell load and
(b) clean separation of static vs. dynamic concerns; the trade-off is a small, well-understood
CORS + CSRF surface that is fully mitigable (see Risks).

### Consequences

**Good**
- Admin UI loads instantly from Cloudflare's edge; only data fetches cold-start on Render.
- Cloudflare Access replaces the shared password with Google OAuth / one-time PIN
  (MFA-capable, per-user auditable). Free for a small team.
- `X-Robots-Tag: noindex` + `robots.txt` Disallow make the surface non-indexable; Access
  makes it non-accessible without identity — the actual privacy control.
- Single Cloudflare zone (`bentondrones.com`) holds DNS, Pages, Access, and the proxied
  Render origin. SSL mode Full (strict) end-to-end; Render cert auto-renews.
- Disabling the `onrender.com` subdomain + server-side JWT verification closes the
  direct-origin-bypass risk.

**Bad**
- New CORS surface (Pages UI → Render API) requires `Access-Control-Allow-Origin` scoped to
  the admin origin, `Allow-Credentials: true`, and a cookie strategy that works cross-subdomain.
- CSRF protection must be added (the stdlib server has none today): SameSite + custom
  header + Origin/Referer check, or a double-submit/HMAC token minted by a Pages Function.
- JWT verification code must be added to the minimal Python server (PyJWT + JWKS fetch,
  `kid` matching, `iss`/`aud`/`exp` checks, key-rotation refresh).
- Access signing-key rotation every ~6 weeks requires the backend to refresh JWKS (cache
  with short TTL; previous key valid 7 days provides a buffer).
- Render free-tier cold starts still affect API calls (mitigations below).

**Neutral**
- Two deploy targets (Pages for UI, Render for API) instead of one — both are git-driven.
- The public signup form stays on Render (unchanged); only the admin UI moves to Pages.

## STRIDE Security Analysis

| Threat | Vector in this design | Mitigation |
|---|---|---|
| **Spoofing** | Attacker forges a `Cf-Access-Jwt-Assertion` to impersonate an admin; or spoofs the Pages origin. | Render API verifies the JWT signature against the team JWKS (`<team>.cloudflareaccess.com/cdn-cgi/access/certs`), checks `iss`, `aud` (app AUD tag), and `exp`. Access itself authenticates the user via Google OTP/one-time PIN. TLS (Full strict) prevents origin spoofing. |
| **Tampering** | Attacker modifies a request body or an API response in transit; tampered static asset. | HTTPS end-to-end (Full strict). Pages integrity via Cloudflare; API responses signed by TLS. State-changing API calls require a CSRF token / custom header + Origin check, so a tampered cross-site request is rejected. |
| **Repudiation** | Admin denies an action (export/delete). | Cloudflare Access logs every access event (Zero Trust → Logs → Access authentication logs). The API should also write an audit row per mutating action keyed to the Access `sub`/email claim from the JWT. |
| **Information Disclosure** | Admin URL leaks and is indexed; lead PII returned to an unauthenticated caller; API error messages leak internals. | Access blocks unauthenticated access (no PII without identity). `X-Robots-Tag: noindex` + `robots.txt` Disallan reduce indexing. Server-side JWT check means even a leaked URL yields no data. API returns generic errors; `X-Frame-Options: DENY` (already present) prevents clickjacking disclosure. |
| **Denial of Service** | Render free instance sleeps and slow-wakes; attacker floods the API. | UI shell on Pages is always-on (no DoS there). Render cold start is a latency issue, not a crash. Cloudflare's edge (rate limiting / DDoS) sits in front of the API. For predictable latency, keep the Render instance warm (cron ping) or upgrade to a paid always-on instance. |
| **Elevation of Privilege** | Attacker reaches the origin directly bypassing Access, or escalates from public signup to admin. | Disable the `onrender.com` subdomain (origin reachable only via the Cloudflare-fronted custom domain). Server-side JWT verification means even a direct hit on the custom domain without a valid Access token is rejected. Separate public signup routes (no JWT required) from `/admin/*` API routes (JWT required) with an explicit allowlist. |

## Fitness Functions (pytest, `tests/architecture/`)

```python
# tests/architecture/test_admin_architecture.py
# Run against the deployed architecture. Mark with @pytest.mark.architecture.
import httpx, base64, json, os, re

PAGES_URL = os.environ["ADMIN_PAGES_URL"]      # https://admin.bentondrones.com
API_URL    = os.environ["ADMIN_API_URL"]       # https://leads.bentondrones.com
TEAM       = os.environ["CF_ACCESS_TEAM"]      # <team>.cloudflareaccess.com
AUD        = os.environ["CF_ACCESS_AUD"]

def test_admin_pages_serve_noindex():
    r = httpx.get(PAGES_URL, follow_redirects=True)
    assert r.status_code == 200
    assert "noindex" in r.headers.get("x-robots-tag", "").lower()

def test_robots_disallows_admin():
    r = httpx.get(PAGES_URL.rstrip("/") + "/robots.txt")
    assert r.status_code == 200
    assert re.search(r"Disallow:\s*/", r.text)

def test_access_gate_blocks_unauthenticated():
    r = httpx.get(PAGES_URL, follow_redirects=False)
    # Access redirects to the IdP or returns 302/403 without a valid CF_Authorization cookie.
    assert r.status_code in (302, 403)
    assert "cloudflareaccess" in r.headers.get("location", "") or r.status_code == 403

def test_api_rejects_missing_jwt():
    r = httpx.get(API_URL + "/admin/leads", headers={"origin": PAGES_URL})
    assert r.status_code in (401, 403)

def test_api_rejects_tampered_jwt():
    bogus = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b'=').decode() + ".."
    r = httpx.get(API_URL + "/admin/leads", headers={"cf-access-jwt-assertion": bogus})
    assert r.status_code in (401, 403)

def test_api_cors_origin_is_scoped_not_wildcard():
    r = httpx.options(API_URL + "/admin/leads", headers={
        "origin": PAGES_URL, "access-control-request-method": "GET"})
    acao = r.headers.get("access-control-allow-origin", "")
    assert acao == PAGES_URL            # never "*"
    assert r.headers.get("access-control-allow-credentials") == "true"

def test_onrender_subdomain_disabled():
    r = httpx.get("https://benton-drones-lead-ingest.onrender.com/admin",
                  follow_redirects=False, timeout=15)
    assert r.status_code == 404         # origin not directly reachable

def test_no_legacy_password_login_fallback():
    # The old /admin-login password flow must not grant access in the new architecture.
    r = httpx.post(API_URL + "/admin-login", data={"password": "anything"},
                   follow_redirects=False)
    assert r.status_code in (401, 403, 404)
```

> Note: a `test_ssl_mode_full_strict` check can be added once the Cloudflare API token is
> available — query the zone SSL setting and assert it equals `strict`.

## Step-by-step architecture proposal (Option B)

1. **Move nameservers** for `bentondrones.com` from Namecheap to Cloudflare (full DNS
   export first; Cloudflare scans existing records). Verify no `AAAA` records remain for
   the Render-bound host (Render is IPv4).
2. **Create the Cloudflare Pages project** for the admin UI. Connect the GitHub repo, set
   the build output dir, and add a `robots.txt` (`User-agent: *` / `Disallow: /`) plus a
   `_headers` file:
   ```
   /*
     X-Robots-Tag: noindex, nofollow
     X-Content-Type-Options: nosniff
     X-Frame-Options: DENY
     Referrer-Policy: no-referrer
   ```
   (If you later add an advanced-mode `_worker.js`, set `X-Robots-Tag` inside the worker
   response instead — `_headers` does not apply to Function responses.)
3. **Map the Pages custom domain** `admin.bentondrones.com` (same Cloudflare account →
   auto-provisioned DNS/Cert). Keep this hostname orange-cloud.
4. **Add the Render custom domain** `leads.bentondrones.com` in Render (Settings → Custom
   Domains). Render will issue/renew the Let's Encrypt cert. CNAME it to the service's
   onrender.com subdomain. **Disable the onrender.com subdomain** in Render settings so the
   origin is reachable only via the custom domain.
5. **Set the zone SSL/TLS mode to Full (strict)** (Cloudflare → SSL/TLS → Origin Server).
   Render presents a valid cert, so strict validation passes. Avoid Flexible (plaintext to
   origin). Keep the apex/root record on gray cloud if you only use subdomains (per Render's
   wildcard caveat).
6. **Enable Cloudflare Zero Trust (Free)**, create the team domain
   (`<team>.cloudflareaccess.com`), and add an identity provider — **Google OAuth** and/or
   **one-time PIN (OTP email)** for Anderson (1–2 admins). (Free tier: historically up to
   50 users — confirm the current seat count at signup; OTP and Google/GitHub are free,
   SAML/SCIM are paid.)
7. **Create two Access applications** (Access → Applications → Add → Self-hosted):
   - App 1: `admin.bentondrones.com` (the Pages UI) — policy: allow Anderson's email(s).
   - App 2: `leads.bentondrones.com` (the API) — same allow policy; copy each app's **AUD tag**.
   Access sits in front of both hostnames; unauthenticated requests are redirected to login.
8. **Add JWT verification to the Render Python API** (the minimal stdlib server): fetch the
   JWKS from `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs`, verify the
   `Cf-Access-Jwt-Assertion` header signature (RS256) via PyJWT, match the JWT `kid` to
   `public_certs[]`, check `iss == https://<team>.cloudflareaccess.com`, `aud == <AUD tag>`,
   `exp` not passed. Refresh the JWKS on a short TTL (key rotates ~6 weeks; previous key
   valid 7 days). Apply this middleware to all `/admin/*` API routes; leave public signup
   routes open.
9. **CORS on the API**: return `Access-Control-Allow-Origin: https://admin.bentondrones.com`
   (never `*`), `Access-Control-Allow-Credentials: true`, and handle OPTIONS preflight.
10. **Session/cookie + CSRF**: Prefer a **stateless bearer model** — the UI holds the
    Access-issued identity and sends the Access JWT (or a short-lived HMAC-signed token
    minted by a Pages Function) as a bearer header on API calls, avoiding cross-subdomain
    cookie complications entirely. If a session cookie is required, set it `SameSite=Lax`,
    `Secure`, `__Host-`-scoped where possible, and pair it with a CSRF token (double-submit
    or HMAC) plus an Origin/Referer check on every state-changing request.
11. **Remove the legacy password login** from `/admin` once Access + JWT verification are
    verified end-to-end; keep the public signup flow unchanged.
12. **Audit logging**: rely on Zero Trust Access authentication logs; additionally write an
    audit row in Neon for every mutating admin action, keyed to the JWT `sub`/email.
13. **Warm the Render instance** (optional): a cron-based keep-alive ping every ~10 minutes
    to `leads.bentondrones.com` (health route) to avoid free-tier sleep, or upgrade Render to
    a paid always-on instance if sub-15 s data-load latency matters to Anderson.

## Research References

- Primary observation: `https://benton-drones-lead-ingest.onrender.com/admin-login` —
  headers (`server: cloudflare`, `x-render-origin-server: BaseHTTP/0.6 Python/3.11.15`,
  no `X-Robots-Tag`), `/robots.txt` 404, ~14 s free cold start, `/admin` redirect.
- Render docs — Custom Domains: https://render.com/docs/custom-domains
  (managed TLS auto-renew; Hobby = 2 domains; disable onrender subdomain; Cloudflare
  orange-cloud caveat for wildcard+root).
- Cloudflare docs — Validate JWTs:
  https://developers.cloudflare.com/cloudflare-one/identity/authorization-cookie/validating-json/
  (`Cf-Access-Jwt-Assertion`, certs endpoint, key rotation, AUD tag, `jose` example).
- Cloudflare docs — Account limits:
  https://developers.cloudflare.com/cloudflare-one/account-limits/
  (Access apps 500, IdPs 50, service tokens 50; confirms "Zero Trust Free" tier).
- Cloudflare docs — SSL/TLS encryption modes:
  https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/
  (Full / Full strict recommended; Flexible insecure).
- Cloudflare docs — Pages `_headers`:
  https://developers.cloudflare.com/pages/configuration/headers/
  (`X-Robots-Tag: noindex` example; caveat: not applied to Pages Functions/`_worker.js`).
- GitHub Pages docs hub (confirmed): https://t-granlund.github.io/Benton-Drones-Lead-Ingest/
- Note: web-puppy research dossier was unavailable (sub-agent model misconfiguration); all
  evidence above was gathered directly via the browser by solutions-architect.
