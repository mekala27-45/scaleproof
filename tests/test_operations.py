import unittest
from unittest.mock import patch
from scaleproof.operations import cpu_millicores,baseline


class OperationTests(unittest.TestCase):
    def test_cpu_units(self):
        self.assertEqual(cpu_millicores("1000000n"),1)
        self.assertEqual(cpu_millicores("1500u"),1.5)
        self.assertEqual(cpu_millicores("250m"),250)
        self.assertEqual(cpu_millicores(".5"),500)

    @patch("scaleproof.operations.verify_owner")
    @patch("scaleproof.operations.kubectl")
    @patch("scaleproof.operations.write_json")
    @patch("scaleproof.operations.time.sleep")
    def test_baseline_retries_transient_startup_metrics(self,*mocks):
        ready=dict(desired=1,current=1,ready=1,pods=[{}],metrics_age_seconds=1)
        with patch("scaleproof.operations.observe",side_effect=[RuntimeError("metrics unavailable"),ready]) as observe:
            self.assertEqual(baseline("fixed"),ready)
            self.assertEqual(observe.call_count,2)
