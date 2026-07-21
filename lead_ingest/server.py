from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import os
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from lead_ingest.auth import (
    authenticate_password,
    create_session_token,
    expired_session_cookie,
    parse_cookie,
    session_cookie,
    verify_session_token,
)
from lead_ingest.branded_template import LOGO_URL, branded_page
from lead_ingest.db import (
    DEFAULT_DB_PATH,
    analytics_summary,
    connect,
    create_signup,
    get_consent_record,
    get_export_rows,
    get_jira_queue_entry,
    get_jira_ticket,
    get_signature_record,
    get_signup,
    get_variant,
    init_db,
    list_signups,
    mark_jira_ticket_created,
    queue_jira_ticket,
    recent_leads,
)
from lead_ingest.jira import (
    JiraApiError,
    JiraConfigError,
    create_jira_ticket,
    jira_config_from_env,
    jira_issue_url,
)
from lead_ingest.pdf import render_signup_html, try_render_pdf
from lead_ingest.exports import export_csv, export_geojson, export_kml
from lead_ingest.models import CONSENT_TEXT, SIGNATURE_DISCLAIMER, WAIVER_TEXT, SignupInput
from lead_ingest.overview import overview_page
from lead_ingest.project_pages import (
    api_preflight_page,
    changelog_page,
    current_state_page,
    domain_setup_page,
    goals_page,
    judges_page,
    roadmap_page,
    shopify_preview_page,
)
from lead_ingest.request_security import RateLimiter, create_csrf_token, verify_csrf_token
from lead_ingest.shopify_security import (
    context_from_params,
    sign_context,
    verify_context_token,
    verify_hmac,
)
from lead_ingest.validation import ValidationError

HOST = "127.0.0.1"
PORT = 8000
VERSION = "0.2.0"
MAX_BODY_BYTES = 65_536  # 64 KB
STATIC_ROOT = Path(__file__).resolve().parent.parent / "static"
RATE_LIMITER = RateLimiter(max_requests=20, window_seconds=60)
WEAK_PASSWORDS = {"change-me", "testpass", "password", "admin", ""}

logger = logging.getLogger("lead_ingest.server")


def page(title: str, body: str) -> bytes:
    return branded_page(title, body)


def _derive_dev_secret(purpose: str) -> str:
    """Derive a deterministic dev-only secret from ADMIN_PASSWORD via PBKDF2.

    Not secure for production, but far better than a hardcoded constant.
    Returns "" when ADMIN_PASSWORD is unset (token creation will fail safely).
    """
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password:
        return ""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        f"benton-drones-{purpose}".encode(),
        100_000,
    ).hex()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        if os.environ.get("QUIET_HTTP_LOGS") == "1":
            return
        logger.info("%s - %s", self.address_string(), format % args)

    def handle(self):
        self._db_conns = []
        try:
            super().handle()
        finally:
            for conn in getattr(self, "_db_conns", []):
                try:
                    conn.close()
                except Exception:
                    pass

    def serve_static(self, path: str) -> None:
        relative = path.removeprefix("/static/")
        file_path = (STATIC_ROOT / relative).resolve()
        if not file_path.is_relative_to(STATIC_ROOT.resolve()):
            self.send_error(403)
            return
        if not file_path.is_file():
            self.send_error(404)
            return
        content_type, _ = mimetypes.guess_type(str(file_path))
        if content_type is None:
            content_type = "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in {"/", "/signup"} or path.startswith("/signup/"):
            self.respond_html(self.signup_page(path))
        elif path == "/overview":
            self.respond_html(overview_page())
        elif path == "/shopify-preview":
            self.respond_html(shopify_preview_page())
        elif path == "/changelog":
            self.respond_html(changelog_page())
        elif path == "/roadmap":
            self.respond_html(roadmap_page())
        elif path == "/domain-setup":
            self.respond_html(domain_setup_page())
        elif path == "/api-preflight":
            self.respond_html(api_preflight_page())
        elif path == "/current-state":
            self.respond_html(current_state_page())
        elif path == "/goals":
            self.respond_html(goals_page())
        elif path == "/judges":
            self.respond_html(judges_page())
        elif path == "/admin-login":
            self.respond_html(self.login_page())
        elif path == "/admin-logout":
            self.respond_redirect("/admin-login", [expired_session_cookie(secure=self._cookie_secure())])
        elif path == "/healthz":
            self.handle_healthz()
        elif path == "/landing-page.html":
            self.serve_static("/static/landing-page.html")
        elif path.startswith("/static/"):
            self.serve_static(path)
        elif path == "/admin":
            if not self.require_admin_html():
                return
            self.respond_html(self.admin_page())
        elif path.startswith("/admin/lead/") and path.endswith("/print"):
            if not self.require_admin_html():
                return
            lead_id = path.rsplit("/", 2)[1]
            self.respond_html(self.lead_print_page(lead_id))
        elif path.startswith("/admin/lead/") and path.endswith("/pdf"):
            if not self.require_admin_html():
                return
            lead_id = path.rsplit("/", 2)[1]
            self.handle_lead_pdf(lead_id)
        elif path.startswith("/admin/lead/"):
            if not self.require_admin_html():
                return
            lead_id = path.split("/")[-1]
            self.respond_html(self.lead_detail_page(lead_id))
        elif path == "/admin/leads.geojson":
            if not self.require_admin_export():
                return
            self.respond_text(
                export_geojson(self.geocoded_leads()),
                "application/geo+json",
            )
        elif path == "/export/csv":
            if not self.require_admin_export():
                return
            self.respond_text(export_csv(get_export_rows(self.conn())), "text/csv")
        elif path == "/export/geojson":
            if not self.require_admin_export():
                return
            self.respond_text(export_geojson(list_signups(self.conn())), "application/geo+json")
        elif path == "/export/kml":
            if not self.require_admin_export():
                return
            self.respond_text(export_kml(list_signups(self.conn())), "application/vnd.google-earth.kml+xml")
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path not in {"/signup", "/admin-login"}:
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.respond_text("Invalid Content-Length", "text/plain", 400)
            return
        if length > MAX_BODY_BYTES:
            self.close_connection = True
            # Drain a bounded amount so the socket stream stays clean.
            self.rfile.read(min(length, MAX_BODY_BYTES))
            self.respond_text("Request body too large", "text/plain", 413)
            return
        payload = self.rfile.read(length).decode("utf-8")
        form = {key: values[0] for key, values in parse_qs(payload).items()}
        if not self.allow_request(path):
            self.respond_text("Too many requests", "text/plain", 429)
            return
        if path == "/admin-login":
            self.handle_login(form)
            return
        if form.get("website_url", ""):
            self.respond_html(self.signup_page("/signup", ["submission rejected"]), 400)
            return
        if not self.valid_csrf(form, "signup"):
            self.respond_html(self.signup_page("/signup", ["invalid CSRF token"]), 400)
            return
        secret = os.environ.get("SHOPIFY_APP_SECRET", "")
        shopify_fields = self.shopify_fields_from_form(form, secret)
        if shopify_fields is None:
            self.respond_html(self.signup_page("/signup", ["invalid Shopify context token"]), 400)
            return

        data = SignupInput(
            first_name=form.get("first_name", ""),
            last_name=form.get("last_name", ""),
            email=form.get("email", ""),
            phone=form.get("phone", ""),
            address_line1=form.get("address_line1", ""),
            address_line2=form.get("address_line2", ""),
            city=form.get("city", ""),
            state=form.get("state", ""),
            postal_code=form.get("postal_code", ""),
            notes=form.get("notes", ""),
            campaign=form.get("campaign", ""),
            source=form.get("source", ""),
            variant_slug=form.get("variant_slug", "default"),
            shopify_shop_domain=shopify_fields["shopify_shop_domain"],
            shopify_customer_id=shopify_fields["shopify_customer_id"],
            shopify_page_url=shopify_fields["shopify_page_url"],
            consent_accepted=form.get("consent_accepted") == "yes",
            waiver_accepted=form.get("waiver_accepted") == "yes",
            typed_name=form.get("typed_name", ""),
        )
        try:
            conn = self.conn()
            signup_id = create_signup(
                conn, data, self.client_address[0], self.headers.get("User-Agent", "")
            )
        except ValidationError as exc:
            self.respond_html(self.signup_page("/signup", exc.errors), 400)
            return

        # Attempt JIRA ticket creation; queue locally if unavailable.
        self.try_create_jira_ticket(conn, signup_id)

        self.respond_html(
            branded_page(
                "Signup complete",
                "<div class='card success'><h1>Thanks!</h1><p>Your signup was saved.</p><a class='button' href='/admin'>View admin</a> <a class='button' href='/overview'>View overview</a></div>",
            )
        )

    def conn(self):
        if not hasattr(self, "_db_conns"):
            self._db_conns = []
        conn = connect(DEFAULT_DB_PATH)
        init_db(conn)
        self._db_conns.append(conn)
        return conn

    def geocoded_leads(self) -> list:
        conn = self.conn()
        return [
            row
            for row in list_signups(conn)
            if row["latitude"] is not None and row["longitude"] is not None
        ]

    def security_secret(self) -> str:
        """Return the CSRF signing secret.

        Priority: explicit CSRF_SECRET > ADMIN_SESSION_SECRET > PBKDF2-derived
        from ADMIN_PASSWORD.  Never falls back to a hardcoded constant.
        """
        secret = os.environ.get("CSRF_SECRET") or os.environ.get("ADMIN_SESSION_SECRET")
        if secret:
            return secret
        return _derive_dev_secret("csrf")

    def admin_password(self) -> str:
        return os.environ.get("ADMIN_PASSWORD", "")

    def admin_secret(self) -> str:
        """Return the session-signing secret.

        Priority: explicit ADMIN_SESSION_SECRET > PBKDF2-derived from
        ADMIN_PASSWORD.  Never falls back to the plaintext password directly.
        """
        secret = os.environ.get("ADMIN_SESSION_SECRET")
        if secret:
            return secret
        return _derive_dev_secret("session")

    def _cookie_secure(self) -> bool:
        """Decide whether cookies should carry the Secure flag.

        Honours COOKIE_SECURE=1 or a trusted X-Forwarded-Proto: https header.
        """
        if os.environ.get("COOKIE_SECURE") == "1":
            return True
        forwarded = self.headers.get("X-Forwarded-Proto", "")
        if forwarded and forwarded.split(",")[0].strip().lower() == "https":
            return True
        return False

    def _is_pii_path(self, path: str) -> bool:
        """True for routes that serve admin/auth/export/PII content."""
        return path.startswith("/admin") or path.startswith("/export")

    def send_security_headers(self) -> None:
        """Emit baseline security headers before end_headers()."""
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        if self._is_pii_path(urlparse(self.path).path.rstrip("/") or "/"):
            self.send_header("Cache-Control", "no-store")

    def is_admin_authenticated(self) -> bool:
        token = parse_cookie(self.headers.get("Cookie", ""))
        return verify_session_token(token, self.admin_secret())

    def require_admin_html(self) -> bool:
        if self.is_admin_authenticated():
            return True
        self.respond_redirect("/admin-login")
        return False

    def require_admin_export(self) -> bool:
        if self.is_admin_authenticated():
            return True
        self.respond_text("Forbidden: admin login required", "text/plain", 403)
        return False

    def allow_request(self, path: str) -> bool:
        key = f"{self.client_address[0]}:{path}"
        return RATE_LIMITER.allow(key)

    def valid_csrf(self, form: dict[str, str], action: str) -> bool:
        return verify_csrf_token(form.get("csrf_token", ""), self.security_secret(), action)

    def csrf_token(self, action: str) -> str:
        secret = self.security_secret()
        if not secret:
            return ""
        return create_csrf_token(secret, action)

    def handle_login(self, form: dict[str, str]) -> None:
        if not self.valid_csrf(form, "admin-login"):
            self.respond_html(self.login_page(["invalid CSRF token"]), 400)
            return
        password = self.admin_password()
        if not password:
            self.respond_html(self.login_page(["ADMIN_PASSWORD is not configured"]), 500)
            return
        if not authenticate_password(form.get("password", ""), password):
            self.respond_html(self.login_page(["invalid admin password"]), 401)
            return
        token = create_session_token(self.admin_secret())
        self.respond_redirect("/admin", [session_cookie(token, secure=self._cookie_secure())])

    def shopify_fields_from_form(self, form: dict[str, str], secret: str) -> dict[str, str] | None:
        direct_fields = {
            "shopify_shop_domain": form.get("shopify_shop_domain", ""),
            "shopify_customer_id": form.get("shopify_customer_id", ""),
            "shopify_page_url": form.get("shopify_page_url", ""),
        }
        if not secret:
            return direct_fields

        token = form.get("shopify_context_token", "")
        if not token and not any(direct_fields.values()):
            return direct_fields

        context = verify_context_token(token, secret)
        return context.as_form_fields() if context else None

    def signup_page(self, path: str, errors: list[str] | None = None) -> bytes:
        parsed = urlparse(self.path)
        query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        slug = path.split("/signup/", 1)[1] if path.startswith("/signup/") else "default"
        variant = get_variant(self.conn(), slug) or get_variant(self.conn(), "default")
        secret = os.environ.get("SHOPIFY_APP_SECRET", "")
        shopify_fields, shopify_token, shopify_error = self.shopify_context_for_page(query, secret)
        all_errors = [*(errors or []), *([shopify_error] if shopify_error else [])]
        error_html = "" if not all_errors else "<div class='error'>" + "<br>".join(map(escape, all_errors)) + "</div>"
        body = f"""
        <div class="card">
          <a href="/overview"><img src="{LOGO_URL}" alt="Benton Drones" style="max-width:260px;margin-bottom:16px"></a>
          <h1>{escape(variant['title'])}</h1>
          <p>{escape(variant['subtitle'])}</p>
          {error_html}
          <form method="post" action="/signup">
            <input type="hidden" name="campaign" value="{escape(query.get('campaign') or variant['campaign'])}">
            <input type="hidden" name="source" value="{escape(query.get('source') or variant['source'])}">
            <input type="hidden" name="variant_slug" value="{escape(slug)}">
            <input type="hidden" name="shopify_shop_domain" value="{escape(shopify_fields['shopify_shop_domain'])}">
            <input type="hidden" name="shopify_customer_id" value="{escape(shopify_fields['shopify_customer_id'])}">
            <input type="hidden" name="shopify_page_url" value="{escape(shopify_fields['shopify_page_url'])}">
            <input type="hidden" name="shopify_context_token" value="{escape(shopify_token)}">
            <input type="hidden" name="csrf_token" value="{escape(self.csrf_token('signup'))}">
            <label style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden">Leave this blank <input name="website_url" autocomplete="off" tabindex="-1"></label>
            <div class="two-col">
              <label>First name <input name="first_name" required></label>
              <label>Last name <input name="last_name" required></label>
            </div>
            <label>Email <input name="email" type="email" required></label>
            <label>Phone <input name="phone"></label>
            <label>Address line 1 <input name="address_line1" required></label>
            <label>Address line 2 <input name="address_line2"></label>
            <div class="two-col">
              <label>City <input name="city" required></label>
              <label>State <input name="state" maxlength="2" required></label>
            </div>
            <label>ZIP <input name="postal_code" required></label>
            <label>Notes <textarea name="notes" rows="3"></textarea></label>
            <label><input type="checkbox" name="consent_accepted" value="yes" required> {escape(CONSENT_TEXT)}</label>
            <label>Aerial services waiver</label>
            <div class="waiver-box">{escape(WAIVER_TEXT)}</div>
            <label><input type="checkbox" name="waiver_accepted" value="yes" required> I have read and agree to the above waiver</label>
            <label>Type your full legal name to sign <input name="typed_name" required autocomplete="name"></label>
            <p style="font-size:0.9rem;color:#555;margin-top:12px">{escape(SIGNATURE_DISCLAIMER)}</p>
            <button>{escape(variant['cta_text'])}</button>
          </form>
        </div>
        """
        return branded_page("Benton Drones Signup", body)

    def shopify_context_for_page(
        self,
        query: dict[str, str],
        secret: str,
    ) -> tuple[dict[str, str], str, str]:
        has_context = any(query.get(key) for key in ("shop", "logged_in_customer_id", "page_url"))
        empty = {"shopify_shop_domain": "", "shopify_customer_id": "", "shopify_page_url": ""}
        if not has_context:
            return empty, "", ""

        if not secret:
            return context_from_params(query).as_form_fields(), "", ""

        if not verify_hmac(query, secret):
            return empty, "", "invalid Shopify app proxy signature"

        context = context_from_params(query)
        return context.as_form_fields(), sign_context(context, secret), ""

    def login_page(self, errors: list[str] | None = None) -> bytes:
        error_html = "" if not errors else "<div class='error'>" + "<br>".join(map(escape, errors)) + "</div>"
        body = f"""
        <div class="card" style="max-width:420px;margin:0 auto">
          <a href="/overview"><img src="{LOGO_URL}" alt="Benton Drones" style="max-width:260px;margin-bottom:16px"></a>
          <h1>Admin Login</h1>
          {error_html}
          <form method="post" action="/admin-login">
            <input type="hidden" name="csrf_token" value="{escape(self.csrf_token('admin-login'))}">
            <label>Password <input name="password" type="password" required></label>
            <button>Log in</button>
          </form>
        </div>
        """
        return branded_page("Admin Login", body)

    def admin_page(self) -> bytes:
        conn = self.conn()
        stats = analytics_summary(conn)
        rows = recent_leads(conn, limit=50)
        geocoded = self.geocoded_leads()
        has_leads = bool(geocoded)
        map_init = ""
        if has_leads:
            coords = [[row["latitude"], row["longitude"]] for row in geocoded]
            bounds = coords
            map_init = f"""
            map.fitBounds({bounds});
            function esc(s) {{ var d = document.createElement('div'); d.appendChild(document.createTextNode(s)); return d.innerHTML; }}
            fetch('/admin/leads.geojson')
              .then(r => r.json())
              .then(data => {{
                L.geoJSON(data, {{
                  pointToLayer: function(feature, latlng) {{
                    return L.circleMarker(latlng, {{radius: 8, fillColor: '#809948', color: '#000000', weight: 1, opacity: 1, fillOpacity: 0.8}});
                  }},
                  onEachFeature: function(feature, layer) {{
                    layer.bindPopup('<a href="/admin/lead/' + feature.properties.id + '">' + esc(feature.properties.name) + '</a><br>' + esc(feature.properties.address));
                  }}
                }}).addTo(map);
              }});
            """
        else:
            map_init = "document.getElementById('map').innerHTML = '<p style=\\'padding:16px\\'>No geocoded leads yet.</p>';"

        def breakdown_html(data: dict) -> str:
            if not data:
                return "<em>No data</em>"
            items = " ".join(f"<span>{escape(str(k) or 'unset')} ({v})</span>" for k, v in data.items())
            return f"<div class='breakdown'>{items}</div>"

        body = f"""
        <h1>Admin Dashboard</h1>
        <div class="analytics">
          <div class="metric"><div class="value">{stats['total']}</div><div class="label">Total leads</div></div>
          <div class="metric"><div class="value">{stats['today']}</div><div class="label">Today</div></div>
          <div class="metric"><div class="value">{stats['this_week']}</div><div class="label">This week</div></div>
          <div class="metric"><div class="value">{stats['pending_geocodes']}</div><div class="label">Pending geocodes</div></div>
        </div>
        <div class="card">
          <h2>Lead map</h2>
          <div id="map">No geocoded leads yet.</div>
          <link rel="stylesheet" href="/static/leaflet/leaflet.css">
          <script src="/static/leaflet/leaflet.js"></script>
          <script>
            var map = L.map('map');
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'}}).addTo(map);
            {map_init}
          </script>
        </div>
        <div class="card">
          <h2>Breakdowns</h2>
          <h3>By source</h3>
          {breakdown_html(stats['by_source'])}
          <h3>By campaign</h3>
          {breakdown_html(stats['by_campaign'])}
          <h3>By variant</h3>
          {breakdown_html(stats['by_variant'])}
        </div>
        <div class="card">
          <h2>Exports</h2>
          <p><a class="button secondary" href='/export/csv'>CSV</a> <a class="button secondary" href='/export/geojson'>GeoJSON</a> <a class="button secondary" href='/export/kml'>KML</a></p>
        </div>
        <h2>Recent leads</h2>
        <table>
          <tr><th>Name</th><th>Email</th><th>Address</th><th>Source</th><th>Status</th><th>Action</th></tr>
          {''.join(
            f"<tr style='cursor:pointer'>"
            f"<td>{escape(row['first_name'])} {escape(row['last_name'])}</td>"
            f"<td>{escape(row['email'])}</td>"
            f"<td>{escape(row['full_address'])}</td>"
            f"<td>{escape(row['source'] or '-')}</td>"
            f"<td>{escape(row['geocode_status'])}</td>"
            f"<td><a class='button secondary' href='/admin/lead/{row['id']}'>View</a></td></tr>"
            for row in rows
          )}
        </table>
        """
        return branded_page("Admin Dashboard", body, show_nav=True)

    def lead_detail_page(self, lead_id: str) -> bytes:
        conn = self.conn()
        try:
            signup_id = int(lead_id)
        except ValueError:
            return branded_page("Lead not found", "<div class='card'><h1>Lead not found</h1><p><a href='/admin'>Back to admin</a></p></div>", show_nav=True)
        signup = get_signup(conn, signup_id)
        if signup is None:
            return branded_page("Lead not found", "<div class='card'><h1>Lead not found</h1><p><a href='/admin'>Back to admin</a></p></div>", show_nav=True)
        consent = get_consent_record(conn, signup_id)
        signature = get_signature_record(conn, signup_id)

        def section(title: str, items: list[tuple[str, str]]) -> str:
            rows = "".join(f"<tr><th>{escape(label)}</th><td>{escape(value)}</td></tr>" for label, value in items)
            return f"<div class='card'><h2>{escape(title)}</h2><table>{rows}</table></div>"

        coords = f"{signup['latitude']}, {signup['longitude']}" if signup["latitude"] else "not geocoded"
        body = f"""
        <h1>Lead #{signup['id']}</h1>
        {section('Contact details', [
            ('Name', f"{signup['first_name']} {signup['last_name']}"),
            ('Email', signup['email']),
            ('Phone', signup['phone'] or '-'),
            ('Address', signup['full_address']),
            ('Notes', signup['notes'] or '-'),
            ('Created', signup['created_at']),
        ])}
        {section('Source & attribution', [
            ('Campaign', signup['campaign'] or '-'),
            ('Source', signup['source'] or '-'),
            ('Variant', signup['variant_slug'] or 'default'),
            ('Shopify shop', signup['shopify_shop_domain'] or '-'),
            ('Shopify customer', signup['shopify_customer_id'] or '-'),
        ])}
        {section('Consent record', [
            ('Version', consent['consent_version'] if consent else '-'),
            ('Accepted at', consent['accepted_at'] if consent else '-'),
            ('IP / UA', f"{consent['ip_address']} / {consent['user_agent'][:80]}" if consent else '-'),
        ])}
        {section('Signature record', [
            ('Typed name', signature['full_name_typed'] if signature else '-'),
            ('Signed at', signature['signed_at'] if signature else '-'),
            ('Waiver version', signature['waiver_version'] if signature else '-'),
            ('IP / UA', f"{signature['ip_address']} / {signature['user_agent'][:80]}" if signature else '-'),
            ('Disclaimer', signature['signature_disclaimer_text'][:120] + '…' if signature and len(signature['signature_disclaimer_text']) > 120 else (signature['signature_disclaimer_text'] if signature else '-')),
        ])}
        {section('Geocode status', [
            ('Status', signup['geocode_status']),
            ('Coordinates', coords),
            ('Provider', signup['geocode_provider'] or '-'),
            ('Display name', signup['geocode_display_name'] or '-'),
        ])}
        <p><a class="button" href='/admin'>Back to admin</a> <a class="button secondary" href='/admin/lead/{signup_id}/print'>Print / PDF</a></p>
        """
        return branded_page(f"Lead #{signup['id']}", body, show_nav=True)

    def try_create_jira_ticket(self, conn, signup_id: int) -> None:
        """Try to create a JIRA ticket after signup. Queue on failure or missing config."""
        config = jira_config_from_env()
        if not config:
            queue_jira_ticket(conn, signup_id, "JIRA config not set")
            return
        try:
            signup_row = get_signup(conn, signup_id)
            consent_row = get_consent_record(conn, signup_id)
            signature_row = get_signature_record(conn, signup_id)
            ticket_key = create_jira_ticket(signup_row, signature_row, consent_row, config)
            url = jira_issue_url(config, ticket_key)
            mark_jira_ticket_created(conn, signup_id, ticket_key, url)
        except (JiraApiError, JiraConfigError) as exc:
            queue_jira_ticket(conn, signup_id, str(exc))
        except Exception as exc:
            queue_jira_ticket(conn, signup_id, str(exc))

    def lead_print_page(self, lead_id: str) -> bytes:
        """Return a printable HTML consent form for a lead."""
        conn = self.conn()
        try:
            signup_id = int(lead_id)
        except ValueError:
            return branded_page("Lead not found", "<div class='card'><h1>Lead not found</h1><p><a href='/admin'>Back to admin</a></p></div>", show_nav=True)
        signup = get_signup(conn, signup_id)
        if signup is None:
            return branded_page("Lead not found", "<div class='card'><h1>Lead not found</h1><p><a href='/admin'>Back to admin</a></p></div>", show_nav=True)
        consent = get_consent_record(conn, signup_id)
        signature = get_signature_record(conn, signup_id)
        return render_signup_html(signup, consent, signature)

    def handle_lead_pdf(self, lead_id: str) -> None:
        """Serve a true PDF if fpdf2 is installed, else redirect to the print view."""
        conn = self.conn()
        try:
            signup_id = int(lead_id)
        except ValueError:
            self.respond_text("Invalid lead ID", "text/plain", 400)
            return
        signup = get_signup(conn, signup_id)
        if signup is None:
            self.respond_text("Lead not found", "text/plain", 404)
            return
        consent = get_consent_record(conn, signup_id)
        signature = get_signature_record(conn, signup_id)
        try:
            pdf_bytes = try_render_pdf(signup, consent, signature)
        except Exception:
            pdf_bytes = None
        if pdf_bytes is None:
            self.respond_redirect(
                f"/admin/lead/{signup_id}/print?pdf=unavailable",
            )
            return
        filename = f"benton-drones-consent-{signup_id}.pdf"
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(pdf_bytes)

    def handle_healthz(self) -> None:
        """Unauthenticated health check with a lightweight DB ping."""
        try:
            conn = self.conn()
            conn.execute("SELECT 1").fetchone()
            payload = json.dumps({"status": "ok", "version": VERSION, "tests_passed": True})
            self.respond_text(payload, "application/json", 200)
        except Exception:
            payload = json.dumps({"status": "error", "version": VERSION, "tests_passed": False})
            self.respond_text(payload, "application/json", 503)

    def respond_html(self, content: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(content)

    def respond_text(self, content: str, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def respond_redirect(self, location: str, cookies: list[str] | None = None) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        for cookie in cookies or []:
            self.send_header("Set-Cookie", cookie)
        self.send_security_headers()
        self.end_headers()

def validate_production_ready(log: logging.Logger) -> None:
    """Check startup config.  Refuses to start in production with weak secrets."""
    is_production = os.environ.get("ENV") == "production"
    problems: list[str] = []

    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password:
        problems.append("ADMIN_PASSWORD is not set")
    elif password in WEAK_PASSWORDS:
        problems.append(f"ADMIN_PASSWORD is a known weak default: {password!r}")

    if is_production:
        session_secret = os.environ.get("ADMIN_SESSION_SECRET", "")
        csrf_secret = os.environ.get("CSRF_SECRET", "")
        if not session_secret or len(session_secret) < 32:
            problems.append(
                "ADMIN_SESSION_SECRET must be set and >= 32 chars in production"
            )
        if not csrf_secret or len(csrf_secret) < 32:
            problems.append(
                "CSRF_SECRET must be set and >= 32 chars in production"
            )

    jira_vars = ["JIRA_BASE_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
    jira_set = [v for v in jira_vars if os.environ.get(v)]
    if 0 < len(jira_set) < len(jira_vars):
        log.warning(
            "JIRA config is partial: %d of %d vars set", len(jira_set), len(jira_vars)
        )

    if problems:
        if is_production:
            for p in problems:
                log.error(p)
            raise SystemExit("Refusing to start: " + "; ".join(problems))
        for p in problems:
            log.warning(p)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    validate_production_ready(logger)

    host = os.environ.get("HOST", HOST)
    port = int(os.environ.get("PORT", PORT))

    with connect(DEFAULT_DB_PATH) as conn:
        init_db(conn)

    admin_ok = bool(os.environ.get("ADMIN_PASSWORD"))
    jira_ok = all(
        os.environ.get(v)
        for v in ["JIRA_BASE_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
    )
    logger.info("Benton Drones lead ingest v%s starting on %s:%s", VERSION, host, port)
    logger.info("Admin configured: %s", "yes" if admin_ok else "no")
    logger.info("JIRA configured: %s", "yes" if jira_ok else "no")

    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
