import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PRIMARY_KEYS = {
    "requirements.csv": "requirement_id",
    "tasks.csv": "task_id",
    "judges.csv": "judge_id",
    "evidence.csv": "evidence_id",
    "decisions.csv": "decision_id",
    "platform_snapshots.csv": "snapshot_id",
    "status_log.csv": "log_id",
}

ALLOWED_STATUSES = {
    "",
    "accepted",
    "blocked",
    "captured",
    "csv_only",
    "deferred",
    "dolt_backed",
    "failed",
    "in_progress",
    "needed",
    "needs_review",
    "not_ready",
    "not_started",
    "passed",
    "proposed",
    "ready",
    "superseded",
}

ALLOWED_RESULTS = {"", "PASS", "FAIL", "BLOCKED", "DEFERRED", "unknown", "WARN"}


def read_tracking_csv(name):
    with (ROOT / "tracking" / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class GoalsJudgesTrackingTests(unittest.TestCase):
    def test_goal_and_judge_indexes_exist(self):
        self.assertTrue((ROOT / "goals" / "README.md").exists())
        self.assertTrue((ROOT / "judges" / "README.md").exists())

    def test_requirement_goal_and_judge_files_exist(self):
        with (ROOT / "tracking" / "requirements.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertGreaterEqual(len(rows), 10)
        for row in rows:
            self.assertTrue((ROOT / row["goal_file"]).exists(), row["goal_file"])
            self.assertTrue((ROOT / row["judge_file"]).exists(), row["judge_file"])

    EXPECTED_HEADERS = {
        "requirements.csv": ["requirement_id", "goal_file", "judge_file", "status"],
        "tasks.csv": ["task_id", "requirement_id", "title", "status"],
        "judges.csv": ["judge_id", "requirement_id", "judge_file", "status"],
        "evidence.csv": ["evidence_id", "type", "source", "command_or_url"],
        "decisions.csv": ["decision_id", "domain", "title", "decision"],
        "platform_snapshots.csv": ["snapshot_id", "platform", "snapshot_type", "status"],
        "status_log.csv": ["log_id", "entity_type", "entity_id", "old_status"],
    }

    def test_tracking_csvs_are_parseable(self):
        for path in (ROOT / "tracking").glob("*.csv"):
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertIsNotNone(rows, path.name)
            expected = self.EXPECTED_HEADERS.get(path.name, [])
            if expected:
                self.assertGreater(len(rows), 0, path.name)
                first_row = rows[0]
                for column in expected:
                    self.assertIn(column, first_row, f"{path.name}: missing column {column}")

    def test_no_obvious_secret_values_in_tracking(self):
        forbidden = ["api_token=", "password=", "secret=", "private_key", "session="]
        for path in (ROOT / "tracking").glob("*.csv"):
            text = path.read_text(encoding="utf-8").lower()
            for item in forbidden:
                self.assertNotIn(item, text, path.name)

    def test_tracking_primary_keys_are_unique_and_present(self):
        for filename, key in PRIMARY_KEYS.items():
            rows = read_tracking_csv(filename)
            values = [row[key] for row in rows]
            self.assertTrue(all(values), filename)
            self.assertEqual(len(values), len(set(values)), filename)

    def test_requirement_references_exist(self):
        requirements = {row["requirement_id"] for row in read_tracking_csv("requirements.csv")}
        for filename in ("tasks.csv", "judges.csv"):
            for row in read_tracking_csv(filename):
                requirement_id = row.get("requirement_id", "")
                if requirement_id:
                    self.assertIn(requirement_id, requirements, f"{filename}: {requirement_id}")

    def test_evidence_references_exist(self):
        evidence = {row["evidence_id"] for row in read_tracking_csv("evidence.csv")}
        for filename in ("judges.csv", "status_log.csv"):
            for row in read_tracking_csv(filename):
                evidence_id = row.get("evidence_id", "")
                if evidence_id:
                    self.assertIn(evidence_id, evidence, f"{filename}: {evidence_id}")

    def test_status_values_are_known(self):
        for filename in ("requirements.csv", "tasks.csv", "judges.csv", "decisions.csv", "platform_snapshots.csv"):
            for row in read_tracking_csv(filename):
                status = row.get("status", "")
                self.assertIn(status, ALLOWED_STATUSES, f"{filename}: {status}")

        for row in read_tracking_csv("status_log.csv"):
            self.assertIn(row.get("old_status", ""), ALLOWED_STATUSES)
            self.assertIn(row.get("new_status", ""), ALLOWED_STATUSES)

        for row in read_tracking_csv("judges.csv"):
            self.assertIn(row.get("result", ""), ALLOWED_RESULTS)


if __name__ == "__main__":
    unittest.main()
