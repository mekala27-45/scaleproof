import asyncio
import time
import uuid
import httpx
from .common import ROOT,write_json,read_json,now
from .operations import baseline,observe,TARGET,capture_logs
from .parity import check_parity


async def main():
    baseline("hpa")
    parity=check_parity(ROOT/"artifacts/raw/smoke-parity.json")
    query=read_json(ROOT/"fixtures/development/queries.json")[0]["query"]
    rows=[]; start=time.monotonic(); seen=set();events=[]
    # Development mechanism probe only. Never contributes performance claims.
    async with httpx.AsyncClient(trust_env=False,timeout=5,limits=httpx.Limits(max_connections=32,max_keepalive_connections=0)) as client:
        async def hit():
            try:
                return await client.post(TARGET+"/infer",json=dict(query=query,request_id="smoke-"+uuid.uuid4().hex,timeout_seconds=5),headers={"Connection":"close"})
            except httpx.HTTPError: return None
        active=set()
        next_observe=0
        while time.monotonic()-start<210:
            t=time.monotonic()-start
            if t<100 and len(active)<32:
                task=asyncio.create_task(hit());active.add(task);task.add_done_callback(active.discard)
            if t>=next_observe:
                rows.append(await asyncio.to_thread(observe,t));events.extend(await asyncio.to_thread(capture_logs,seen));next_observe=t+5
            await asyncio.sleep(.02 if t<100 else 1)
        await asyncio.gather(*active)
    up=any(r["ready"]>1 for r in rows)
    down=up and any(r["seconds"]>120 and r["ready"]==1 for r in rows)
    result=dict(mode="development_smoke",observed_at=now(),parity=parity["passed"],observed_scale_up=up,observed_scale_down=down,observations=rows,server_events=events)
    write_json(ROOT/"artifacts/raw/smoke.json",result)
    if not up or not down: raise RuntimeError("Development smoke did not observe both real ready-capacity transitions")


if __name__=="__main__": asyncio.run(main())
