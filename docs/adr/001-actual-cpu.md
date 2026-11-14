# ADR 001: actual CPU retrieval with explicit identity

Status: accepted implementation decision, operational verification remains a separate gate.

Use the BAAI/bge-small-en-v1.5 model exported in Qdrant/bge-small-en-v1.5-onnx-Q at c32e6154d1bb7a0e47c5e745fd895e7700f44385. Download only six named files, verify their SHA-256 manifest, disable remote code, and use CPUExecutionProvider with one intra-op and inter-op thread.

A lexical-only substitute or hashing embedder would remove the intended CPU mechanism. A separate executor keeps readiness responsive while actual encoding runs. A bounded queue provides explicit overload.

Full embeddings are returned only for direct-versus-served parity probes. Ordinary requests still compute the same vector but return ranked outputs and their digest. This reduces telemetry overhead without caching results.

Consequence: model startup, host contention and ONNX numerical tolerance must be measured. A successful readiness endpoint alone is not inference evidence.
