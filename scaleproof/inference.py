"""No hashing or lexical fallback: every request runs pinned CPU ONNX."""
from pathlib import Path
import time
import numpy as np
from .common import ROOT, digest, read_json
from .model_bundle import verify
from .ranking import BM25, fuse


class Encoder:
    dim = 384

    def __init__(self, directory):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        self.directory = Path(directory)
        self.manifest = verify(directory)
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(str(self.directory / "model_optimized.onnx"), sess_options=options,
                                            providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_file(str(self.directory / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=512)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        self.invocations = 0

    def embed(self, texts, query=False):
        if query:
            texts = [self.manifest["query_prefix"] + text for text in texts]
        encoded = self.tokenizer.encode_batch(texts)
        arrays = {"input_ids": np.asarray([e.ids for e in encoded], dtype=np.int64),
                  "attention_mask": np.asarray([e.attention_mask for e in encoded], dtype=np.int64),
                  "token_type_ids": np.asarray([e.type_ids for e in encoded], dtype=np.int64)}
        inputs = {i.name: arrays[i.name] for i in self.session.get_inputs()}
        raw = self.session.run(None, inputs)[0]
        self.invocations += 1
        vectors = raw[:, 0, :] if raw.ndim == 3 else raw
        if vectors.shape != (len(texts), self.dim) or not np.isfinite(vectors).all():
            raise ValueError("Encoder output shape or finite-value check failed")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if (norms <= 0).any():
            raise ValueError("Zero encoder norm")
        return (vectors / norms).astype(np.float32)


class Kernel:
    def __init__(self, directory, corpus=ROOT / "fixtures/corpus/notes.json"):
        self.documents = sorted(read_json(corpus), key=lambda d: d["id"])
        if len(self.documents) != 24 or len({d["id"] for d in self.documents}) != 24:
            raise ValueError("Expected all 24 unique synthetic notes")
        self.corpus_digest = digest(self.documents)
        self.encoder = Encoder(directory)
        self.vectors = self.encoder.embed([d["title"] + " " + d["text"] for d in self.documents])
        self.bm25 = BM25(self.documents)
        self.retrieve("Which worker is ready after its model loads?")

    def retrieve(self, query):
        before = self.encoder.invocations
        start = time.perf_counter()
        vector = self.encoder.embed([query], query=True)[0]
        encoder_ms = (time.perf_counter() - start) * 1000
        dense = sorted(zip([d["id"] for d in self.documents], map(float, self.vectors @ vector)), key=lambda r: (-r[1], r[0]))
        lexical = self.bm25.search(query)
        results = [{"document_id": ident, "fused_score": score, "cosine": dict(dense)[ident]} for ident, score in fuse([[r[0] for r in dense], [r[0] for r in lexical]])[:5]]
        return {"results": results, "model_digest": self.encoder.manifest["bundle_digest"], "corpus_digest": self.corpus_digest,
                "input_digest": digest(query), "output_digest": digest(results), "encoder_invocations": self.encoder.invocations - before,
                "encoder_ms": encoder_ms, "embedding": vector.tolist(), "execution_mode": "actual_cpu_inference"}
