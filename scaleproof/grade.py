"""Join from the registered inventory and publish only sanitized evidence."""
from .common import ROOT,read_json,write_json,digest,file_digest,now
from .grading import grade_run


def main():
    plan=read_json(ROOT/"evaluation/plan.json")
    inventory=read_json(ROOT/"evaluation/inventory.json")
    runs=[]; public_observations=[]; public_requests=[]
    for item in inventory:
        folder=ROOT/"artifacts/raw"/item["id"]
        paths={name:folder/(name+".json") for name in ("ledger","observations","server-events","parity-before","parity-after")}
        missing=[name for name,path in paths.items() if not path.exists()]
        report=dict(status="not_done",errors=["Missing raw artifacts: "+", ".join(missing)],metrics=None)
        hashes={name:file_digest(path) for name,path in paths.items() if path.exists()}
        if not missing:
            ledger=read_json(paths["ledger"]); observations=read_json(paths["observations"])
            report=grade_run(read_json(ROOT/item["schedule"]),ledger,observations,plan["identity"],item["lane"],read_json(paths["server-events"]))
            if not all(read_json(paths[p])["passed"] for p in ("parity-before","parity-after")):
                report["status"]="not_done";report["errors"].append("Model parity failed")
            public_observations.extend({"run_id":item["id"],**{k:o[k] for k in ("seconds","observed_at","desired","current","ready","cpu_millicores","metrics_age_seconds")}} for o in observations)
            public_requests.extend(dict(run_id=item["id"],id=r["id"],phase=r["phase"],scheduled_seconds=r["scheduled_seconds"],status=r["status"],dispatched_seconds=r.get("dispatched_seconds"),finished_seconds=r.get("finished_seconds")) for r in ledger)
        runs.append({**item,"acceptance":report,"raw_sha256":hashes})
    pairs=[]
    for pair in range(1,4):
        lanes={r["lane"]:r for r in runs if r["pair"]==pair}
        accepted=all(r["acceptance"]["status"]=="done" for r in lanes.values()) and len(lanes)==2
        outcome={lane:r["acceptance"]["metrics"]["phases"]["high"] if r["acceptance"]["metrics"] else None for lane,r in lanes.items()}
        pairs.append(dict(pair=pair,status="done" if accepted else "not_done",lanes=outcome,
                          deadline_success_difference=(outcome["hpa"]["deadline_success_fraction"]-outcome["fixed"]["deadline_success_fraction"]) if accepted else None))
    recovery=read_json(ROOT/"artifacts/raw/recovery.json") if (ROOT/"artifacts/raw/recovery.json").exists() else None
    accepted=all(p["status"]=="done" for p in pairs) and bool(recovery and recovery["recovered"])
    manifest=dict(schema_version=1,experiment_id="core-v1",mode="recorded_experiment",status="done" if accepted else "not_done",source_revision=plan["source_revision"],observed_at=now(),
                  plan_digest=plan["plan_digest"],identity=plan["identity"],runs=runs,pairs=pairs,observations=public_observations,requests=public_requests,recovery=recovery,
                  limits=["One shared local CPU host and three paired repetitions.","Descriptive comparison only. Replica-seconds are not money or energy.","Synthetic operations requests do not measure general retrieval quality."],
                  main_result="All registered runs passed the evidence gates." if accepted else "The recorded study has incomplete evidence gates. No benefit claim is eligible.")
    manifest["evidence_digest"]=digest(manifest)
    write_json(ROOT/"artifacts/manifests/core-v1.json",manifest)
    return manifest


if __name__=="__main__": main()
