import asyncio
import random
import json
import time
import uuid
import httpx
from .common import ROOT,write_json,read_json,now
from .operations import verify_owner,baseline,observe,kubectl,TARGET


async def main():
    verify_owner(); baseline("hpa")
    initial=observe(0)
    pod=next(p for p in initial["pods"] if p["ready"])
    current=json.loads(kubectl("get","pod",pod["name"],"-o","json").stdout)
    if current["metadata"]["uid"]!=pod["uid"] or current["metadata"]["labels"].get("scaleproof-owned")!="true":
        raise ValueError("Pod ownership changed before recovery probe")
    start=time.monotonic(); deleted_at=now()
    kubectl("delete","pod",pod["name"],"--wait=false")
    rows=[]; observations=[]; recovered=None; active=set()
    rate=read_json(ROOT/"artifacts/raw/calibration/result.json")["low_rps"]
    rng=random.Random(3131)
    next_arrival=next_observation=0.
    query=read_json(ROOT/"fixtures/development/queries.json")[1]["query"]
    async with httpx.AsyncClient(timeout=5,trust_env=False,limits=httpx.Limits(max_connections=32,max_keepalive_connections=0),headers={"Connection":"close"}) as client:
        async def request(scheduled):
            row=dict(scheduled_seconds=scheduled,seconds=time.monotonic()-start,observed_at=now())
            try:
                response=await client.post(TARGET+"/infer",json=dict(query=query,request_id="recovery-"+uuid.uuid4().hex,timeout_seconds=5))
                row["status"]=response.status_code
                if response.status_code==200:
                    row["receipt"]=response.json()
            except httpx.HTTPError as exc: row["error"]=type(exc).__name__
            row["finished_seconds"]=time.monotonic()-start
            rows.append(row)
        while time.monotonic()-start<300 and recovered is None:
            elapsed=time.monotonic()-start
            if elapsed>=next_arrival:
                if len(active)<32:
                    task=asyncio.create_task(request(next_arrival));active.add(task);task.add_done_callback(active.discard)
                else: rows.append(dict(scheduled_seconds=next_arrival,status="dispatch_failure"))
                next_arrival+=rng.expovariate(rate)
            if elapsed>=next_observation:
                observation=await asyncio.to_thread(observe,elapsed);observations.append(observation)
                ready={p["uid"] for p in observation["pods"] if p["ready"] and p["uid"]!=pod["uid"]}
                recovered=next((r for r in rows if r.get("receipt",{}).get("pod_uid") in ready and r["receipt"].get("encoder_invocations")==1),None)
                next_observation=elapsed+2
            await asyncio.sleep(.005)
        await asyncio.gather(*active)
    result=dict(mode="actual_cpu_inference",low_rps=rate,seed=3131,lost_pod_uid=pod["uid"],deleted_at=deleted_at,attempts=rows,observations=observations,recovered=recovered is not None,
                replacement_pod_uid=recovered["receipt"]["pod_uid"] if recovered else None,recovery_seconds=recovered["finished_seconds"] if recovered else None)
    write_json(ROOT/"artifacts/raw/recovery.json",result)
    if not recovered: raise RuntimeError("Replacement model inference not observed within five minutes")


if __name__=="__main__": asyncio.run(main())
