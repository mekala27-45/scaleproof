# Reuse and licenses

GroundedRAG was inspected at b3273286b3a8f3f48cdb4f540d65c297ad096ccc: https://github.com/mekala27-45/grounded-rag/tree/b3273286b3a8f3f48cdb4f540d65c297ad096ccc . Its MIT retrieval design informed BM25, normalized embeddings and reciprocal-rank fusion. Scaleproof reimplements the small ranking contract and adds stable ID tie breaks, negative cosine preservation, direct ONNX execution, bounded serving and runtime identity. Its measurements do not transfer.

The model is BAAI/bge-small-en-v1.5, using Qdrant/bge-small-en-v1.5-onnx-Q at c32e6154d1bb7a0e47c5e745fd895e7700f44385. The bundle records every downloaded file hash. Model files are not committed. Model license metadata is MIT; inspect the upstream model card and retain the actual downloaded model metadata.

The original 24-note synthetic corpus and 24 split queries are dedicated to CC0-1.0 by Ajay Mekala. They do not contain employer or customer documents.

Palette validator source: https://github.com/mekala27-45/handoff/blob/main/scripts/validators/palette_validator.py . Checked Git blob: 12b1afd64f1cad5ac19f3b83e22fe243ba8f96e0. Checked LF bytes SHA-256: 353610c704916d5a764728e77a15f7528d501d953b73ec301f788c01b40da266. It retains the existing numerical floors.

Fenix, Lunasima and Rubik Mono One are self-hosted through pinned Fontsource packages under OFL-1.1. Build output must retain the installed package LICENSE files. The primary fonts are reserved for this day; Antic Slab, Arimo, Bitcount Grid Single Ink, Andada Pro, Padauk and Bitcount Grid Double Ink remain alternate reservations.

No Tracepath or Foundry runtime was copied. Those optional integrations remain stretch work.
