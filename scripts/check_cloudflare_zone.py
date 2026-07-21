from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API_BASE = "https://api.cloudflare.com/client/v4"
ZONE_NAME = "bentondrones.com"


def cloudflare_get(path: str, token: str) -> dict:
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID", "")

    print("Benton Drones Cloudflare Read-Only Check")
    print("========================================")

    if not token:
        print("[WARN] CLOUDFLARE_API_TOKEN is not set. Create a read-only token first.")
        return 0

    try:
        zone_lookup = cloudflare_get(f"/zones?name={ZONE_NAME}", token)
    except urllib.error.HTTPError as exc:
        print(f"[FAIL] Cloudflare API rejected request: HTTP {exc.code}")
        return 1
    except urllib.error.URLError as exc:
        print(f"[FAIL] Could not reach Cloudflare API: {exc}")
        return 1

    zones = zone_lookup.get("result", [])
    if not zones:
        print(f"[WARN] Zone not found in Cloudflare: {ZONE_NAME}")
        return 0

    zone = zones[0]
    discovered_zone_id = zone.get("id", "")
    print(f"[PASS] Zone found: {zone.get('name')} ({zone.get('status')})")
    print(f"[INFO] Zone ID: {discovered_zone_id}")
    print(f"[INFO] Nameservers: {', '.join(zone.get('name_servers', []))}")

    if zone_id and zone_id != discovered_zone_id:
        print("[WARN] CLOUDFLARE_ZONE_ID does not match discovered zone ID")

    records = cloudflare_get(f"/zones/{discovered_zone_id}/dns_records?per_page=100", token)
    print("\nDNS Records")
    print("-----------")
    for record in records.get("result", []):
        proxied = record.get("proxied")
        proxied_label = "proxied" if proxied else "dns-only"
        print(f"{record.get('type'):5} {record.get('name'):35} -> {record.get('content')} ({proxied_label})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
