---
name: scaleproof-public-check
description: Verify a deployed Scaleproof workload-check API through a browser, ordinary client and independent database read.
---

Read AGENTS.md and docs/runbooks/PUBLIC_API.md. Resolve pending credential authorization before deployment. Send only a handful of bounded policy checks, never load. Create fresh accepted and rejected receipts, read them, verify identical replay and changed-payload conflict. Match IDs, mode, digest and deployed revision with a separate database connection. Preserve missing access as not done. Never copy secrets into artifacts or disable deployment protection.
