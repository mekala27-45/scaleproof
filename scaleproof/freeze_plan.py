from .common import ROOT,read_json,write_json,digest,now,revision,file_digest
from .schedule import generate


def main():
    target=ROOT/"evaluation/plan.json"
    if target.exists(): raise RuntimeError("A frozen plan exists. Use a new study checkout, never overwrite it.")
    calibration=read_json(ROOT/"artifacts/raw/calibration/result.json")
    identity=read_json(ROOT/"artifacts/raw/image.json")
    identity["corpus_digest"]=digest(sorted(read_json(ROOT/"fixtures/corpus/notes.json"),key=lambda d:d["id"]))
    queries=read_json(ROOT/"fixtures/reserved/queries.json")
    inventory=[]
    for pair,seed in enumerate((3101,3102,3103),1):
        schedule=generate(calibration["low_rps"],calibration["high_rps"],seed,queries)
        path=f"evaluation/schedules/pair-{pair}.json"
        write_json(ROOT/path,schedule)
        for lane in (("fixed","hpa") if pair%2 else ("hpa","fixed")):
            inventory.append(dict(id=f"pair-{pair}-{lane}",pair=pair,lane=lane,schedule=path,schedule_digest=schedule["schedule_digest"],status="not_started"))
    plan=dict(schema_version=1,registered_at=now(),source_revision=revision(),identity=identity,calibration_digest=digest(calibration),
              low_rps=calibration["low_rps"],high_rps=calibration["high_rps"],duration_seconds=720,warmup_seconds=60,high_start_seconds=180,high_end_seconds=480,drain_start_seconds=660,
              request_timeout_seconds=5,concurrent_client_cap=64,dispatch_lag_limit_seconds=.1,total_arrival_cap_per_run=50000,
              seeds=[3101,3102,3103],comparison="high-phase deadline success / all scheduled high-phase arrivals",
              statistical_scope="Three paired repetitions; descriptive only; no formal hypothesis family or cost claim.",
              invariants={p:file_digest(ROOT/p) for p in ["infra/local/hpa.json","infra/local/workload.json","fixtures/corpus/notes.json","fixtures/reserved/queries.json"]},
              hpa=dict(min=1,max=3,cpu_target_percent=70,cpu_request_millicores=250),inventory=inventory)
    plan["plan_digest"]=digest(plan)
    write_json(target,plan)
    write_json(ROOT/"evaluation/inventory.json",inventory)
    return plan


if __name__=="__main__": main()
