# Rejected approaches and observed failures

The first owned smoke run reached model image construction and cluster readiness,
then failed because the metrics API returned ServiceUnavailable before collecting
its first sample. Deployment rollout success did not imply resource-metrics readiness.
Run: https://github.com/mekala27-45/scaleproof/actions/runs/43543192029
Source: 484416836bb671a69985526a7e3c59d3a97ac69a.

The baseline now polls for real fresh samples within a fixed deadline, preserving
startup failures. Measured run observations still mark missing metrics as missing.

The public database connection is blocked by automatic approval review. The
restricted application credential cannot be transferred to Vercel without
specific authorization. No alternate credential transport will be attempted.

Closed-loop arrival generation and single-pod port-forwarding were excluded by
design. The executable investigation in docs/method will show why these approaches
can conceal overload; it is a synthetic mechanism example, not experiment evidence.
