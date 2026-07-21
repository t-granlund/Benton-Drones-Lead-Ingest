from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field

DEFAULT_CSRF_SECONDS = 60 * 60


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_csrf_token(secret: str, action: str, now: int | None = None) -> str:
    if not secret:
        raise ValueError("CSRF secret is required")
    issued_at = int(time.time() if now is None else now)
    payload = {"action": action, "iat": issued_at}
    encoded = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_csrf_token(
    token: str,
    secret: str,
    action: str,
    now: int | None = None,
    max_age_seconds: int = DEFAULT_CSRF_SECONDS,
) -> bool:
    if not token or not secret or "." not in token:
        return False
    encoded, signature = token.rsplit(".", 1)
    expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False
    try:
        payload = json.loads(_b64decode(encoded))
    except (ValueError, json.JSONDecodeError):
        return False
    if payload.get("action") != action:
        return False
    issued_at = int(payload.get("iat", 0))
    current_time = int(time.time() if now is None else now)
    return 0 <= current_time - issued_at <= max_age_seconds


@dataclass
class RateLimiter:
    max_requests: int
    window_seconds: int
    hits: dict[str, list[float]] = field(default_factory=dict)

    def allow(self, key: str, now: float | None = None) -> bool:
        current_time = time.time() if now is None else now
        cutoff = current_time - self.window_seconds
        recent = [timestamp for timestamp in self.hits.get(key, []) if timestamp >= cutoff]
        if len(recent) >= self.max_requests:
            self.hits[key] = recent
            return False
        recent.append(current_time)
        self.hits[key] = recent
        return True

    def clear(self) -> None:
        self.hits.clear()
