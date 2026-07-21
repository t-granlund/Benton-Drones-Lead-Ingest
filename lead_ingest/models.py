from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

CONSENT_VERSION = "2026-07-06.v1"
CONSENT_TEXT = (
    "I consent to Benton Drones contacting me about drone delivery simulations. "
    "I understand this signup is for planning and simulation purposes and does not "
    "guarantee service availability."
)

WAIVER_VERSION = "2026-07-21.v1"
# Based on provided consent form PDF; must be reviewed by legal counsel before production use.
WAIVER_TEXT = """\
Benton Drones Confidential
BENTON DRONES CONSENT FORM

Name:
Address (\u201cProperty\u201d):
Date:
Phone & Email:

By signing this Release, I hereby grant permission for Benton Drones and/or its
representatives, agents, or assigns (individually or collectively, \u201cBenton
Drones\u201d) to enter and remain on the Property, with equipment, including but
not limited to still or video cameras and a commercial drone, for the purpose of
collecting still or video images or sound recordings (individually or
collectively, \u201cRecordings\u201d), in connection with research and development
of safe and precise drone delivery operations.

This permission includes the right to take motion pictures, videotapes, still
photographs and/or sound recordings on and of any and all portions of the
Property.

I also grant permission to being and/or having been photographed, filmed and/or
recorded at the Property on the Date specified above. I understand that, if I do
not wish to be photographed, filmed, and/or recorded, that it is my exclusive
responsibility to stay indoors and away from the photographed, filmed, and/or
recorded portions of the property during such photography, filming, and or
recording. For more information about how we collect, use, and retain your personal
information and your rights, as well as Benton Drones\u2019 vision data collection
practices, please see our Privacy Policy at [PRIVACY POLICY URL \u2014 REPLACE
BEFORE USE] and [VISION POLICY URL \u2014 REPLACE BEFORE USE].

To the extent that other individuals are photographed, filmed, and/or recorded, I
represent that I have obtained all necessary consents from such individuals for
them to be photographed, filmed, or recorded and for such photographs, film, or
recording to be used for the purposes described in this Release. I have also
provided such individuals with the URL of Benton Drones\u2019 Privacy Policy
referenced in the preceding paragraph.

I also grant to Benton Drones and its successors, assigns, agents, licensees
(through multiple tiers), affiliates and representatives the right and permission
to process, analyse, study, copyright, copy, create derivative works of, print,
reproduce, and otherwise use for any lawful purpose, in whole or in part, through
any means or medium (now known or hereafter created) without limitation, the
Recordings. I hereby assign to Benton Drones the perpetual, worldwide and
royalty-free right, title and interest in and to the Recordings and any and all
results and proceeds from any such use.

I certify that I have the full right and authority to enter into this agreement and
grant the rights herein granted, and that the consent or permission of no other
person, firm, or entity is necessary in order to enable you to exercise or enjoy
the rights herein granted.

AGREED AND ACCEPTED

By: ________________________________________
(print name)

Signature:
Date:
Referral name
"""
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
