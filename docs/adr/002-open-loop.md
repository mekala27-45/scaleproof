# ADR 002: freeze arrivals before observing responses

Status: accepted.

Use exponential inter-arrival times from deterministic seeds 3101, 3102 and 3103. Register every scheduled ID before either lane runs. Bound concurrent clients to 64, total arrivals to 50,000 per run, and all requests to localhost derived from verified ownership.

A closed-loop client waits for responses and lowers offered demand when the server slows. That can hide overload. A single-pod port-forward also bypasses Service balancing. Use a localhost NodePort with fresh connections and verify successful pod UIDs.

Report client saturation as an invalid paired comparison. Preserve its denominator and failure record. Do not quietly lower the reserved rate and overwrite the run.

Consequence: this stricter design can fail because of client delivery rather than service capacity. Development calibration and the rejected-approach investigation explain that limit.
