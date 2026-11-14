"""Response-independent exponential arrivals with reproducible bytes."""
import random
from .common import digest

PHASES = [("warmup", 0, 60, "low_rps"), ("low_before", 60, 180, "low_rps"),
          ("high", 180, 480, "high_rps"), ("low_after", 480, 660, "low_rps")]


def generate(low_rps, high_rps, seed, queries, cap=50000):
    if not 0 < low_rps <= high_rps <= 100 or not queries:
        raise ValueError("Invalid offered rate or empty query inventory")
    rng = random.Random(seed)
    rates = dict(low_rps=low_rps, high_rps=high_rps)
    queries = sorted(queries, key=lambda q: q["id"])
    rows = []
    for phase, begin, end, key in PHASES:
        t = float(begin)
        while True:
            t += rng.expovariate(rates[key])
            if t >= end:
                break
            if len(rows) >= cap:
                raise ValueError("Frozen schedule exceeds total request cap")
            q = queries[len(rows) % len(queries)]
            rows.append(dict(id=f"arrival-{len(rows):06}", scheduled_seconds=round(t, 9), phase=phase, query_id=q["id"], query=q["query"]))
    return dict(schema_version=1, seed=seed, duration_seconds=720, drain_start_seconds=660,
                rows=rows, schedule_digest=digest(rows), expected_count=len(rows))


def verify(schedule):
    rows = schedule["rows"]
    if not rows or digest(rows) != schedule["schedule_digest"] or len(rows) != schedule["expected_count"]:
        raise ValueError("Missing or changed schedule")
    if len({r["id"] for r in rows}) != len(rows) or rows != sorted(rows, key=lambda r: r["scheduled_seconds"]):
        raise ValueError("Duplicate or unordered scheduled requests")
    if len(rows) > 50000 or any(not 0 <= r["scheduled_seconds"] < 660 for r in rows):
        raise ValueError("Schedule exceeds fixed safety limits")
    return schedule
