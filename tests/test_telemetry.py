import concurrent.futures
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scaleproof.telemetry import append_event

class TelemetryTests(unittest.TestCase):
    def test_parallel_append_survives_reader_restart(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{"SCALEPROOF_EVENT_DIR":directory}):
            records=[{"pod_uid":"pod-123","event":"finished","request_id":str(i)} for i in range(200)]
            with concurrent.futures.ThreadPoolExecutor(8) as executor: list(executor.map(append_event,records))
            rows=[json.loads(line) for line in (Path(directory)/"pod-123.jsonl").read_text().splitlines()]
            self.assertEqual({r["request_id"] for r in rows},{str(i) for i in range(200)})
            self.assertEqual(len(rows),200)
    def test_invalid_pod_path_is_refused(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{"SCALEPROOF_EVENT_DIR":directory}):
            with self.assertRaises(ValueError): append_event({"pod_uid":"../escape"})
            self.assertEqual(list(Path(directory).iterdir()),[])
    def test_missing_spool_does_not_silently_report_persistence(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{"SCALEPROOF_EVENT_DIR":directory+"/absent"}):
            with self.assertRaises(FileNotFoundError): append_event({"pod_uid":"pod-123"})
