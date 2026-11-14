"""Original CC0 synthetic operations notes, not a retrieval benchmark."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
"sensor_freshness": [
("Beacon freshness", "Beacon marks a sensor stale after 45 seconds without a sample. A stale sample cannot support a capacity decision.", "When does Beacon mark a sample stale?", "Can stale Beacon samples support capacity decisions?"),
("Lumen timestamps", "Lumen stores capture time and arrival time separately. Its freshness rule uses capture time.", "Which timestamp defines Lumen freshness?", "Does arrival time define freshness for Lumen?"),
("Reef clock check", "Reef rejects a sample captured more than five seconds in the future. It records the clock error without changing the sample.", "How does Reef handle future samples?", "Does Reef rewrite a sample with a clock error?"),
("Tide gaps", "Tide retains a missing interval as unknown. It does not interpolate a healthy reading across the gap.", "How does Tide represent missing intervals?", "Can Tide interpolate health over a missing interval?")],
"document_revision": [
("Harbor revision", "Harbor serves only the revision named in the signed manifest. A newer filename alone does not update the active revision.", "What selects the Harbor active revision?", "Does a newer Harbor filename activate a revision?"),
("Quay supersession", "Quay retains superseded notes for audit. Search results identify the selected revision and its effective date.", "Does Quay retain superseded notes?", "What revision details accompany Quay search results?"),
("Buoy conflicts", "Buoy flags contradictory revisions for review. It never merges conflicting instructions silently.", "What does Buoy do with conflicting revisions?", "Can Buoy merge contradictory instructions silently?"),
("Pier document hash", "Pier verifies each document hash before indexing. A mismatched document stops readiness.", "When does Pier verify document hashes?", "What happens when a Pier document hash mismatches?")],
"request_budgets": [
("Jetty queue", "Jetty admits at most eight waiting requests per worker. Further requests receive an explicit overload rejection.", "What is the Jetty waiting queue limit?", "How does Jetty report excess requests?"),
("Cove deadlines", "Cove measures deadlines from scheduled arrival. A delayed dispatch does not grant a later deadline.", "Where does a Cove deadline begin?", "Does late dispatch extend a Cove deadline?"),
("Dune retries", "Dune records every physical attempt. A logical retry does not remove the original timeout from the ledger.", "How does Dune account for retries?", "Can a retry erase a Dune timeout?"),
("Shoal drain", "Shoal stops new arrivals during its final drain. Work unfinished at the drain deadline remains unfinished in the report.", "What happens during the Shoal drain?", "How is unfinished Shoal drain work reported?")],
"model_identity": [
("Atlas bundle", "Atlas identifies a model by revision and hashes of all executed files. The package version alone is insufficient.", "What identifies an Atlas model bundle?", "Is the Atlas package version sufficient model identity?"),
("Kelp provider", "Kelp records the CPU execution provider and thread count. A provider change requires a new environment record.", "What runtime settings does Kelp record?", "What must happen after a Kelp provider change?"),
("Foam parity", "Foam compares direct and served embeddings with an absolute tolerance of one hundred-thousandth. Different ranked IDs fail parity.", "What tolerance does Foam use for parity?", "Can Foam parity pass when ranked IDs differ?"),
("Mast cache", "Mast keeps weights loaded but disables query-result caches during measurement. Each successful request invokes the encoder.", "Which cache does Mast disable during measurement?", "Must each successful Mast request invoke the encoder?")],
"worker_recovery": [
("Skiff readiness", "Skiff becomes ready only after loading its model, validating the corpus and completing an encoder probe. Liveness alone is insufficient.", "What makes a Skiff worker ready?", "Does Skiff liveness prove model readiness?"),
("Sail replacement", "Sail records the lost pod UID and its replacement UID. Recovery requires a fresh inference from the replacement.", "What proves Sail recovery?", "Which pod identities does Sail retain after loss?"),
("Dock shutdown", "Dock stops admission before draining in-flight work. Its termination budget is thirty seconds.", "What is the Dock shutdown order?", "How long is the Dock termination budget?"),
("Channel capacity", "Channel distinguishes desired replicas from ready replicas. A pending pod contributes no ready capacity.", "Does a pending Channel pod count as ready capacity?", "Which replica quantities does Channel distinguish?")],
"artifact_retention": [
("Anchor raw data", "Anchor retains failed runs alongside successful runs. Its inventory determines the denominator.", "What determines the Anchor denominator?", "Does Anchor retain failed runs?"),
("Lagoon expiry", "Lagoon expires public receipts after twenty-four hours. Expired sessions cannot read those receipts.", "When do Lagoon public receipts expire?", "Can an expired Lagoon session read a receipt?"),
("Breakwater secrets", "Breakwater excludes credentials and cluster configuration from public artifacts. It publishes sanitized identities only.", "What does Breakwater exclude from public artifacts?", "Which identities may Breakwater publish?"),
("Estuary rederive", "Estuary regenerates reports from raw evidence in a clean checkout. Changed input hashes invalidate the accepted summary.", "How does Estuary regenerate reports?", "What invalidates an Estuary summary?")]
}

corpus, development, reserved = [], [], []
for group, notes in GROUPS.items():
    for j, (title, text, q1, q2) in enumerate(notes):
        ident = f"note-{len(corpus)+1:03}"
        corpus.append(dict(id=ident, version=1, group=group, title=title, text=text, synthetic=True, license="CC0-1.0"))
        # All variants of each note stay together; 2 notes per group per split.
        split = development if j < 2 else reserved
        split.append(dict(id=f"query-{ident}", query=q1, alternate=q2, expected_id=ident, group=group, synthetic=True))
for path, value in [("corpus/notes.json", corpus), ("development/queries.json", development), ("reserved/queries.json", reserved)]:
    output = ROOT / "fixtures" / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
