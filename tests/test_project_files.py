"""Tests for project-level files: .gitignore, requirements.txt, pyproject.toml, Makefile."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectFilesTests(unittest.TestCase):
    def test_gitignore_exists(self):
        gitignore = ROOT / ".gitignore"
        self.assertTrue(gitignore.exists())
        content = gitignore.read_text()
        self.assertIn("data/", content)
        self.assertIn("__pycache__/", content)
        self.assertIn("*.pyc", content)
        self.assertIn(".DS_Store", content)
        self.assertIn(".tools/", content)
        self.assertIn(".dolt/", content)
        self.assertIn(".env", content)
        self.assertIn("qa_screenshots/", content)
        self.assertIn("dist/", content)
        self.assertIn("build/", content)

    def test_requirements_txt_exists(self):
        req = ROOT / "requirements.txt"
        self.assertTrue(req.exists())
        content = req.read_text()
        self.assertIn("fpdf2", content)

    def test_pyproject_toml_exists(self):
        pyproject = ROOT / "pyproject.toml"
        self.assertTrue(pyproject.exists())
        content = pyproject.read_text()
        self.assertIn("benton-drones-lead-ingest", content)
        self.assertIn(">=3.11", content)
        self.assertIn("fpdf2", content)

    def test_makefile_exists_with_targets(self):
        makefile = ROOT / "Makefile"
        self.assertTrue(makefile.exists())
        content = makefile.read_text()
        for target in ("install:", "test:", "run:", "init-db:"):
            self.assertIn(target, content)

    def test_makefile_run_sets_admin_password(self):
        makefile = (ROOT / "Makefile").read_text()
        self.assertIn("ADMIN_PASSWORD", makefile)

    def test_makefile_test_uses_unittest_discover(self):
        makefile = (ROOT / "Makefile").read_text()
        self.assertIn("unittest discover", makefile)

    def test_code_puppy_readme_exists(self):
        readme = ROOT / ".code_puppy" / "README.md"
        self.assertTrue(readme.exists())
        content = readme.read_text()
        self.assertIn("make test", content)
        self.assertIn("make run", content)

    def test_landing_page_html_exists(self):
        landing = ROOT / "static" / "landing-page.html"
        self.assertTrue(landing.exists())
        content = landing.read_text()
        self.assertIn("Benton Drones", content)
        self.assertIn("/signup", content)
        self.assertIn("Jost", content)
        self.assertIn("Cinematic FPV", content)
        self.assertIn("Aerial Surveys", content)
        self.assertIn("Part 107", content)
        self.assertIn("How it works", content)

    def test_landing_page_has_footer_links(self):
        content = (ROOT / "static" / "landing-page.html").read_text()
        self.assertIn("/overview", content)
        self.assertIn("/admin", content)


if __name__ == "__main__":
    unittest.main()
