"""Publish durable, bounded evidence without private ownership or model files."""
import gzip
import shutil
from .common import ROOT, file_digest, write_json, revision, now


def main():
    destination = ROOT / "evidence-bundle"
    destination.mkdir(exist_ok=False)
    entries = []
    for directory in ("artifacts/raw", "artifacts/manifests", "evaluation"):
        for source in sorted((ROOT / directory).rglob("*")):
            if not source.is_file() or source.suffix not in (".json", ".jsonl", ".txt", ".yaml"):
                continue
            relative = source.relative_to(ROOT).as_posix()
            output = destination / (relative + ".gz")
            output.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as incoming, output.open("wb") as target:
                with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as compressed:
                    shutil.copyfileobj(incoming, compressed)
            entries.append({"path": relative, "sha256": file_digest(source), "bytes": source.stat().st_size,
                            "compressed_sha256": file_digest(output), "compressed_bytes": output.stat().st_size})
    write_json(destination / "index.json", {"schema_version": 1, "source_revision": revision(),
               "created_at": now(), "files": entries, "purpose": "Raw evidence, including failed attempts. Presence does not imply acceptance."})


if __name__ == "__main__":
    main()
