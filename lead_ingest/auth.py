from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from http.cookies import SimpleCookie

ADMIN_COOKIE_NAME = "bd_admin_session"
DEFAULT_SESSION_SECONDS = 8 * 60 * 60


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def authenticate_password(candidate: str, expected: str) -> bool:
    if not expected:
        return False
    return hmac.compare_digest(candidate, expected)


def create_session_token(secret: str, now: int | None = None) -> str:
    if not secret:
        raise ValueError("session secret is required")
    issued_at = int(time.time() if now is None else now)
    payload = {"role": "admin", "iat": issued_at}
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = hmac.new(secret.encode(), encoded_payload.encode(), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def verify_session_token(
    token: str,
    secret: str,
    now: int | None = None,
    max_age_seconds: int = DEFAULT_SESSION_SECONDS,
) -> bool:
    if not token or not secret or "." not in token:
        return False
    encoded_payload, signature = token.rsplit(".", 1)
    expected = hmac.new(secret.encode(), encoded_payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False
    try:
        payload = json.loads(_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError):
        return False
    if payload.get("role") != "admin":
        return False
    issued_at = int(payload.get("iat", 0))
    current_time = int(time.time() if now is None else now)
    return 0 <= current_time - issued_at <= max_age_seconds


def parse_cookie(header: str, name: str = ADMIN_COOKIE_NAME) -> str:
    if not header:
        return ""
    cookie = SimpleCookie()
    cookie.load(header)
    return cookie[name].value if name in cookie else ""


def session_cookie(token: str, secure: bool = False) -> str:
    parts = [
        f"{ADMIN_COOKIE_NAME}={token}",
        "HttpOnly",
        "SameSite=Lax",
        "Path=/",
        f"Max-Age={DEFAULT_SESSION_SECONDS}",
    ]
    if secure:
        parts.append("Secure")
    return "; ".join(parts)


def expired_session_cookie(secure: bool = False) -> str:
    parts = [
        f"{ADMIN_COOKIE_NAME}=",
        "HttpOnly",
        "SameSite=Lax",
        "Path=/",
        "Max-Age=0",
    ]
    if secure:
        parts.append("Secure")
    return "; ".join(parts)
