import concurrent.futures
import time
import uuid
import httpx
from .common import ROOT,read_json,write_json,now
from .operations import baseline,TARGET
from .parity import check_parity


def main():
    baseline("fixed")
    check_parity(ROOT/"artifacts/raw/calibration/parity.json")
    query=read_json(ROOT/"fixtures/development/queries.json")[0]["query"]
    start=time.monotonic()
    def worker(index):
        completed=failed=0
        with httpx.Client(trust_env=False,timeout=10,headers={"Connection":"close"}) as client:
            while time.monotonic()-start<45:
                response=client.post(TARGET+"/infer",json=dict(query=query,request_id="cal-"+uuid.uuid4().hex,timeout_seconds=10))
                if response.status_code==200: completed+=1
                else: failed+=1
        return completed,failed
    with concurrent.futures.ThreadPoolExecutor(4) as pool: counts=list(pool.map(worker,range(4)))
    elapsed=time.monotonic()-start
    rate=sum(c for c,_ in counts)/elapsed
    result=dict(observed_at=now(),mode="development_calibration",elapsed_seconds=elapsed,completed=sum(c for c,_ in counts),failed=sum(f for _,f in counts),
                sustainable_completion_rps=rate,low_rps=round(max(.1,rate*.15),3),high_rps=round(min(100,rate*1.6),3),
                rate_rule="Low is 15 percent and high is 160 percent of measured completion rate, clipped at 100 requests/s.",client_workers=4)
    if rate<=0: raise RuntimeError("Calibration produced no actual-model completions")
    write_json(ROOT/"artifacts/raw/calibration/result.json",result)
    return result


if __name__=="__main__": main()
