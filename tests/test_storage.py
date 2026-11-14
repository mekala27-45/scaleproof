import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from scaleproof.policy import DEFAULT
from scaleproof.storage import Store, StoreError


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "receipts.db")
        self.store = Store(self.db)
        self.store.migrate()
        self.token = self.store.new_session()

    def tearDown(self):
        self.temp.cleanup()

    def test_replay_conflict_and_cross_session(self):
        a = self.store.create(self.token, "abcdefgh", DEFAULT)
        self.assertTrue(self.store.create(self.token, "abcdefgh", DEFAULT)["replay"])
        with self.assertRaises(StoreError) as err:
            self.store.create(self.token, "abcdefgh", {**DEFAULT, "high_rps": 11})
        self.assertEqual(err.exception.status, 409)
        with Store(self.db).connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM receipts").fetchone()[0], 1)
            outcomes = [r[0] for r in connection.execute("SELECT outcome FROM physical_attempts ORDER BY observed_at")]
            self.assertEqual(outcomes, ["created", "replay", "conflict"])
        with self.assertRaises(StoreError):
            self.store.get(self.store.new_session(), a["plan_check_id"])

    def test_parallel_identical_requests_commit_once(self):
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            rows = list(pool.map(lambda _: Store(self.db).create(self.token, "parallel-key", DEFAULT), range(8)))
        self.assertEqual(len({r["plan_check_id"] for r in rows}), 1)
        self.assertEqual(sum(not r["replay"] for r in rows), 1)
        with Store(self.db).connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM physical_attempts").fetchone()[0], 8)

    def test_commit_then_process_death_readback(self):
        # Child commits and exits without delivering a receipt to its caller.
        code = "from scaleproof.storage import Store; from scaleproof.policy import DEFAULT; import os,sys; Store(sys.argv[1]).create(sys.argv[2], 'dead-client', DEFAULT); os._exit(17)"
        proc = subprocess.run([sys.executable, "-c", code, self.db, self.token], capture_output=True)
        self.assertEqual(proc.returncode, 17)
        code = "from scaleproof.storage import Store; from scaleproof.policy import DEFAULT; import json,sys; print(json.dumps(Store(sys.argv[1]).create(sys.argv[2], 'dead-client', DEFAULT)))"
        row = json.loads(subprocess.check_output([sys.executable, "-c", code, self.db, self.token], text=True))
        self.assertTrue(row["replay"])
        self.assertEqual(Store(self.db).get(self.token, row["plan_check_id"])["input_digest"], row["input_digest"])

    def test_budget_and_expiry(self):
        with self.store.connection(True) as c:
            c.execute("UPDATE sessions SET attempts = 50")
        with self.assertRaises(StoreError) as err:
            self.store.create(self.token, "budget-key", DEFAULT)
        self.assertEqual(err.exception.status, 429)
        with self.store.connection(True) as c:
            c.execute("UPDATE sessions SET expires = 0")
        with self.assertRaises(StoreError) as err:
            self.store.get(self.token, "none")
        self.assertEqual(err.exception.status, 401)
