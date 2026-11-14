import uuid
import httpx
import numpy as np
from .common import ROOT, read_json, write_json, now
from .inference import Kernel
from .operations import verify_owner,TARGET


def check_parity(output):
    verify_owner()
    kernel=Kernel(ROOT/"models/bge")
    queries=read_json(ROOT/"fixtures/development/queries.json")[:2]
    rows=[]
    with httpx.Client(trust_env=False,timeout=10,headers={"Connection":"close"}) as client:
        for query in queries:
            direct=kernel.retrieve(query["query"])
            served=client.post(TARGET+"/infer",json=dict(query=query["query"],request_id="parity-"+uuid.uuid4().hex,timeout_seconds=10,include_embedding=True)).raise_for_status().json()
            passed=bool(np.allclose(direct["embedding"],served["embedding"],rtol=0,atol=1e-5)) and [r["document_id"] for r in direct["results"]]==[r["document_id"] for r in served["results"]] and direct["model_digest"]==served["model_digest"] and served["encoder_invocations"]==1
            rows.append(dict(query_id=query["id"],direct=direct,served=served,passed=passed))
    record=dict(observed_at=now(),mode="actual_cpu_inference",tolerance_absolute=1e-5,passed=all(r["passed"] for r in rows),rows=rows)
    write_json(output,record)
    if not record["passed"]: raise RuntimeError("Direct versus served model parity failed")
    return record
