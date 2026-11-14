# Assumptions and limits

| Practitioner assumption | Evidence to inspect |
| --- | --- |
| CPU utilization is useful for this model workload | HPA conditions, per-pod metrics and desired/ready observations |
| New model workers become ready within the workload window | Startup receipts, direct parity and scale-up delay |
| The Service reaches additional workers | Distinct successful pod UIDs after scale-up |
| The client can deliver offered work | Scheduled versus dispatch timestamps and dispatch-failure count |
| The database serializes duplicate writes | Concurrent receipt tests and separate connection read-back |

| Reviewer limit | Consequence |
| --- | --- |
| One shared CPU host | Results do not predict a production cluster |
| Three matched pairs | Descriptive comparison, no broad statistical superiority claim |
| Synthetic operations queries | No general retrieval quality or customer impact claim |
| Successful-only latency | Must be read alongside deadline success and error counts |
| Ready replica-seconds | Resource exposure, never dollars or energy |
| Missing hosted verification | No live persistence claim |
