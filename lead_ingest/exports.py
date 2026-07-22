from __future__ import annotations

import csv
import io
import json
import sqlite3
import xml.etree.ElementTree as ET


def export_csv(rows: list[sqlite3.Row]) -> str:
    output = io.StringIO()
    fields = [
        "id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "full_address",
        "latitude",
        "longitude",
        "geocode_status",
        "campaign",
        "source",
        "variant_slug",
        "shopify_shop_domain",
        "shopify_customer_id",
        "shopify_page_url",
        "consent_version",
        "consent_accepted_at",
        "signed_name",
        "signed_at",
        "waiver_version",
        "signature_disclaimer",
        "created_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        row_dict = dict(row)
        writer.writerow({field: row_dict.get(field, "") for field in fields})
    return output.getvalue()


def export_geojson(rows: list[sqlite3.Row]) -> str:
    features = []
    for row in rows:
        if row["latitude"] is None or row["longitude"] is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]},
                "properties": {
                    "id": row["id"],
                    "name": f"{row['first_name']} {row['last_name']}",
                    "email": row["email"],
                    "address": row["full_address"],
                    "campaign": row["campaign"],
                    "source": row["source"],
                    "variant_slug": row["variant_slug"],
                    "shopify_shop_domain": row["shopify_shop_domain"],
                    "geocode_status": row["geocode_status"],
                },
            }
        )
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2)


def export_kml(rows: list[sqlite3.Row]) -> str:
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = ET.SubElement(kml, "Document")
    ET.SubElement(document, "name").text = "Benton Drones Leads"

    for row in rows:
        if row["latitude"] is None or row["longitude"] is None:
            continue
        placemark = ET.SubElement(document, "Placemark")
        ET.SubElement(placemark, "name").text = f"{row['first_name']} {row['last_name']}"
        ET.SubElement(placemark, "description").text = (
            f"{row['full_address']} | email: {row['email']}"
        )
        point = ET.SubElement(placemark, "Point")
        ET.SubElement(point, "coordinates").text = f"{row['longitude']},{row['latitude']},0"

    return ET.tostring(kml, encoding="unicode", xml_declaration=True)
