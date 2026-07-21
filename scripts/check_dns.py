from __future__ import annotations

import socket
from dataclasses import dataclass

DOMAINS = [
    "bentondrones.com",
    "www.bentondrones.com",
    "leads.bentondrones.com",
]

DNS_TYPES = ["MX", "TXT"]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def resolve_host(hostname: str) -> CheckResult:
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, None)})
    except socket.gaierror as exc:
        return CheckResult(hostname, "WARN", f"not resolving yet: {exc}")
    return CheckResult(hostname, "PASS", ", ".join(addresses))


def main() -> int:
    print("Benton Drones DNS Readiness Check")
    print("================================")
    results = [resolve_host(domain) for domain in DOMAINS]
    for result in results:
        print(f"[{result.status}] {result.name}: {result.detail}")

    print("\nNote: MX/TXT lookups are platform-specific without extra dependencies.")
    print("Use these commands for deeper checks on Windows:")
    print("  nslookup -type=mx bentondrones.com")
    print("  nslookup -type=txt bentondrones.com")
    print("  nslookup -type=txt _dmarc.bentondrones.com")
    print("  nslookup -type=txt google._domainkey.bentondrones.com")

    return 0 if any(result.status == "PASS" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
