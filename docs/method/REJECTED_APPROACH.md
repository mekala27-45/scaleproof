# Rejected approach: a closed-loop denominator

Run python scripts/investigate_closed_loop.py from the repository root.

This executable report uses an idealized deterministic queue, labeled synthetic_fault. It is a development reasoning fixture, not an actual model benchmark. At an intended 10 requests per second over 20 seconds, the open-loop inventory contains 200 arrivals. A single server taking 250 ms per request completes only six within a one-second arrival deadline as backlog grows. A closed-loop caller submits only 80 requests and reports all 80 timely.

Both calculations are correct for their own workloads. Treating them as the same offered workload would hide overload. The report therefore rejects closed-loop pacing for the registered comparison. It also rejects a single-pod port-forward because that path cannot test Service distribution to new pods.

The actual main comparison uses a seeded response-independent schedule, preserves scheduled IDs, and treats dispatch failures as failed evidence rather than silently slowing arrivals.
