import json
import sqlite3
import unittest

from lead_ingest.db import create_signup, get_export_rows, init_db, list_signups
from lead_ingest.exports import export_csv, export_geojson, export_kml
from lead_ingest.models import SignupInput


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)
        create_signup(
            self.conn,
            SignupInput(
                first_name="Katherine",
                last_name="Johnson",
                email="kj@example.com",
                phone="555-1111",
                address_line1="3 Orbit Ave",
                city="Bentonville",
                state="AR",
                postal_code="72712",
                consent_accepted=True,
                waiver_accepted=True,
                typed_name="Katherine Johnson",
            ),
        )
        self.rows = list_signups(self.conn)
        self.export_rows = get_export_rows(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_csv_export_contains_header_and_lead(self):
        content = export_csv(self.export_rows)
        self.assertIn("first_name", content)
        self.assertIn("Katherine", content)
        self.assertIn("signed_name", content)
        self.assertIn("waiver_version", content)

    def test_geojson_export_is_feature_collection(self):
        payload = json.loads(export_geojson(self.rows))
        self.assertEqual(payload["type"], "FeatureCollection")
        self.assertEqual(len(payload["features"]), 1)

    def test_kml_export_contains_placemark(self):
        content = export_kml(self.rows)
        self.assertIn("Placemark", content)
        self.assertIn("Katherine Johnson", content)

    def test_csv_export_empty_data(self):
        """CSV export with no rows still produces a header row."""
        content = export_csv([])
        lines = content.strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("first_name", lines[0])
        self.assertIn("signed_name", lines[0])

    def test_geojson_export_empty_data(self):
        payload = json.loads(export_geojson([]))
        self.assertEqual(payload["type"], "FeatureCollection")
        self.assertEqual(len(payload["features"]), 0)

    def test_kml_export_empty_data(self):
        content = export_kml([])
        self.assertIn("<kml", content)
        self.assertIn("Benton Drones Leads", content)
        self.assertNotIn("Placemark", content)

    def test_geojson_filters_non_geocoded_leads(self):
        """Leads with null latitude/longitude are excluded from GeoJSON."""
        # Manually null out the coordinates on our existing lead.
        self.conn.execute("UPDATE signups SET latitude = NULL, longitude = NULL")
        self.conn.commit()
        rows = list_signups(self.conn)
        payload = json.loads(export_geojson(rows))
        self.assertEqual(len(payload["features"]), 0)

    def test_kml_filters_non_geocoded_leads(self):
        """Leads with null latitude/longitude are excluded from KML."""
        self.conn.execute("UPDATE signups SET latitude = NULL, longitude = NULL")
        self.conn.commit()
        rows = list_signups(self.conn)
        content = export_kml(rows)
        self.assertNotIn("Placemark", content)

    def test_csv_includes_all_signature_metadata_columns(self):
        content = export_csv(self.export_rows)
        for column in ("consent_version", "consent_accepted_at", "signed_name",
                        "signed_at", "waiver_version", "signature_disclaimer"):
            self.assertIn(column, content, f"Missing CSV column: {column}")

    def test_csv_contains_lead_data(self):
        content = export_csv(self.export_rows)
        self.assertIn("Katherine", content)
        self.assertIn("Johnson", content)
        self.assertIn("kj@example.com", content)
        self.assertIn("3 Orbit Ave", content)

    def test_geojson_coordinates_order_is_lng_lat(self):
        """GeoJSON spec requires [longitude, latitude] order."""
        payload = json.loads(export_geojson(self.rows))
        coords = payload["features"][0]["geometry"]["coordinates"]
        self.assertEqual(len(coords), 2)
        # Longitude should be negative (NWA is west of prime meridian).
        self.assertLess(coords[0], 0)
        # Latitude should be positive (NWA is north of equator).
        self.assertGreater(coords[1], 0)

    def test_kml_coordinates_format(self):
        content = export_kml(self.rows)
        # KML coordinates are lng,lat,altitude.
        self.assertIn(",0</coordinates>", content)


if __name__ == "__main__":
    unittest.main()
