import json
import time
import uuid
import httpx
from .common import ROOT,write_json,read_json,now
from .operations import verify_owner,baseline,observe,kubectl,TARGET


def main():
    verify_owner(); baseline("hpa")
    initial=observe(0)
    pod=next(p for p in initial["pods"] if p["ready"])
    current=json.loads(kubectl("get","pod",pod["name"],"-o","json").stdout)
    if current["metadata"]["uid"]!=pod["uid"] or current["metadata"]["labels"].get("scaleproof-owned")!="true":
        raise ValueError("Pod ownership changed before recovery probe")
    start=time.monotonic(); deleted_at=now()
    kubectl("delete","pod",pod["name"],"--wait=false")
    rows=[]; recovered=None
    query=read_json(ROOT/"fixtures/development/queries.json")[1]["query"]
    with httpx.Client(timeout=5,trust_env=False,headers={"Connection":"close"}) as client:
        while time.monotonic()-start<300:
            row=dict(seconds=time.monotonic()-start,observed_at=now())
            try:
                response=client.post(TARGET+"/infer",json=dict(query=query,request_id="recovery-"+uuid.uuid4().hex,timeout_seconds=5))
                row["status"]=response.status_code
                if response.status_code==200:
                    row["receipt"]=response.json()
                    if row["receipt"]["pod_uid"]!=pod["uid"] and row["receipt"]["encoder_invocations"]==1:
                        observation=observe(time.monotonic()-start)
                        if any(p["uid"]==row["receipt"]["pod_uid"] and p["ready"] for p in observation["pods"]): recovered=row
            except httpx.HTTPError as exc: row["error"]=type(exc).__name__
            rows.append(row)
            if recovered: break
            time.sleep(1)
    result=dict(mode="actual_cpu_inference",lost_pod_uid=pod["uid"],deleted_at=deleted_at,attempts=rows,recovered=recovered is not None,
                replacement_pod_uid=recovered["receipt"]["pod_uid"] if recovered else None,recovery_seconds=recovered["seconds"] if recovered else None)
    write_json(ROOT/"artifacts/raw/recovery.json",result)
    if not recovered: raise RuntimeError("Replacement model inference not observed within five minutes")


if __name__=="__main__": main()
