from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from urllib.parse import parse_qs

SHOPIFY_SIGNATURE_FIELDS = {"hmac", "signature"}


@dataclass(frozen=True)
class ShopifyContext:
    shop: str = ""
    logged_in_customer_id: str = ""
    page_url: str = ""

    def as_form_fields(self) -> dict[str, str]:
        return {
            "shopify_shop_domain": self.shop,
            "shopify_customer_id": self.logged_in_customer_id,
            "shopify_page_url": self.page_url,
        }


def first_values(params: dict[str, list[str] | str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in params.items():
        normalized[key] = value[0] if isinstance(value, list) else value
    return normalized


def parse_query(query: str) -> dict[str, str]:
    return first_values(parse_qs(query, keep_blank_values=True))


def canonical_message(params: dict[str, str]) -> str:
    filtered = {
        key: value
        for key, value in params.items()
        if key not in SHOPIFY_SIGNATURE_FIELDS
    }
    return "&".join(f"{key}={filtered[key]}" for key in sorted(filtered))


def calculate_hmac(params: dict[str, str], secret: str) -> str:
    message = canonical_message(params).encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return digest


def verify_hmac(params: dict[str, str], secret: str) -> bool:
    if not secret:
        return False
    expected = params.get("hmac") or params.get("signature") or ""
    if not expected:
        return False
    actual = calculate_hmac(params, secret)
    return hmac.compare_digest(actual, expected)


def context_from_params(params: dict[str, str]) -> ShopifyContext:
    return ShopifyContext(
        shop=params.get("shop", ""),
        logged_in_customer_id=params.get("logged_in_customer_id", ""),
        page_url=params.get("page_url", ""),
    )


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def sign_context(context: ShopifyContext, secret: str) -> str:
    payload = json.dumps(context.__dict__, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded_payload = _b64encode(payload)
    signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def verify_context_token(token: str, secret: str) -> ShopifyContext | None:
    if not token or not secret or "." not in token:
        return None
    encoded_payload, signature = token.rsplit(".", 1)
    expected = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        payload = json.loads(_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError):
        return None
    return ShopifyContext(
        shop=str(payload.get("shop", "")),
        logged_in_customer_id=str(payload.get("logged_in_customer_id", "")),
        page_url=str(payload.get("page_url", "")),
    )
