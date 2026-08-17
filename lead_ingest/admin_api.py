"""JSON admin API + CORS for the Cloudflare Pages static dashboard (ADR-001).

The Pages-hosted admin UI at ``admin.bentondrones.com`` talks to these
endpoints on the Render backend.  Auth is the same as for the HTML admin:
either the password session cookie or a verified Cloudflare Access JWT.

CORS is env-gated by ``CORS_ADMIN_ORIGIN`` (e.g.
``https://admin.bentondrones.com``).  When unset, cross-origin requests get
no CORS headers at all (today's default = same-origin only).  Never uses
the wildcard origin.
"""
from __future__ import annotations

import json
import os
from typing import Any

from lead_ingest import db as ledger
from lead_ingest.jira_replay import queue_stats as jira_queue_stats
from lead_ingest.jira_replay import sweep as jira_sweep
from lead_ingest.jira import jira_config_from_env
from lead_ingest.notify import process_queue as email_process_queue
from lead_ingest.notify import queue_counts as email_queue_counts
from lead_ingest.notify import smtp_config_from_env


def allowed_origin() -> str:
    """Configured admin UI origin (without trailing slash); '' when unset."""
    return os.environ.get("CORS_ADMIN_ORIGIN", "").strip().rstrip("/")


def request_origin_is_allowed(headers) -> bool:
    """True if the request's Origin matches CORS_ADMIN_ORIGIN exactly."""
    configured = allowed_origin()
    if not configured:
        return False
    origin = (headers.get("Origin", "") or "").rstrip("/")
    return origin == configured


def preflight(handler) -> None:
    """Answer an OPTIONS preflight for an allowed admin-UI origin."""
    handler.send_response(204)
    if request_origin_is_allowed(handler.headers):
        handler.send_header("Access-Control-Allow-Origin", allowed_origin())
        handler.send_header("Access-Control-Allow-Credentials", "true")
        handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        handler.send_header(
            "Access-Control-Allow-Headers",
            "Cf-Access-Jwt-Assertion, Content-Type, Authorization",
        )
        handler.send_header("Access-Control-Max-Age", "3600")
    handler.send_header("Vary", "Origin")
    handler.send_security_headers()
    handler.end_headers()


def apply_cors(handler) -> None:
    """Attach CORS response headers (call before end_headers on API routes)."""
    if request_origin_is_allowed(handler.headers):
        handler.send_header("Access-Control-Allow-Origin", allowed_origin())
        handler.send_header("Access-Control-Allow-Credentials", "true")
    handler.send_header("Vary", "Origin")


def respond_json(handler, payload: Any, status: int = 200) -> None:
    """JSON response with CORS applied explicitly (respond_text bypasses)."""
    body = json.dumps(payload, default=str)
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    apply_cors(handler)
    handler.send_security_headers()
    handler.end_headers()
    handler.wfile.write(body.encode("utf-8"))


def _row_to_lead(row) -> dict:
    """Thin, UI-focused projection of a signup row (avoids dumping PII fields
    the dashboard never renders)."""
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": row["email"],
        "phone": row["phone"],
        "full_address": row["full_address"],
        "source": row["source"],
        "campaign": row["campaign"],
        "variant_slug": row["variant_slug"],
        "geocode_status": row["geocode_status"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "created_at": row["created_at"],
    }


def summary_payload(conn, run_sweeps: bool = True) -> dict:
    """Dashboard summary: analytics + queue counts (matches HTML admin)."""
    jstats = {"pending": 0, "created": 0, "dead": 0}
    estats = {"pending": 0, "sent": 0, "dead": 0}
    if run_sweeps:
        try:
            outcome = jira_sweep(conn, jira_config_from_env())
            jstats = jira_queue_stats(conn, outcome)
        except Exception:
            pass
        try:
            email_process_queue(conn, smtp_config_from_env())
            estats = email_queue_counts(conn)
        except Exception:
            pass
    stats = ledger.analytics_summary(conn)
    return {
        **stats,
        "jira_pending": jstats["pending"],
        "jira_created": jstats["created"],
        "jira_dead": jstats["dead"],
        "email_pending": estats["pending"],
        "email_sent": estats["sent"],
        "email_dead": estats["dead"],
    }


def handle_summary(handler) -> None:
    conn = handler.conn()
    respond_json(handler, summary_payload(conn))


def handle_leads(handler) -> None:
    conn = handler.conn()
    rows = ledger.recent_leads(conn, limit=200)
    respond_json(handler, {"leads": [_row_to_lead(r) for r in rows]})


def handle_lead_detail(handler, lead_id: str) -> None:
    conn = handler.conn()
    row = ledger.get_signup(conn, lead_id)
    if not row:
        respond_json(handler, {"error": "not found"}, 404)
        return
    payload = _row_to_lead(row)
    consent = ledger.get_consent_record(conn, lead_id)
    sig = ledger.get_signature_record(conn, lead_id)
    payload["consent"] = (
        {
            "version": consent["consent_version"],
            "accepted_at": consent["accepted_at"],
            "ip_address": consent["ip_address"],
        }
        if consent
        else None
    )
    payload["signature"] = (
        {
            "full_name_typed": sig["full_name_typed"],
            "waiver_version": sig["waiver_version"],
            "signed_at": sig["signed_at"],
        }
        if sig
        else None
    )
    payload["notes"] = row["notes"]
    respond_json(handler, payload)


def handle_audit_log(handler) -> None:
    conn = handler.conn()
    rows = ledger.list_admin_events(conn, limit=100)
    respond_json(
        handler,
        {
            "events": [
                {
                    "id": r["id"],
                    "event_type": r["event_type"],
                    "actor": r["actor"],
                    "path": r["path"],
                    "detail": r["detail"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        },
    )


# Routes served by this module (server.do_GET dispatches here).
API_ROUTES = ("/admin/api/summary", "/admin/api/leads", "/admin/api/audit")


def handle_get(handler, path: str) -> bool:
    """Route ``path`` if it belongs to this API.  Returns False if unowned."""
    if path == "/admin/api/summary":
        handle_summary(handler)
        return True
    if path == "/admin/api/leads":
        handle_leads(handler)
        return True
    if path == "/admin/api/audit":
        handle_audit_log(handler)
        return True
    if path.startswith("/admin/api/lead/"):
        handle_lead_detail(handler, path.rsplit("/", 1)[-1])
        return True
    return False
