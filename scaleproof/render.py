"""Mechanical report renderer. Numbers are derived by the independent grader."""
from .common import ROOT,read_json,digest

CHECKLIST=["Scope, source audit and complete run inventory registered","Pinned real CPU model and output parity checks pass","Image, resource bounds and readiness verified","Owned cluster, routing and fresh metrics observed","HPA spec and controller conditions recorded","Open-loop accounting passes independent fixtures","Three frozen matched pairs execute","Actual scale-up and scale-down with ready capacity observed","Public workload-check API live and fresh receipts persist","Every scheduled arrival accounted for","Pod-loss recovery includes replacement model output","Grader rejects missing, stale and contradictory evidence","Paired metrics and replica-seconds rederive","Security, sessions and restart persistence pass","UI, keyboard, viewport, palette and modes verified","Reports state findings and local limits","Clean rederivation, smoke and teardown verified","Forty meaningful commits and authorized release verified"]


def main():
    manifest=read_json(ROOT/"artifacts/manifests/core-v1.json")
    if "evidence_digest" in manifest:
        body=dict(manifest); claimed=body.pop("evidence_digest")
        if digest(body)!=claimed: raise ValueError("Changed evidence cannot render claims")
    state=read_json(ROOT/"artifacts/manifests/checklist.json") if (ROOT/"artifacts/manifests/checklist.json").exists() else {}
    lines=["# Scaleproof results","",manifest["main_result"],"","Mode: "+manifest["mode"],"","Source: "+str(manifest["source_revision"]),"","## Acceptance","","| Gate | Status | Evidence |","| --- | --- | --- |"]
    for i,label in enumerate(CHECKLIST,1):
        row=state.get(str(i),{})
        lines.append(f"| {i:02} {label} | {row.get('status','not done')} | {row.get('evidence','No qualifying evidence recorded')} |")
    lines += ["","## Matched comparisons","","| Pair | Evidence status | HPA minus fixed deadline success |","| --- | --- | --- |"]
    for pair in manifest.get("pairs",[]):
        difference=pair["deadline_success_difference"]
        lines.append(f"| {pair['pair']} | {pair['status']} | {difference if difference is not None else 'unavailable'} |")
    lines += ["","## Limits",""]+manifest.get("limits",[])+["","No cloud cost, production reliability or general model-quality claim is made.",""]
    (ROOT/"RESULTS.md").write_text("\n".join(lines),encoding="utf-8")


if __name__=="__main__": main()
