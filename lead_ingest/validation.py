from __future__ import annotations

import re
from typing import Iterable

from lead_ingest.models import SignupInput

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ZIP_RE = re.compile(r"^\d{5}(?:-\d{4})?$")
STATE_RE = re.compile(r"^[A-Za-z]{2}$")


class ValidationError(ValueError):
    def __init__(self, errors: Iterable[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


def validate_signup(data: SignupInput) -> None:
    errors: list[str] = []
    required = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "address_line1": data.address_line1,
        "city": data.city,
        "state": data.state,
        "postal_code": data.postal_code,
    }

    for field, value in required.items():
        if not value or not value.strip():
            errors.append(f"{field} is required")

    if data.email and not EMAIL_RE.match(data.email.strip()):
        errors.append("email must be valid")

    if data.state and not STATE_RE.match(data.state.strip()):
        errors.append("state must be a 2-letter code")

    if data.postal_code and not ZIP_RE.match(data.postal_code.strip()):
        errors.append("postal_code must be a valid US ZIP code")

    if not data.consent_accepted:
        errors.append("consent is required")

    if not data.waiver_accepted:
        errors.append("waiver agreement is required")

    if not data.typed_name or not data.typed_name.strip():
        errors.append("typed legal name is required")

    if errors:
        raise ValidationError(errors)
