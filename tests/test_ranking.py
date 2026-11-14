import unittest
from scaleproof.ranking import fuse, BM25
from scaleproof.common import ROOT, read_json


class RankingTests(unittest.TestCase):
    def test_independent_rrf(self):
        got = fuse([["a", "b", "c"], ["b", "a", "c"]], k=0)
        self.assertEqual(got, [("a", 1.5), ("b", 1.5), ("c", 2/3)])
        with self.assertRaises(ValueError):
            fuse([["a", "a"]])

    def test_lexical_tie_is_stable(self):
        docs = [{"id": "b", "title": "same", "text": "same"}, {"id": "a", "title": "same", "text": "same"}]
        self.assertEqual(BM25(docs).search("same")[0][0], "a")

    def test_fixture_inventory_and_split(self):
        docs = read_json(ROOT / "fixtures/corpus/notes.json")
        dev = read_json(ROOT / "fixtures/development/queries.json")
        reserved = read_json(ROOT / "fixtures/reserved/queries.json")
        self.assertEqual((len(docs), len(dev), len(reserved)), (24, 12, 12))
        self.assertFalse({q["expected_id"] for q in dev} & {q["expected_id"] for q in reserved})
