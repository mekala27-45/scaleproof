# Scaleproof handoff: not complete

The first six-run study is invalid for a paired benefit claim because independent server events are incomplete. The corrected study is running separately: [workflow 43553134850](https://github.com/mekala27-45/scaleproof/actions/runs/43553134850), source 9f08f2f619fff3c0af61ebaa599fbd40d3dcb408, experiment core-v2-spooled-events. Do not infer its result from its workflow definition or progress.

The first archive is [artifact 14097065478](https://github.com/mekala27-45/scaleproof/actions/runs/43545207072/artifacts/14097065478), ZIP SHA-256 68e9d3241c8ba932007f31692702f1731055714119ea3411c10e523e120941d6. Its manifest digest is 794c4a12cade2e149e2789c28019b649ec8cc1b7cb8ace06c387f8c34856e562. The offline review found zero raw hash mismatches and retained every rejected run.

| Gate | Status | Source/run evidence | Observation |
| --- | --- | --- | --- |
| 01 Scope, source audit, calibration boundary and complete inventory | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43545207072) | The first study registered three schedules and six run slots before comparison. |
| 02 Pinned real CPU model, original corpus and output parity | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43545207072) | The actual ONNX parity gates passed before and after all six executed runs. |
| 03 Image, resource bounds, threads and readiness | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43545207072) | The built image served actual inference with the bounded worker and readiness gates. |
| 04 Owned cluster, local routing and fresh metrics | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43545207072) | Ownership, localhost routing and fresh observed metrics passed the run checks. |
| 05 Actual HPA specification and controller conditions | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43552784713) | Controller-condition and fresh-metric gates passed in the HPA lanes. |
| 06 Open-loop schedule and accounting fixtures | done | [9f08f2f](https://github.com/mekala27-45/scaleproof/actions/runs/43553139541) | Complete inventory, late completion and dispatch-failure fixtures passed. |
| 07 Three matched pairs under frozen rates, seeds and phases | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43545207072) | All six first-study runs executed; comparison acceptance still failed. |
| 08 Actual scale-up and scale-down with ready capacity | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43552784713) | Each HPA lane reached three serving pods and returned toward one ready replica. |
| 09 Functional public API and fresh persisted receipts | not done | [9f08f2f](docs/runbooks/PUBLIC_API.md) | Hosted credential transfer is awaiting specific authorization. |
| 10 Every scheduled arrival accounted for in the client ledger | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43552784713) | The grader found no missing or duplicate client arrival IDs; server reconciliation remains incomplete. |
| 11 Owned pod-loss recovery with replacement inference | done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43552784713) | Fresh replacement inference was observed after 5.520 seconds. |
| 12 Independent grader rejects missing, stale and contradictory evidence | done | [9f08f2f](https://github.com/mekala27-45/scaleproof/actions/runs/43553139541) | Six adversarial fixtures passed; the real incomplete study was rejected. |
| 13 Paired metrics and replica-seconds independently rederive | not done | [9f08f2f](docs/method/REDERIVATION.md) | Accepted raw rederivation is blocked by incomplete server accounting in the first study. |
| 14 Security, ownership refusal, sessions and restart persistence | not done | [9f08f2f](https://github.com/mekala27-45/scaleproof/actions/runs/43553139541) | Source-boundary and PostgreSQL tests passed; final image/public artifact checks remain open. |
| 15 UI, keyboard, viewport, palette and mode-label checks | not done | [2c51d2e](https://github.com/mekala27-45/scaleproof/actions/runs/43546063227) | Nine automated browser checks passed; actual browser zoom and public-host verification remain open. |
| 16 Final findings, uncertainty and local limits | not done | [9f2f7c7](docs/method/FIRST_STUDY.md) | The failed first attempt is documented; final corrected-study findings are pending. |
| 17 Clean rederivation, fresh smoke, cleanup and handoff | not done | [9f2f7c7](https://github.com/mekala27-45/scaleproof/actions/runs/43545207072) | First-study cleanup passed; clean reproduction and corrected-study completion remain open. |
| 18 Forty meaningful commits and authorized release/tag | not done | [9f08f2f](https://github.com/mekala27-45/scaleproof/pull/1) | The commit floor is met; the PR remains draft and no release or tag is claimed. |

## Main result and limit

No accepted HPA benefit claim exists. The first attempt demonstrates actual model execution and controller behavior but fails complete independent server accounting. One shared CPU host and three pairs cannot establish cloud cost savings, general model quality or production reliability.

## Remaining approvals

Automatic review rejected storing the restricted Scaleproof Neon connection credential as encrypted DATABASE_URL in Vercel project scaleproof-api preview and production. This remains blocked.

Automatic review rejected exporting compressed raw experiment logs to a public evidence branch. No raw branch was published. Approval would cover reviewed, secret-scanned synthetic experiment evidence from workflows 43545207072 and 43553134850 to mekala27-45/scaleproof. Only aggregate findings are currently committed.

A proposed PR-based evidence review was also rejected. It was replaced with an accepted pinned, offline, read-only review which does not execute PR code or expose a token to the review script.

## Tool and publication state

The Windows execution and browser tools stopped starting after the session permission configuration introduced invalid non-Windows paths. Remote GitHub work continued. The local checkout is behind later remote commits and must be reconciled without discarding changes after access is repaired.

Pages source was configured for Actions. The first deployment failed before action steps, with no accessible job log. Publication is now limited to main. The build branch validates and packages the reader. No live reader or API URL is claimed.

## Commands and next task

After restoring owned artifacts to their source-matched checkout, run python -m scaleproof.grade and python scripts/rederive.py. Run python -m scaleproof.render only with consistent manifest provenance. Perform a fresh model/HPA smoke and owned cleanup before release.

After approved Vercel credential setup, run python -m scaleproof.verify_public against the verified owned Vercel origin, then verify the same receipt independently in the browser and PostgreSQL. Never send inference or load traffic to the public host.

Inspect corrected workflow 43553134850 before starting any new cluster. Retain its exact source and verdict. All stretch steps remain unstarted.
