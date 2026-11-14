import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
    from scaleproof import serving
except ImportError:
    TestClient = None


class TinyKernel:
    """Endpoint contract fixture only; never performance evidence."""
    def __init__(self, directory):
        self.encoder = SimpleNamespace(manifest={"bundle_digest": "model"})
        self.corpus_digest = "corpus"

    def retrieve(self, query):
        return {"results": [{"document_id": "note"}], "encoder_invocations": 1}


@unittest.skipIf(TestClient is None, "FastAPI test dependencies unavailable")
class ServingTests(unittest.TestCase):
    def test_admitted_request_finishes_and_emits_receipt(self):
        import contextlib
        import io
        import json
        output = io.StringIO()
        with patch.object(serving, "Kernel", TinyKernel), contextlib.redirect_stdout(output):
            with TestClient(serving.app) as client:
                self.assertEqual(client.get("/ready").status_code, 200)
                response = client.post("/infer", json={"query": "ready worker", "request_id": "contract-1", "timeout_seconds": 5})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["request_id"], "contract-1")
        events = [json.loads(line) for line in output.getvalue().splitlines() if line.startswith("{")]
        request_events = [e["event"] for e in events if e.get("request_id") == "contract-1"]
        self.assertEqual(request_events, ["admitted", "started", "finished"])
