"""Exact BM25 and reciprocal rank fusion, with stable document ties."""
from collections import Counter
import math
import re


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25:
    def __init__(self, documents):
        self.rows = [(d["id"], Counter(tokenize(d["title"] + " " + d["text"]))) for d in documents]
        self.average_length = sum(sum(c.values()) for _, c in self.rows) / len(self.rows)
        self.df = Counter(t for _, c in self.rows for t in c)

    def search(self, query):
        n, k1, b = len(self.rows), 1.5, .75
        scores = []
        for ident, counts in self.rows:
            length = sum(counts.values())
            score = 0.
            for t in tokenize(query):
                freq = counts[t]
                idf = math.log(1 + (n - self.df[t] + .5) / (self.df[t] + .5))
                score += idf * freq * (k1 + 1) / (freq + k1 * (1 - b + b * length / self.average_length))
            scores.append((ident, score))
        return sorted(scores, key=lambda row: (-row[1], row[0]))


def fuse(rankings, k=60):
    scores = {}
    for ranking in rankings:
        if len(ranking) != len(set(ranking)):
            raise ValueError("Duplicate document in ranking")
        for rank, ident in enumerate(ranking, 1):
            scores[ident] = scores.get(ident, 0.) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda row: (-row[1], row[0]))
