import unittest
from scaleproof.schedule import generate, verify, PHASES


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.queries = [{"id":"q2", "query":"two"}, {"id":"q1", "query":"one"}]

    def test_deterministic_complete_schedule(self):
        a = generate(.2, .5, 42, self.queries)
        b = generate(.2, .5, 42, self.queries[::-1])
        self.assertEqual(a, b)
        verify(a)
        for row in a["rows"]:
            begin, end = next((b,e) for p,b,e,_ in PHASES if p == row["phase"])
            self.assertTrue(begin <= row["scheduled_seconds"] < end)
        self.assertNotEqual(a["schedule_digest"], generate(.2,.5,43,self.queries)["schedule_digest"])

    def test_missing_changed_and_over_budget_refused(self):
        a = generate(.2,.5,42,self.queries)
        a["rows"].pop()
        with self.assertRaises(ValueError): verify(a)
        with self.assertRaises(ValueError): generate(10,20,1,self.queries,cap=2)
        with self.assertRaises(ValueError): generate(0,1,1,self.queries)
