from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

CONSENT_VERSION = "2026-07-06.v1"
CONSENT_TEXT = (
    "I consent to Benton Drones contacting me about drone delivery simulations. "
    "I understand this signup is for planning and simulation purposes and does not "
    "guarantee service availability."
)

WAIVER_VERSION = "2026-07-15.placeholder.v1"
WAIVER_TEXT = (
    "[PLACEHOLDER WAIVER — MUST BE REVIEWED BY LEGAL COUNSEL BEFORE USE]\n\n"
    "I understand that Benton Drones may conduct aerial survey and imaging activities "
    "on or near the property I provide. I release Benton Drones and its operator from "
    "claims arising from participation, to the extent permitted by law. I confirm I am "
    "at least 18 years old and have the authority to authorize access to this property."
)
SIGNATURE_DISCLAIMER = (
    "I understand that typing my full legal name below constitutes a legally binding "
    "electronic signature, and I agree to be bound by the waiver shown above."
)


@dataclass(frozen=True)
class SignupInput:
    first_name: str
    last_name: str
    email: str
    phone: str
    address_line1: str
    city: str
    state: str
    postal_code: str
    consent_accepted: bool
    waiver_accepted: bool
    typed_name: str
    address_line2: str = ""
    notes: str = ""
    campaign: str = ""
    source: str = ""
    variant_slug: str = "default"
    shopify_shop_domain: str = ""
    shopify_customer_id: str = ""
    shopify_page_url: str = ""

    @property
    def full_address(self) -> str:
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.postal_code]
        return ", ".join(part.strip() for part in parts if part and part.strip())


@dataclass(frozen=True)
class LeadPoint:
    signup_id: int
    name: str
    latitude: float
    longitude: float


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
