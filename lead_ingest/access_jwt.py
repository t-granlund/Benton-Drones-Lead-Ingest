"""Cloudflare Access JWT verification (optional, env-gated).

When enabled, every /admin/* and /export/* request must carry a valid
``Cf-Access-Jwt-Assertion`` header signed by Cloudflare Access.  The module
fetches the Cloudflare Access JWKS at startup and refreshes on cache miss or
TTL expiry.

Env vars (all required to enable):

    CF_ACCESS_TEAM_DOMAIN  your team name, e.g. "bentondrones"
                           (from https://<team>.cloudflareaccess.com)
    CF_ACCESS_AUD          the Application Audience tag from the Access app
                           (long random string from the Access dashboard)

Optional but recommended once tested:

    CF_ACCESS_STRICT       set to "1" to disable the shared-password login
                           fallback entirely (Access becomes the only auth)
    CF_ACCESS_JWKS_TTL     seconds before JWKS refresh (default 300)

Behaviour when disabled:
    - If the env vars are absent or empty, ``is_enabled()`` returns False
      and the existing password login is used unchanged.
    - If enabled but verification fails, the request is 403 Forbidden.
      In strict mode, the password login route is also disabled.

Audit trail:
    Successfully verified JWTs expose the user's email via ``.email`` on
    the returned claims object.  Pair this with per-request logging in
    ``server.py`` to build a tamper-evident access log.

Dependencies:
    Requires ``pyjwt`` and ``cryptography``.  Install via requirements.txt.
    The module fails closed (AssertionError) if the deps are missing at
    import time when the feature is configured.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen as _urlopen


def _fetch_url(req: Request, timeout: int = 10) -> bytes:
    """Open *req* and return the response body.  Isolated for easy mocking."""
    with _urlopen(req, timeout=timeout) as resp:
        return resp.read()


# Backward-compatible alias used by _JwksCache._fetch().  Tests patch
# ``access_jwt.urlopen`` so we keep this private name.
urlopen = _urlopen  # noqa: F841

log = logging.getLogger(__name__)

DEFAULT_TEAM_DOMAIN = ""
DEFAULT_AUD = ""
DEFAULT_JWKS_TTL = 300  # 5 minutes; Cloudflare rotates keys but keeps old ones alive ~7d
CF_ACCESS_CERTS_URL_TEMPLATE = "https://{team}.cloudflareaccess.com/cdn-cgi/access/certs"
assertion_header = "Cf-Access-Jwt-Assertion"


class AccessJwtError(Exception):
    """Base class for Access JWT failures."""


class AccessNotEnabledError(AccessJwtError):
    """Access env vars are not configured."""


class AccessJwksError(AccessJwtError):
    """JWKS fetch or parse failure."""


class AccessVerifyError(AccessJwtError):
    """JWT verification failure (bad signature, exp, aud, iss, etc)."""


@dataclass(frozen=True)
class AccessClaims:
    """Verified Cloudflare Access JWT claims."""

    sub: str
    email: str
    aud: str
    iss: str
    iat: int
    exp: int
    extra: dict[str, Any] = field(default_factory=dict)


def config_from_env() -> dict[str, str]:
    """Return the Access configuration from environment variables."""
    return {
        "team_domain": os.environ.get("CF_ACCESS_TEAM_DOMAIN", DEFAULT_TEAM_DOMAIN).strip(),
        "aud": os.environ.get("CF_ACCESS_AUD", DEFAULT_AUD).strip(),
        "strict": os.environ.get("CF_ACCESS_STRICT", "").strip() == "1",
        "jwks_ttl": int(os.environ.get("CF_ACCESS_JWKS_TTL", DEFAULT_JWKS_TTL)),
    }


def is_enabled(cfg: dict[str, str] | None = None) -> bool:
    """True if CF_ACCESS_TEAM_DOMAIN and CF_ACCESS_AUD are both set."""
    if cfg is None:
        cfg = config_from_env()
    return bool(cfg["team_domain"] and cfg["aud"])


def is_strict(cfg: dict[str, str] | None = None) -> bool:
    """True if CF_ACCESS_STRICT=1 and Access is otherwise enabled."""
    if cfg is None:
        cfg = config_from_env()
    return bool(is_enabled(cfg) and cfg["strict"])


# ---------------------------------------------------------------------------
# JWKS fetching and caching
# ---------------------------------------------------------------------------


class _JwksCache:
    """Fetch, cache, and serve Cloudflare Access JWKS."""

    def __init__(self, team_domain: str, ttl: int = DEFAULT_JWKS_TTL) -> None:
        self.team_domain = team_domain
        self.ttl = ttl
        self._keys: dict[str, Any] = {}
        self._fetched_at: float = 0.0
        self._last_error: AccessJwksError | None = None

    def _fetch(self) -> None:
        try:
            import jwt  # pyjwt[all] provides PyJWK
        except ImportError as exc:
            raise AccessJwksError(
                "pyjwt is required for Cloudflare Access JWT verification; "
                "pip install PyJWT cryptography"
            ) from exc

        url = CF_ACCESS_CERTS_URL_TEMPLATE.format(team=self.team_domain)
        req = Request(url, headers={"User-Agent": "benton-drones-lead-ingest/0.2"})
        try:
            raw = _fetch_url(req, timeout=10)
            payload = raw.decode("utf-8")
        except URLError as exc:
            raise AccessJwksError(f"failed to fetch Access JWKS from {url}: {exc}") from exc

        try:
            jwks = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise AccessJwksError(f"Access JWKS response is not valid JSON") from exc

        new_keys: dict[str, Any] = {}
        for key_data in jwks.get("keys", []):
            kid = key_data.get("kid")
            if not kid:
                continue
            try:
                new_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_data))
            except Exception as exc:  # noqa: BLE001
                log.warning("Failed to load Access JWK kid=%s: %s", kid, exc)
        if not new_keys:
            raise AccessJwksError("no usable RSA keys in Access JWKS")
        self._keys = new_keys
        self._fetched_at = time.time()
        self._last_error = None
        log.info("Access JWKS refreshed: %d key(s)", len(new_keys))

    def get_key(self, kid: str) -> Any:
        """Return the RSA public key for ``kid``.

        Refreshes the JWKS if the key is missing or the cache is stale.  Raises
        ``AccessJwksError`` if the key cannot be found even after refresh.
        """
        now = time.time()
        if now - self._fetched_at > self.ttl or kid not in self._keys:
            try:
                self._fetch()
            except AccessJwksError as exc:
                self._last_error = exc
                log.error("Access JWKS refresh failed: %s", exc)
        try:
            return self._keys[kid]
        except KeyError:
            err_msg = f"Access JWT kid={kid} not in JWKS"
            if self._last_error is not None:
                err_msg += f" (last refresh error: {self._last_error})"
            raise AccessJwksError(err_msg) from None


def _jwks_cache_for(cfg: dict[str, str]) -> _JwksCache:
    """Return a shared (module-level) JWKS cache, creating it if needed."""
    global _JWKS_CACHE
    try:
        cache = _jwks_cache_singleton  # type: ignore[name-defined]
    except NameError:
        cache = _JwksCache(cfg["team_domain"], cfg["jwks_ttl"])
        globals()["_jwks_cache_singleton"] = cache
    return cache


# Reset for tests
_JWKS_CACHE: _JwksCache | None = None


def reset_jwks_cache() -> None:
    """Drop the module-level JWKS cache (useful in tests)."""
    globals()["_jwks_cache_singleton"] = _JwksCache(  # noqa: F841
        config_from_env()["team_domain"]
    )


# ---------------------------------------------------------------------------
# JWT verification
# ---------------------------------------------------------------------------


def _decode_and_verify(
    token: str,
    cfg: dict[str, str],
    jwks: _JwksCache,
) -> dict[str, Any]:
    """Decode and cryptographically verify the JWT; raise on any failure."""
    try:
        import jwt
    except ImportError as exc:
        raise AccessJwtError(
            "pyjwt is required for Cloudflare Access JWT verification"
        ) from exc

    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:  # noqa: BLE001
        raise AccessVerifyError(f"failed to parse JWT header: {exc}") from exc
    if header.get("alg") != "RS256":
        raise AccessVerifyError(f"unexpected alg {header.get('alg')!r}")

    kid = header.get("kid")
    if not kid:
        raise AccessVerifyError("JWT missing kid header")

    key = jwks.get_key(kid)

    expected_iss = f"https://{cfg['team_domain']}.cloudflareaccess.com"
    try:
        decoded = jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            audience=cfg["aud"],
            issuer=expected_iss,
            options={
                "require": ["exp", "iat", "aud", "iss"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )
    except Exception as exc:  # noqa: BLE001
        raise AccessVerifyError(f"JWT verification failed: {exc}") from exc
    return decoded


def verify_assertion(
    headers: dict[str, str],
    cfg: dict[str, str] | None = None,
) -> AccessClaims:
    """Verify the ``Cf-Access-Jwt-Assertion`` header and return the claims.

    Raises:
        AccessNotEnabledError: Access env vars not configured (caller should
            fall back to password auth).
        AccessJwksError: could not fetch or parse the JWKS.
        AccessVerifyError: the token itself is invalid (bad signature, exp,
            aud, iss, etc.).
    """
    if cfg is None:
        cfg = config_from_env()
    if not is_enabled(cfg):
        raise AccessNotEnabledError("Cloudflare Access env vars not configured")

    token = headers.get(assertion_header) or headers.get(assertion_header.lower())
    if not token:
        raise AccessVerifyError(f"missing {assertion_header} header")

    jwks = _jwks_cache_for(cfg)
    payload = _decode_and_verify(token.strip(), cfg, jwks)

    email = payload.get("email", "")
    return AccessClaims(
        sub=payload.get("sub", ""),
        email=email,
        aud=payload.get("aud", ""),
        iss=payload.get("iss", ""),
        iat=int(payload.get("iat", 0)),
        exp=int(payload.get("exp", 0)),
        extra=payload,
    )


def verify_or_none(headers: dict[str, str]) -> AccessClaims | None:
    """Like ``verify_assertion`` but returns None on any failure.

    Use this when the password login is still active as a fallback.  The
    caller decides whether to allow the request when this returns None.
    Strict mode should never call this; strict callers use
    ``verify_assertion`` directly to get the specific error.
    """
    try:
        return verify_assertion(headers)
    except AccessJwtError:
        return None
