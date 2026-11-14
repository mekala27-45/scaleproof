import tempfile
import unittest
from pathlib import Path
try:
    from fastapi.testclient import TestClient
    from scaleproof.api import create_app
except ImportError:
    TestClient = None
from scaleproof.policy import DEFAULT
from scaleproof.storage import Store


@unittest.skipIf(TestClient is None, "FastAPI test dependencies unavailable")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(str(Path(self.temp.name) / "test.db"))
        self.store.migrate()
        self.client = TestClient(create_app(self.store))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def test_full_receipt_flow(self):
        self.assertEqual(self.client.post("/v1/sessions", json={}).status_code, 201)
        h = {"Idempotency-Key": "browser-flow"}
        first = self.client.post("/v1/workload-checks", json=DEFAULT, headers=h)
        self.assertEqual(first.status_code, 200, first.text)
        row = first.json()
        self.assertEqual(self.client.get("/v1/workload-checks/" + row["plan_check_id"]).json(), row)
        self.assertTrue(self.client.post("/v1/workload-checks", json=DEFAULT, headers=h).json()["replay"])
        self.assertEqual(self.client.post("/v1/workload-checks", json={**DEFAULT, "high_rps": 12}, headers=h).status_code, 409)

    def test_input_boundaries(self):
        self.assertEqual(self.client.post("/v1/workload-checks", json={**DEFAULT, "url": "https://example.com"}).status_code, 422)
        self.assertEqual(self.client.post("/v1/sessions", json={}, headers={"Origin": "https://evil.invalid"}).status_code, 403)
        self.assertEqual(self.client.post("/v1/sessions", content="x" * 4097, headers={"Content-Type": "application/json"}).status_code, 413)
        self.assertEqual(self.client.post("/v1/sessions", content="hello").status_code, 415)
        self.assertEqual(self.client.get("/ready").status_code, 200)
