---
name: scaleproof-operate
description: Run or diagnose the owned Scaleproof CPU and HPA study while preserving frozen plans and failed attempts.
---

Read AGENTS.md, PROJECT_STATE.md and docs/runbooks/OPERATIONS.md. Verify source, container, namespace UID and localhost binding before mutations. Run the documented modules in order. Stop on ownership mismatch. Do not overwrite evaluation/plan.json or any run directory. Grade every planned row, including failed and absent evidence. Preserve diagnostics before owned cleanup. Do not publish raw evidence while its approval is pending.
