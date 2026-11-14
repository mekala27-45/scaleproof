"""Acquire immutable public ONNX files and freeze their exact identities."""
import argparse
from pathlib import Path
import urllib.request
from .common import ROOT, file_digest, read_json, write_json, digest

MODEL_REPO = "Qdrant/bge-small-en-v1.5-onnx-Q"
REVISION = "c32e6154d1bb7a0e47c5e745fd895e7700f44385"
FILES = ("model_optimized.onnx", "tokenizer.json", "config.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.txt")


def acquire(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    entries = []
    for name in FILES:
        url = f"https://huggingface.co/{MODEL_REPO}/resolve/{REVISION}/{name}"
        path = destination / name
        if not path.exists():
            temporary = path.with_suffix(path.suffix + ".part")
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
                count = 0
                while block := response.read(1048576):
                    count += len(block)
                    if count > 100_000_000:
                        raise ValueError("Model file exceeds acquisition budget")
                    output.write(block)
            temporary.replace(path)
        entries.append(dict(name=name, sha256=file_digest(path), size_bytes=path.stat().st_size, source=url))
    manifest = dict(schema_version=1, model="BAAI/bge-small-en-v1.5", artifact_repo=MODEL_REPO,
                    upstream_revision=REVISION, files=entries, pooling="CLS", normalize="L2", dimensions=384,
                    sequence_limit=512, execution_provider="CPUExecutionProvider", intra_threads=1, inter_threads=1,
                    query_prefix="Represent this sentence for searching relevant passages: ", license="MIT")
    manifest["bundle_digest"] = digest(manifest)
    write_json(destination / "bundle.json", manifest)
    return manifest


def verify(directory):
    directory = Path(directory)
    manifest = read_json(directory / "bundle.json")
    identity = dict(manifest)
    claimed = identity.pop("bundle_digest")
    if digest(identity) != claimed or manifest["upstream_revision"] != REVISION:
        raise ValueError("Model manifest identity mismatch")
    if {row["name"] for row in manifest["files"]} != set(FILES):
        raise ValueError("Incomplete model file inventory")
    for row in manifest["files"]:
        if row["name"] not in FILES or file_digest(directory / row["name"]) != row["sha256"]:
            raise ValueError("Model file hash mismatch")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", default=str(ROOT / "models/bge"))
    args = parser.parse_args()
    print(acquire(args.destination)["bundle_digest"])
