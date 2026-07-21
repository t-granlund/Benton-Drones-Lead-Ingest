import unittest

from lead_ingest.server import page


class ServerTests(unittest.TestCase):
    def test_page_returns_bytes(self):
        content = page("Hello", "<p>World</p>")
        self.assertIsInstance(content, bytes)
        self.assertIn(b"World", content)


if __name__ == "__main__":
    unittest.main()
