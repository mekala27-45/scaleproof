# Owned execution runbook

Start from a clean checkout of the intended source commit on Linux with Docker, kubectl, kind 0.33.0, Python 3.12 and at least two CPUs and 5 GiB free RAM. A standard public GitHub Actions runner is the verified fallback for the Windows host where the Linux Docker engine was unavailable.

Install with python -m pip install -e '.[inference,test,postgres]'. Run python -m unittest discover -s tests -v.

Run the modules in order: scaleproof.probe, scaleproof.build_image, scaleproof.bootstrap, scaleproof.smoke, scaleproof.calibrate, scaleproof.freeze_plan, scaleproof.run_pairs, scaleproof.recover_pod, scaleproof.grade, scaleproof.render and scaleproof.cleanup.

Before freeze_plan, inspect the development calibration. Never overwrite an existing plan or run directory. The main comparison takes 72 minutes excluding startup and calibration. The workflow has a 115-minute ceiling and no paid runner.

Only the owned kind-scaleproof context, scaleproof namespace UID, container identity and 127.0.0.1:18080 mapping qualify. Cleanup checks the same ownership before removing the disposable cluster. If ownership differs, stop and preserve evidence.

Readiness failures, stale metrics, model mismatch and missing server events invalidate the affected gate. Do not replace them with hand-authored traces.

Actions artifacts retain raw data for 14 days. Public raw evidence branch publication is disabled pending specific approval. Download and review before expiry; a missing archive cannot support a later claim.
