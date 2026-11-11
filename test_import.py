import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from main import create_app


class ImportTest(unittest.TestCase):
    def setUp(self):
        self.folder = self.enterContext(tempfile.TemporaryDirectory())
        self.client = self.enterContext(TestClient(create_app(Path(self.folder) / "test.sqlite3")))

    def test_preview_then_import_and_retry(self):
        source = Path("demo.csv").read_text(encoding="utf-8")
        preview = self.client.post("/preview", files={"file": ("demo.csv", source, "text/csv")})
        self.assertIn("2 valid, 2 invalid", preview.text)
        self.assertNotIn("DESK-01", self.client.get("/").text)
        imported = self.client.post("/import", data={"source": source})
        self.assertIn("2 inserted, 0 already saved, 2 invalid", imported.text)
        repeated = self.client.post("/import", data={"source": source})
        self.assertIn("0 inserted, 2 already saved, 2 invalid", repeated.text)
        self.assertIn("DESK-01", self.client.get("/").text)
        self.assertNotIn("CHAIR-01", self.client.get("/").text)

    def test_confirmation_revalidates_and_escapes_uploaded_text(self):
        invalid = self.client.post("/import", data={"source": "wrong,header\nA,2"})
        self.assertEqual(invalid.status_code, 400)
        source = "sku,name,quantity\nDEMO,<em>sample</em>,3"
        self.client.post("/import", data={"source": source})
        self.assertIn("&lt;em&gt;sample&lt;/em&gt;", self.client.get("/").text)
        self.assertNotIn("<em>sample</em>", self.client.get("/").text)
