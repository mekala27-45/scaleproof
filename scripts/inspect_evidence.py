"""Inspect retained experiment evidence using an explicit non-secret summary."""
import hashlib
import json
from pathlib import Path
import urllib.request
import os

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
         "cleanup":{key:value for key,value in cleanup.items() if key in ("verified_absent","container_absent","cluster_absent","removed","status","mode")},
         "inventory_count":len(inventory)}
print("EVIDENCE_SUMMARY_START")
print(json.dumps(summary,sort_keys=True))
print("EVIDENCE_SUMMARY_END")
# Read only workflow metadata; never print token or environment.
request=urllib.request.Request("https://api.github.com/repos/mekala27-45/scaleproof/actions/runs?per_page=10",
    headers={"Authorization":"Bearer "+os.environ["GH_TOKEN"],"Accept":"application/vnd.github+json"})
with urllib.request.urlopen(request,timeout=20) as response: workflows=json.load(response)
print("WORKFLOW_SUMMARY "+json.dumps([{"id":run["id"],"name":run["name"],"status":run["status"],"conclusion":run["conclusion"],"head_sha":run["head_sha"]} for run in workflows["workflow_runs"]]))
