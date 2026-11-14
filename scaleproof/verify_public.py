"""Low-volume hosted policy verification. Never sends inference or load traffic."""
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import urllib.error
import urllib.parse
import urllib.request
from .common import ROOT, write_json, now
from .policy import DEFAULT

def main():
    base=os.environ["SCALEPROOF_PUBLIC_URL"].rstrip("/")
    parsed=urllib.parse.urlparse(base)
    if parsed.scheme!="https" or not parsed.hostname or not parsed.hostname.endswith(".vercel.app") or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path:
        raise ValueError("Use the verified owned HTTPS Vercel origin without a path, query or credentials")
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(method,path,payload=None,key=None,client=opener):
        headers={"Origin":"https://mekala27-45.github.io"}
        if payload is not None: headers["Content-Type"]="application/json"
        if key: headers["Idempotency-Key"]=key
        request=urllib.request.Request(base+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers,method=method)
        try:
            with client.open(request,timeout=15) as response: return response.status,json.load(response)
        except urllib.error.HTTPError as error: return error.code,{}
    assert call("GET","/health")[0]==200
    assert call("GET","/ready")[0]==200
    assert call("POST","/v1/sessions",{})[0]==201
    receipts=[]
    for plan,decision in [(DEFAULT,"accepted"),({**DEFAULT,"high_rps":101},"rejected")]:
        key="functional-"+secrets.token_hex(12)
        status,row=call("POST","/v1/workload-checks",plan,key)
        assert status==200 and row["decision"]==decision and row["execution_mode"]=="deterministic_live"
        status,readback=call("GET","/v1/workload-checks/"+row["plan_check_id"])
        assert status==200 and readback==row
        status,replay=call("POST","/v1/workload-checks",plan,key)
        assert status==200 and replay["replay"] and replay["plan_check_id"]==row["plan_check_id"]
        status,_=call("POST","/v1/workload-checks",{**plan,"low_rps":1},key)
        assert status==409
        receipts.append({k:row[k] for k in ("plan_check_id","decision","execution_mode","input_digest","persisted_at","source_revision")})
    output={"schema_version":1,"mode":"deterministic_live","observed_at":now(),"origin":base,"receipts":receipts,
            "client_verified":True,"browser_verified":False,"independent_database_verified":False,
            "limit":"Separate browser and database checks remain mandatory. This is not an inference or load measurement."}
    write_json(ROOT/"artifacts/checks/public-client.json",output)
    print(json.dumps(output))
if __name__=="__main__": main()
