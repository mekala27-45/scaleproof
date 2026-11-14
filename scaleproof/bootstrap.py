import json
import urllib.request
from .common import ROOT, read_json, write_json, file_digest, now
from .operations import run,kubectl,CLUSTER,NODE_IMAGE,OWNERSHIP,TARGET


def main():
    if CLUSTER in run(["kind","get","clusters"]).stdout.splitlines():
        raise RuntimeError("A scaleproof cluster already exists. Refusing to adopt or overwrite it.")
    info=json.loads(run(["docker","info","--format","{{json .}}"]).stdout)
    if info["NCPU"]<2 or info["MemTotal"]<5*1024**3:
        raise RuntimeError("Host needs at least two CPU cores and five GiB for the registered candidate")
    run(["kind","create","cluster","--name",CLUSTER,"--image",NODE_IMAGE,"--config","infra/local/kind.json","--wait","180s"],timeout=300)
    run(["kind","load","docker-image","scaleproof:local","--name",CLUSTER],timeout=180)
    # The node was created by this invocation, before any workload is admitted.
    run(["docker","exec","scaleproof-control-plane","mkdir","-p","/var/local/scaleproof-evidence"])
    run(["docker","exec","scaleproof-control-plane","chown","10001:10001","/var/local/scaleproof-evidence"])
    run(["docker","exec","scaleproof-control-plane","chmod","0700","/var/local/scaleproof-evidence"])
    image=read_json(ROOT/"artifacts/raw/image.json")
    workload=read_json(ROOT/"infra/local/workload.json")
    for item in workload["items"]:
        if item["kind"]=="Deployment":
            item["spec"]["template"]["spec"]["containers"][0]["env"].append(dict(name="IMAGE_IDENTITY",value=image["image_identity"]))
    path=ROOT/"artifacts/private/workload.json"; write_json(path,workload)
    kubectl("apply","-f",str(path),namespace=False)
    node=json.loads(run(["docker","inspect","scaleproof-control-plane"]).stdout)[0]
    ns=json.loads(kubectl("get","namespace","scaleproof","-o","json",namespace=False).stdout)
    write_json(OWNERSHIP,dict(cluster=CLUSTER,container_id=node["Id"],namespace_uid=ns["metadata"]["uid"],target=TARGET,created_at=now()))
    url="https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.8.1/components.yaml"
    path=ROOT/"artifacts/private/metrics-server.yaml"
    with urllib.request.urlopen(url,timeout=30) as response: path.write_bytes(response.read())
    kubectl("apply","-f",str(path),namespace=False)
    # Explicit kind-only TLS workaround; never applied to another context.
    kubectl("-n","kube-system","patch","deployment","metrics-server","--type=json","-p",json.dumps([{ "op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]),namespace=False)
    kubectl("-n","kube-system","rollout","status","deployment/metrics-server","--timeout=180s",namespace=False)
    kubectl("rollout","status","deployment/retrieval","--timeout=300s")
    write_json(ROOT/"artifacts/raw/cluster.json",dict(node_image=NODE_IMAGE,metrics_server_version="v0.8.1",metrics_manifest_sha256=file_digest(path),
               metrics_source=url,kubelet_tls="insecure: disposable kind only",docker_cores=info["NCPU"],docker_memory_bytes=info["MemTotal"],context="kind-scaleproof"))


if __name__ == "__main__": main()
