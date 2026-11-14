"""Pure admission policy. This module has no execution dependency."""
from fractions import Fraction
import math
from .common import digest

POLICY_REVISION = "scaleproof-policy-v1"
FIELDS = {"schema_version", "low_rps", "high_rps", "duration_seconds", "warmup_seconds",
          "high_start_seconds", "high_end_seconds", "min_replicas", "max_replicas", "request_timeout_seconds"}
INTEGERS = FIELDS - {"low_rps", "high_rps", "request_timeout_seconds"}
MAX_ARRIVALS = 50000
DEFAULT = dict(schema_version=1, low_rps=2, high_rps=10, duration_seconds=720,
               warmup_seconds=60, high_start_seconds=180, high_end_seconds=480,
               min_replicas=1, max_replicas=3, request_timeout_seconds=5)


def normalize(payload):
    if not isinstance(payload, dict) or set(payload) != FIELDS:
        raise ValueError("Provide exactly the workload fields. Targets and unknown fields are not accepted.")
    result = {}
    for k, v in payload.items():
        if type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1e9:
            raise ValueError(f"{k} must be a finite number with the declared unit.")
        if k in INTEGERS and type(v) is not int:
            raise ValueError(f"{k} must be an integer.")
        result[k] = int(v) if v == int(v) else v
    if result["schema_version"] != 1:
        raise ValueError("Unsupported schema_version.")
    return result


def check(payload):
    p = normalize(payload)
    phase_ok = 0 <= p["warmup_seconds"] < p["high_start_seconds"] < p["high_end_seconds"] < p["duration_seconds"]
    rules = [
        ("rate", 0 < p["low_rps"] <= p["high_rps"] <= 100, "Rates must be positive, ordered and at most 100 requests/s."),
        ("duration", 1 <= p["duration_seconds"] <= 900, "Duration must be 1 to 900 seconds."),
        ("phases", phase_ok, "Require warmup < high start < high end < duration, in seconds."),
        ("replicas", 1 <= p["min_replicas"] <= p["max_replicas"] <= 3, "Replicas must be ordered from 1 through 3."),
        ("deadline", 1 <= p["request_timeout_seconds"] <= 10, "Request deadline must be 1 to 10 seconds.")]
    budget = None
    if phase_ok and p["low_rps"] > 0 and p["high_rps"] > 0:
        high = p["high_end_seconds"] - p["high_start_seconds"]
        budget = math.ceil(Fraction(str(p["low_rps"])) * (p["duration_seconds"] - high)
                           + Fraction(str(p["high_rps"])) * high)
    rules.append(("arrival_budget", budget is not None and budget <= MAX_ARRIVALS,
                  "The integrated-rate policy budget must not exceed 50000 arrivals."))
    return {"decision": "accepted" if all(r[1] for r in rules) else "rejected",
            "rules": [{"rule": k, "passed": ok, "message": msg} for k, ok, msg in rules],
            "expected_arrival_budget": budget, "budget_unit": "planned_arrivals",
            "budget_definition": "Ceiling of integrated offered rate over all phases; not a stochastic count or measured throughput.",
            "policy_revision": POLICY_REVISION, "input_digest": digest(p), "normalized_input": p}
