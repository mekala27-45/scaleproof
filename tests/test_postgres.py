"""Opt-in tests against disposable CI PostgreSQL, never the hosted database."""
import concurrent.futures
import json
import os
import subprocess
import sys
import unittest
from scaleproof.storage import Store, StoreError
from scaleproof.policy import DEFAULT


@unittest.skipUnless(os.getenv("SCALEPROOF_PG_TEST_DSN"), "Disposable PostgreSQL not configured")
class PostgresTests(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ["SCALEPROOF_PG_TEST_DSN"]
        self.store = Store(self.dsn, live=True)
        self.store.migrate()
        self.token = self.store.new_session()

    def test_parallel_replay_visible_from_independent_connection(self):
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            rows = list(pool.map(lambda _: Store(self.dsn, live=True).create(self.token, "pg-parallel", DEFAULT), range(8)))
        self.assertEqual(len({row["plan_check_id"] for row in rows}), 1)
        with self.store.connection() as connection:
            row = self.store.sql(connection, "SELECT COUNT(*) AS n FROM physical_attempts WHERE session_hash = ?", (self.store.token_hash(self.token),)).fetchone()
            self.assertEqual(row["n"], 8)
        receipt = Store(self.dsn, live=True).get(self.token, rows[0]["plan_check_id"])
        self.assertEqual(receipt["input_digest"], rows[0]["input_digest"])

    def test_committed_operation_survives_process_death(self):
        code = "from scaleproof.storage import Store; from scaleproof.policy import DEFAULT; import os,sys; Store(os.environ['SCALEPROOF_PG_TEST_DSN'],live=True).create(sys.argv[1],'pg-death',DEFAULT); os._exit(17)"
        process = subprocess.run([sys.executable, "-c", code, self.token], capture_output=True)
        self.assertEqual(process.returncode, 17, process.stderr.decode())
        receipt = Store(self.dsn, live=True).create(self.token, "pg-death", DEFAULT)
        self.assertTrue(receipt["replay"])
        with self.assertRaises(StoreError) as error:
            self.store.create(self.token, "pg-death", {**DEFAULT, "high_rps": 11})
        self.assertEqual(error.exception.status, 409)
