from .common import ROOT,write_json,now
from .operations import verify_owner,run,CLUSTER


def main():
    ownership=verify_owner()
    run(["kind","delete","cluster","--name",CLUSTER],timeout=120)
    gone=CLUSTER not in run(["kind","get","clusters"]).stdout.splitlines()
    container=run(["docker","inspect",ownership["container_id"]],check=False)
    verified=gone and container.returncode!=0
    write_json(ROOT/"artifacts/raw/cleanup.json",dict(observed_at=now(),cluster=CLUSTER,deleted_container_id=ownership["container_id"],verified=verified))
    if not verified: raise RuntimeError("Owned cluster cleanup could not be verified")


if __name__=="__main__": main()
