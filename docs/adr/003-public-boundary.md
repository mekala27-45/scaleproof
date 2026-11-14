# ADR 003: public policy and private execution are separate

Status: accepted.

Host only numeric workload validation and session receipts publicly. PostgreSQL enforces session/key uniqueness in the same transaction as the receipt and physical-attempt record. Session tokens are random and stored only as hashes. Sessions expire after 24 hours. Each session is limited to 50 distinct receipts and 200 physical write attempts; the active session cap is 1,000.

No visitor input contains a destination, command, model path or cluster identifier. Cluster work is an owned, reviewed source request. Exact origin and 4,096-byte input limits apply in local tests and production.

Automatic approval review blocked transferring the dedicated database credential into Vercel. The credential is not committed and the live flow remains not done. Automatic review also blocked public raw evidence branch export; the workflow retains read-only repository permission.

Consequence: local policy preview can work while the live persistence gate is unavailable. Neither a local receipt nor a health response qualifies as hosted verification.
