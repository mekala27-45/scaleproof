import asyncio
import time
from .common import ROOT,read_json,write_json,digest,file_digest,now
from .load import execute
from .operations import baseline,observe,capture_logs,verify_owner,kubectl
from .parity import check_parity


async def run_one(item,plan):
    folder=ROOT/"artifacts/raw"/item["id"]
    if folder.exists(): raise RuntimeError("Run folder exists. Refusing to overwrite a prior attempt")
    folder.mkdir(parents=True)
    item["status"]="running"; item["started_at"]=now()
    write_json(ROOT/"evaluation/inventory.json",plan["inventory"])
    observations,events,seen=[],[],set()
    try:
        baseline(item["lane"])
        check_parity(folder/"parity-before.json")
        schedule=read_json(ROOT/item["schedule"])
        if schedule["schedule_digest"]!=item["schedule_digest"]: raise ValueError("Schedule changed after registration")
        initial=observe(0)
        observations.append(initial)
        # Ignore development events while retaining independent run IDs below.
        capture_logs(seen)
        start=time.monotonic()
        loading=asyncio.create_task(execute(schedule,item["id"],timeout_seconds=plan["request_timeout_seconds"]))
        while not loading.done():
            cycle=time.monotonic()
            try:
                row=await asyncio.to_thread(observe,time.monotonic()-start)
                observations.append(row)
                events.extend(await asyncio.to_thread(capture_logs,seen))
            except Exception as exc:
                events.append(dict(event="observer_error",error=str(exc),observed_at=now()))
            write_json(folder/"observations.json",observations)
            write_json(folder/"server-events.json",events)
            await asyncio.sleep(max(0,5-(time.monotonic()-cycle)))
        ledger=await loading
        observations.append(observe(time.monotonic()-start))
        events.extend(capture_logs(seen))
        events=[e for e in events if e.get("request_id","").startswith(item["id"]+":") or e.get("event") in ("model_ready","observer_error")]
        write_json(folder/"ledger.json",ledger)
        write_json(folder/"observations.json",observations)
        write_json(folder/"server-events.json",events)
        (folder/"kubernetes-events.json").write_text(kubectl("get","events","-o","json").stdout,encoding="utf-8")
        check_parity(folder/"parity-after.json")
        item["status"]="executed"
    except Exception as exc:
        item["status"]="failed"; item["error"]=str(exc)
        write_json(folder/"failure.json",dict(error=str(exc),observed_at=now()))
    finally:
        item["finished_at"]=now()
        write_json(ROOT/"evaluation/inventory.json",plan["inventory"])


async def main():
    verify_owner()
    plan=read_json(ROOT/"evaluation/plan.json")
    original=dict(plan); claimed=original.pop("plan_digest")
    if digest(original)!=claimed: raise ValueError("Frozen plan hash mismatch")
    for path,expected in plan["invariants"].items():
        if file_digest(ROOT/path)!=expected: raise ValueError("Frozen source input changed")
    for item in plan["inventory"]:
        await run_one(item,plan)


if __name__=="__main__": asyncio.run(main())
