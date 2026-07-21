from __future__ import annotations

import os
import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    area: str
    status: str
    message: str


def env_check(name: str, required_now: bool = False) -> Item:
    value = os.environ.get(name, "")
    if value:
        return Item("Secrets", "PASS", f"{name} is set")
    if required_now:
        return Item("Secrets", "WARN", f"{name} is not set")
    return Item("Secrets", "INFO", f"{name} not set yet")


def host_check(hostname: str) -> Item:
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, None)})
    except socket.gaierror:
        return Item("DNS", "WARN", f"{hostname} is not resolving yet")
    return Item("DNS", "PASS", f"{hostname} resolves to {', '.join(addresses)}")


def main() -> int:
    items = [
        host_check("bentondrones.com"),
        host_check("www.bentondrones.com"),
        host_check("leads.bentondrones.com"),
        env_check("CLOUDFLARE_API_TOKEN"),
        env_check("CLOUDFLARE_ZONE_ID"),
        env_check("SHOPIFY_STORE_DOMAIN"),
        env_check("SHOPIFY_ADMIN_ACCESS_TOKEN"),
        env_check("SHOPIFY_APP_SECRET"),
        env_check("ADMIN_PASSWORD", required_now=True),
        env_check("ADMIN_SESSION_SECRET", required_now=True),
        env_check("CSRF_SECRET", required_now=True),
    ]

    print("Benton Drones Platform Preflight Report")
    print("======================================")
    for item in items:
        print(f"[{item.status}] {item.area}: {item.message}")

    print("\nNext manual confirmations still required:")
    print("- Namecheap current nameservers and DNS screenshots")
    print("- Shopify required A/CNAME records")
    print("- Google Workspace MX/SPF/DKIM/DMARC confirmation")
    print("- Backend hosting target for leads.bentondrones.com")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
