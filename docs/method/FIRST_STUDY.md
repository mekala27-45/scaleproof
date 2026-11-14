# First study: incomplete independent server accounting

Source: 9f2f7c73f6b48812880a6afe97293d515953e6ed. Workflow: https://github.com/mekala27-45/scaleproof/actions/runs/43545207072 .

All six planned runs executed, with real model parity and observed HPA transitions. The grader rejected every comparison because independent server events were missing for some successful responses. It did not waive this requirement when client results appeared favorable.

The retained archive is artifact 14097065478, SHA-256 68e9d3241c8ba932007f31692702f1731055714119ea3411c10e523e120941d6. Its manifest evidence digest is 794c4a12cade2e149e2789c28019b649ec8cc1b7cb8ace06c387f8c34856e562. Aggregate review rechecked all listed raw hashes with zero mismatches: https://github.com/mekala27-45/scaleproof/actions/runs/43552784713 .

Pod-loss recovery observed fresh replacement inference after 5.520 seconds. Owned cluster deletion was verified. These observations do not repair the missing server accounting.

The correction writes each server event to an append-only per-pod file on the owned node. Files survive pod deletion and container stdout rotation. A new source image and separately frozen study are required. No first-study result is overwritten or promoted.

The aggregate JSON in artifacts/rejected/core-v1-summary.json contains only counts, timing metrics, source identities and acceptance errors. Raw public export remains disabled pending specific approval.
