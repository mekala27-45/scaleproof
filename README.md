# Scaleproof

A real CPU retrieval service, a bounded Kubernetes autoscaling study, and a separate workload-policy checker.

**Status: implemented, not yet accepted end to end.** The first six-run study executed but the independent grader rejected every comparison because polling lost some server events. The corrected study uses durable per-pod event files and is running under a new source identity. No performance benefit is currently eligible as a project claim.

[Build pull request](https://github.com/mekala27-45/scaleproof/pull/1) | [First-study findings](docs/method/FIRST_STUDY.md) | [Current state](PROJECT_STATE.md) | [Next session](NEXT_SESSION.md)

## What is implemented

The serving lane loads a pinned BGE small ONNX bundle, verifies all file hashes, and performs fresh CPU encoding for every query. All 24 notes are original synthetic fixtures. The fixed lane has one replica; the HPA has one to three. Six matched runs use three frozen schedules with alternating order, five-second deadlines and complete scheduled-arrival denominators.

The public FastAPI application validates bounded numeric plans. It cannot execute inference, send load or mutate Kubernetes. PostgreSQL stores session-scoped receipts, idempotent results and separate physical attempts. The React reader has Workload, Capacity, Requests and Method views, self-hosted fonts, light/dark palettes, and inspectable demand, CPU and stepwise replica traces.

## Observed verification

The first study workflow completed at source 9f2f7c73f6b48812880a6afe97293d515953e6ed. It observed actual model parity, scale-up, scale-down, multi-pod routing, 5.520-second replacement inference after pod loss, and verified cleanup. Incomplete independent server accounting prevents acceptance of its paired performance comparison.

The browser build at 2c51d2ea337eea738bd4b17e7c212f4a59eaf4c0 passed nine automated checks, covering 390, 768 and 1440 pixels in both themes, persistence, error state and policy arithmetic. Its CSS zoom check is not a substitute for the still-pending actual browser 200-percent zoom check. The Pages deployment job failed before its action steps; a live reader URL is not verified.

The PostgreSQL contract suite exercises concurrent replay and process-death recovery. The hosted Vercel receipt flow remains blocked pending specific database-credential authorization.

## Run

Install Python 3.12 dependencies with `python -m pip install -e '.[inference,test,postgres]'`. Run `python -m unittest discover -s tests -v`, `python -m scaleproof.audit_security`, and `python scripts/validators/palette_validator.py palette.json`.

Use [the operations runbook](docs/runbooks/OPERATIONS.md) for the disposable Linux Docker/kind study. Use [the public API runbook](docs/runbooks/PUBLIC_API.md) for a handful of functional checks after authorized deployment. The measured load target is always the verified owned localhost NodePort.

Run the reader with `cd web`, `npm install`, and `npm run dev`. Live persistence is disabled until a verified API URL is supplied. Local previews never create a server receipt.

## Evidence and limits

Read [the specification](docs/SPEC.md), [design decisions](DECISIONS.md), [reuse audit](REUSE.md), and [review limits](docs/method/REVIEW_LIMITS.md). The executable closed-loop investigation is deliberately labeled synthetic_fault. The raw rederivation script refuses missing or rejected evidence.

One shared CPU host and three paired repetitions support a narrow descriptive study. Replica-seconds are resource exposure, not money or energy. Synthetic notes do not establish production retrieval quality or customer impact. Public raw evidence export, final release and tag remain pending.
