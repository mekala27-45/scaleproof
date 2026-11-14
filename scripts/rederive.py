"""Independent descriptive rederivation from scheduled IDs and observed steps."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    manifest=read(root/"artifacts/manifests/core-v1.json")
    if manifest.get("mode")!="recorded_experiment":
        raise ValueError("Recorded raw evidence is absent; rederivation is not done")
    reports=[]
    for run in manifest["runs"]:
        folder=root/"artifacts/raw"/run["id"]
        for name,expected in run["raw_sha256"].items():
            if sha(folder/(name+".json"))!=expected: raise ValueError("Raw digest changed: "+run["id"]+"/"+name)
        if run["acceptance"]["status"]!="done": raise ValueError("Incomplete run cannot support accepted comparison: "+run["id"])
        scheduled=read(root/run["schedule"])["rows"]
        ledger=read(folder/"ledger.json")
        counts=Counter(row["id"] for row in ledger)
        if counts!=Counter(row["id"] for row in scheduled): raise ValueError("Request inventory mismatch")
        denominator=sum(row["phase"]=="high" for row in scheduled)
        completed=sum(row["phase"]=="high" and row["status"]=="completed" for row in ledger)
        rows=read(folder/"observations.json")
        exposure=sum(max(0.,min(660.,b["seconds"])-max(60.,a["seconds"]))*a["ready"] for a,b in zip(rows,rows[1:]))
        expected=run["acceptance"]["metrics"]
        if abs(exposure-expected["ready_replica_seconds"])>1e-6: raise ValueError("Replica integral mismatch")
        fraction=completed/denominator
        if abs(fraction-expected["phases"]["high"]["deadline_success_fraction"])>1e-12: raise ValueError("Deadline fraction mismatch")
        reports.append({"id":run["id"],"scheduled_high":denominator,"completed_high":completed,"deadline_success_fraction":fraction,"ready_replica_seconds":exposure})
    output={"mode":"recorded_experiment","source_revision":manifest["source_revision"],"evidence_digest":manifest["evidence_digest"],"runs":reports,"rederived":True}
    destination=root/"artifacts/investigations/rederivation.json"
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
    print(json.dumps(output))
if __name__=="__main__":
    try: main()
    except (ValueError,FileNotFoundError) as error:
        print(json.dumps({"status":"not_done","reason":str(error)}))
        sys.exit(1)
