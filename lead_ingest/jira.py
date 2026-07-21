"""JIRA Cloud ticket creation using only Python stdlib.

No third-party dependencies. Uses urllib.request for HTTP calls.
If JIRA env vars are not set, callers should queue the signup locally.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from lead_ingest.models import CONSENT_VERSION, WAIVER_VERSION


class JiraConfigError(Exception):
    """Raised when JIRA configuration is incomplete."""


class JiraApiError(Exception):
    """Raised when the JIRA API call fails."""


def jira_config_from_env() -> dict[str, str] | None:
    """Read JIRA configuration from environment variables.

    Returns a dict with base_url, user_email, api_token, project_key,
    issue_type, or None if any required var is missing.
    """
    required = (
        "JIRA_BASE_URL",
        "JIRA_USER_EMAIL",
        "JIRA_API_TOKEN",
        "JIRA_PROJECT_KEY",
    )
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        return None
    return {
        "base_url": os.environ["JIRA_BASE_URL"].rstrip("/"),
        "user_email": os.environ["JIRA_USER_EMAIL"],
        "api_token": os.environ["JIRA_API_TOKEN"],
        "project_key": os.environ["JIRA_PROJECT_KEY"],
        "issue_type": os.environ.get("JIRA_ISSUE_TYPE", "Task"),
    }


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Convert a sqlite3.Row (or dict) to a plain dict."""
    if isinstance(row, dict):
        return row
    return dict(row) if row else {}


def build_jira_payload(
    signup_row: Any,
    signature_row: Any | None = None,
    consent_row: Any | None = None,
    config: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a JIRA Cloud REST API issue-create payload (dict).

    Returns a dict suitable for json.dumps with fields: project, summary,
    description, issuetype.
    """
    signup = _row_to_dict(signup_row)
    sig = _row_to_dict(signature_row)
    consent = _row_to_dict(consent_row)
    project_key = (config or {}).get("project_key", "BDS")
    issue_type = (config or {}).get("issue_type", "Task")

    name = f"{signup.get('first_name', '')} {signup.get('last_name', '')}".strip()
    summary = f"New lead signup: {name or signup.get('email', 'unknown')}"

    lines: list[str] = [
        f"*Lead:* {name}",
        f"*Email:* {signup.get('email', '-')}",
        f"*Phone:* {signup.get('phone', '-') or '-'}",
        f"*Address:* {signup.get('full_address', '-')}",
        f"*Campaign:* {signup.get('campaign', '-') or '-'}",
        f"*Source:* {signup.get('source', '-') or '-'}",
        f"*Variant:* {signup.get('variant_slug', 'default') or 'default'}",
        f"*Signup ID:* {signup.get('id', '-')}",
        f"*Created:* {signup.get('created_at', '-')}",
        "",
        f"*Consent version:* {consent.get('consent_version', CONSENT_VERSION)}",
        f"*Consent accepted at:* {consent.get('accepted_at', '-')}",
        f"*Waiver version:* {sig.get('waiver_version', WAIVER_VERSION)}",
        f"*Signed by:* {sig.get('full_name_typed', '-')}",
        f"*Signed at:* {sig.get('signed_at', '-')}",
        f"*IP address:* {sig.get('ip_address', '-') or consent.get('ip_address', '-')}",
    ]
    if signup.get("notes"):
        lines.append("")
        lines.append(f"*Notes:* {signup['notes']}")

    return {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": "\n".join(lines),
            "issuetype": {"name": issue_type},
        }
    }


def create_jira_ticket(
    signup_row: Any,
    signature_row: Any | None = None,
    consent_row: Any | None = None,
    config: dict[str, str] | None = None,
) -> str:
    """Create a JIRA ticket and return the ticket key (e.g. BDS-123).

    Raises JiraConfigError if config is incomplete.
    Raises JiraApiError if the HTTP call fails or the response is unexpected.
    """
    if not config:
        raise JiraConfigError("JIRA config is missing — cannot create ticket")

    payload = build_jira_payload(signup_row, signature_row, consent_row, config)
    url = f"{config['base_url']}/rest/api/3/issue"
    body = json.dumps(payload).encode("utf-8")

    # JIRA Cloud uses basic auth with email:api_token
    import base64

    credentials = f"{config['user_email']}:{config['api_token']}"
    auth_header = base64.b64encode(credentials.encode()).decode()

    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Basic {auth_header}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            pass
        raise JiraApiError(f"JIRA API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise JiraApiError(f"JIRA connection error: {exc.reason}") from exc

    ticket_key = data.get("key")
    if not ticket_key:
        raise JiraApiError(f"JIRA response missing ticket key: {data}")

    return ticket_key  # type: ignore[return-value]


def jira_issue_url(config: dict[str, str], ticket_key: str) -> str:
    """Build the human-friendly URL for a JIRA issue."""
    return f"{config['base_url']}/browse/{ticket_key}"
