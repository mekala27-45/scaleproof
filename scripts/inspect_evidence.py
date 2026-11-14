"""Inspect retained experiment evidence using an explicit non-secret summary."""
import hashlib
import json
from pathlib import Path

root=Path("retained")
manifest=json.loads((root/"artifacts/manifests/core-v1.json").read_text())
plan=json.loads((root/"evaluation/plan.json").read_text())
inventory=json.loads((root/"evaluation/inventory.json").read_text())
hash_failures=[]
runs=[]
for run in manifest["runs"]:
    folder=root/"artifacts/raw"/run["id"]
    for name,expected in run["raw_sha256"].items():
        path=folder/(name+".json")
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if actual!=expected: hash_failures.append(run["id"]+"/"+name)
    runs.append({"id":run["id"],"status":run["status"],"acceptance":run["acceptance"]})
recovery=json.loads((root/"artifacts/raw/recovery.json").read_text())
cleanup=json.loads((root/"artifacts/raw/cleanup.json").read_text())
summary={"source_revision":manifest["source_revision"],"mode":manifest["mode"],"status":manifest["status"],
         "main_result":manifest["main_result"],"evidence_digest":manifest["evidence_digest"],"hash_failures":hash_failures,
         "rates":{"low_rps":plan["low_rps"],"high_rps":plan["high_rps"]},"runs":runs,"pairs":manifest["pairs"],
         "recovery":{"recovered":recovery["recovered"],"recovery_seconds":recovery["recovery_seconds"]},
         "cleanup":{key:value for key,value in cleanup.items() if key in ("verified",)},
         "inventory_count":len(inventory)}
print("EVIDENCE_SUMMARY_START")
print(json.dumps(summary,sort_keys=True))
print("EVIDENCE_SUMMARY_END")
