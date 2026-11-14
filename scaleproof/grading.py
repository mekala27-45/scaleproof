"""Independent raw-evidence grader. Never trusts producer summaries."""
from collections import Counter
import math
from .common import digest

STATUSES = {"completed", "timeout", "rejected", "error", "unfinished", "dispatch_failure"}


def percentile(values, fraction, minimum):
    if len(values) < minimum:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def replica_seconds(observations, start, end, key="ready"):
    if not observations or observations[0]["seconds"] > start or observations[-1]["seconds"] < end:
        raise ValueError("Observation window is not covered")
    if any(b["seconds"] <= a["seconds"] for a, b in zip(observations, observations[1:])):
        raise ValueError("Replica observations must be strictly ordered")
    total = 0.
    for a, b in zip(observations, observations[1:]):
        total += max(0, min(end, b["seconds"]) - max(start, a["seconds"])) * a[key]
    return total


def grade_run(schedule, ledger, observations, identity, lane, server_events=None):
    errors = []
    planned = schedule.get("rows", [])
    if not planned or not ledger or not observations or not identity:
        return {"status": "not_done", "errors": ["Required raw evidence is absent"], "metrics": None}
    if digest(planned) != schedule.get("schedule_digest"):
        errors.append("Schedule digest mismatch")
    expected = {r["id"]: r for r in planned}
    counts = Counter(r["id"] for r in ledger)
    if set(expected) != set(counts) or any(n != 1 for n in counts.values()) or len(expected) != len(planned):
        errors.append("Scheduled request inventory is missing, duplicated or extra")
    for row in ledger:
        if row.get("status") not in STATUSES:
            errors.append("Unknown terminal request status")
            continue
        plan = expected.get(row["id"])
        if plan and any(row.get(k) != plan.get(k) for k in ("scheduled_seconds", "phase", "query_id", "query")):
            errors.append("Ledger does not match frozen arrival")
        if row["status"] == "completed":
            receipt = row.get("receipt", {})
            if any(receipt.get(k) != identity.get(k) for k in ("model_digest", "corpus_digest", "source_revision", "image_identity")):
                errors.append("Successful response has wrong model, corpus, source or image identity")
            if receipt.get("encoder_invocations") != 1 or receipt.get("execution_mode") != "actual_cpu_inference":
                errors.append("Successful response lacks actual encoder execution")
            if receipt.get("request_id") != row.get("request_id") or not receipt.get("pod_uid"):
                errors.append("Response identity does not match request")
            if digest(receipt.get("results")) != receipt.get("output_digest") or digest(row.get("query")) != receipt.get("input_digest"):
                errors.append("Inference input or output digest mismatch")
            finished, dispatched = row.get("finished_seconds", math.inf), row.get("dispatched_seconds", math.inf)
            if not row["scheduled_seconds"] <= dispatched <= finished <= row["scheduled_seconds"] + identity["timeout_seconds"]:
                errors.append("Deadline success contradicts timing")
    if any(o.get("metrics_age_seconds", math.inf) > 45 for o in observations):
        errors.append("Metrics are missing or stale")
    if any(b["seconds"] - a["seconds"] > 20 for a,b in zip(observations,observations[1:])):
        errors.append("Observation gap exceeds 20 seconds")
    conditions_ok = all(o.get("hpa_active") is True for o in observations) if lane == "hpa" else True
    if not conditions_ok:
        errors.append("HPA ScalingActive or AbleToScale missing")
    successes = [r for r in ledger if r["status"] == "completed"]
    pod_uids = {r["receipt"]["pod_uid"] for r in successes}
    scale_up = next((o for o in observations if o["seconds"] >= 180 and o.get("desired", 0) > 1), None)
    ready_up = next((o for o in observations if o["seconds"] >= 180 and o.get("ready", 0) > 1), None)
    scale_down = next((o for o in observations if o["seconds"] >= 480 and ready_up and o["seconds"] > ready_up["seconds"] and o.get("ready") == 1), None)
    if lane == "hpa" and (not scale_up or not ready_up or not scale_down or len(pod_uids) < 2):
        errors.append("Observed scale-up, ready capacity, scale-down or multi-pod routing absent")
    if lane == "fixed" and any(o.get("desired") != 1 or o.get("ready") != 1 for o in observations):
        errors.append("Fixed lane did not remain at one ready replica")
    try:
        exposure = replica_seconds(observations, 60, 660)
        desired_exposure = replica_seconds(observations, 60, 660, "desired")
    except ValueError as exc:
        errors.append(str(exc))
        exposure = desired_exposure = None
    by_phase = {}
    for phase in ("warmup", "low_before", "high", "low_after"):
        rows = [r for r in ledger if r.get("phase") == phase]
        n = sum(r["phase"] == phase for r in planned)
        status = Counter(r["status"] for r in rows)
        completed = [r for r in rows if r["status"] == "completed"]
        scheduled_latency = [(r["finished_seconds"]-r["scheduled_seconds"])*1000 for r in completed]
        dispatch_latency = [(r["finished_seconds"]-r["dispatched_seconds"])*1000 for r in completed]
        by_phase[phase] = dict(scheduled=n, terminal_counts={s:status[s] for s in sorted(STATUSES)},
                               deadline_success_fraction=status["completed"]/n if n else None,
                               completed_latency_sample=len(completed), scheduled_p50_ms=percentile(scheduled_latency,.5,2),
                               scheduled_p95_ms=percentile(scheduled_latency,.95,20), scheduled_p99_ms=percentile(scheduled_latency,.99,100),
                               dispatch_p95_ms=percentile(dispatch_latency,.95,20))
    if any(r["status"] == "dispatch_failure" for r in ledger):
        errors.append("Client missed offered arrivals; paired latency comparison invalid")
    server_events = server_events or []
    admitted = {e["request_id"] for e in server_events if e.get("event") == "admitted"}
    finished = {e["request_id"] for e in server_events if e.get("event") == "finished"}
    if not admitted or any(r["request_id"] not in finished for r in successes):
        errors.append("Independent server accounting is absent or incomplete")
    late = [r["request_id"] for r in ledger if r["status"] != "completed" and r["request_id"] in finished]
    return dict(status="done" if not errors else "not_done", errors=sorted(set(errors)),
                metrics=dict(phases=by_phase, ready_replica_seconds=exposure, desired_replica_seconds=desired_exposure,
                             admitted=len(admitted), server_finished=len(finished), late_completions=len(late),
                             unique_serving_pods=len(pod_uids), scale_up_delay_seconds=scale_up["seconds"]-180 if scale_up else None,
                             ready_delay_seconds=ready_up["seconds"]-180 if ready_up else None,
                             scale_down_delay_seconds=scale_down["seconds"]-480 if scale_down else None))
