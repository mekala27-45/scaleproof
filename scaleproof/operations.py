"""Owned local cluster primitives. All mutation targets are fixed and checked."""
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone
from .common import ROOT, read_json, write_json, now, revision, digest, file_digest

CLUSTER = "scaleproof"
CONTEXT = "kind-scaleproof"
TARGET = "http://127.0.0.1:18080"
OWNERSHIP = ROOT / "artifacts/private/ownership.json"
NODE_IMAGE = "kindest/node:v1.35.0@sha256:452d707d4862f52530247495d180205e029056831160e22870e37e3f6c1ac31f"


def run(args, timeout=120, check=True):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode:
        # Do not include credentials or unrestricted environment in errors.
        raise RuntimeError(f"{args[0]} {args[1]} failed ({p.returncode}): {p.stderr[-1500:]}")
    return p


def kubectl(*args, namespace=True, check=True):
    return run(["kubectl", "--context", CONTEXT, *(["-n", "scaleproof"] if namespace else []), *args], check=check)


def verify_owner():
    owned = read_json(OWNERSHIP)
    if owned.get("cluster") != CLUSTER or owned.get("target") != TARGET:
        raise ValueError("Owned target record missing or invalid")
    node = json.loads(run(["docker", "inspect", "scaleproof-control-plane"]).stdout)[0]
    binding = node["NetworkSettings"]["Ports"].get("30080/tcp", [])
    if node["Id"] != owned["container_id"] or not any(p["HostIp"] == "127.0.0.1" and p["HostPort"] == "18080" for p in binding):
        raise ValueError("Cluster container or localhost binding identity changed")
    namespace = json.loads(kubectl("get", "namespace", "scaleproof", "-o", "json", namespace=False).stdout)
    if namespace["metadata"].get("labels", {}).get("scaleproof-owned") != "true" or namespace["metadata"]["uid"] != owned["namespace_uid"]:
        raise ValueError("Namespace ownership mismatch")
    return owned


def cpu_millicores(value):
    for suffix, scale in [("n",1e-6),("u",.001),("m",1.)]:
        if value.endswith(suffix): return float(value[:-1])*scale
    return float(value)*1000


def observe(seconds):
    deploy = json.loads(kubectl("get","deployment","retrieval","-o","json").stdout)
    pods = json.loads(kubectl("get","pods","-l","app=retrieval","-o","json").stdout)
    hpa = kubectl("get","hpa","retrieval","-o","json",check=False)
    hpa = json.loads(hpa.stdout) if hpa.returncode == 0 else {}
    metrics = json.loads(kubectl("get","--raw","/apis/metrics.k8s.io/v1beta1/namespaces/scaleproof/pods",namespace=False).stdout)
    stamps = [datetime.fromisoformat(row["timestamp"].replace("Z","+00:00")) for row in metrics.get("items",[])]
    age = max((datetime.now(timezone.utc)-stamp).total_seconds() for stamp in stamps) if stamps else None
    conditions = hpa.get("status",{}).get("conditions",[])
    active = all(any(c["type"] == kind and c["status"] == "True" for c in conditions) for kind in ("AbleToScale","ScalingActive"))
    pod_rows = [dict(uid=p["metadata"]["uid"], name=p["metadata"]["name"], created_at=p["metadata"]["creationTimestamp"],
                     ready=any(c["type"]=="Ready" and c["status"]=="True" for c in p["status"].get("conditions",[])),
                     containers=p["status"].get("containerStatuses",[])) for p in pods["items"]]
    return dict(seconds=seconds,observed_at=now(),desired=deploy["spec"]["replicas"],current=deploy["status"].get("replicas",0),ready=deploy["status"].get("readyReplicas",0),
                metrics_age_seconds=age if age is not None else 1e9,cpu_millicores=sum(cpu_millicores(c["usage"]["cpu"]) for row in metrics.get("items",[]) for c in row["containers"]),
                cpu_request_millicores_per_pod=250,hpa_active=active,hpa_conditions=conditions,pods=pod_rows,
                endpoints=json.loads(kubectl("get","endpoints","retrieval","-o","json").stdout))


def baseline(lane):
    verify_owner()
    kubectl("delete","hpa","retrieval","--ignore-not-found=true")
    kubectl("scale","deployment/retrieval","--replicas=1")
    kubectl("rollout","status","deployment/retrieval","--timeout=180s")
    # Wait for metrics and real return to a single ready baseline, not a sleep as proof.
    deadline = time.monotonic()+180
    while time.monotonic()<deadline:
        row=observe(0)
        if row["desired"]==row["ready"]==row["current"]==1 and len(row["pods"])==1 and row["metrics_age_seconds"]<45:
            break
        time.sleep(3)
    else: raise RuntimeError("Baseline readiness and metrics were not observed")
    if lane == "hpa":
        kubectl("apply","-f",str(ROOT/"infra/local/hpa.json"))
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            row=observe(0)
            if row["hpa_active"] and row["desired"]==row["ready"]==1: break
            time.sleep(3)
        else: raise RuntimeError("HPA baseline did not become active")
    return row


def capture_logs(seen):
    pods=json.loads(kubectl("get","pods","-l","app=retrieval","-o","json").stdout)
    fresh=[]
    for pod in pods["items"]:
        raw=kubectl("logs",pod["metadata"]["name"],"--since=30s",check=False).stdout
        for line in raw.splitlines():
            try: event=json.loads(line)
            except ValueError: continue
            key=digest(event)
            if key not in seen:
                seen.add(key); fresh.append(event)
    return fresh
