import unittest
from scaleproof.policy import DEFAULT, check, normalize


class PolicyTests(unittest.TestCase):
    def test_known_budget(self):
        self.assertEqual(check(DEFAULT)["expected_arrival_budget"], 3840)
        self.assertEqual(check(DEFAULT)["decision"], "accepted")

    def test_rejections_and_missing(self):
        for field, value in [("high_rps", 101), ("duration_seconds", 901), ("max_replicas", 4), ("warmup_seconds", 180), ("request_timeout_seconds", .1)]:
            with self.subTest(field=field):
                self.assertEqual(check({**DEFAULT, field: value})["decision"], "rejected")
        for payload in [{}, {**DEFAULT, "target_url": "https://example.com"}, {**DEFAULT, "low_rps": "2"}, {**DEFAULT, "max_replicas": True}, {**DEFAULT, "low_rps": float("nan")}]:
            with self.assertRaises(ValueError):
                check(payload)

    def test_digest_normalizes_equivalent_rates(self):
        self.assertEqual(check(DEFAULT)["input_digest"], check({**DEFAULT, "low_rps": 2.0})["input_digest"])

    def test_fractional_budget_rounds_up(self):
        p = {**DEFAULT, "low_rps": .101, "high_rps": .201}
        self.assertEqual(check(p)["expected_arrival_budget"], 103)

    def test_tiny_positive_rate_is_not_rounded_out_of_ceiling(self):
        self.assertEqual(check({**DEFAULT, "low_rps": 1e-30, "high_rps": 1})["expected_arrival_budget"], 301)
