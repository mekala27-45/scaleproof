import json
from .common import ROOT, revision, write_json
from .model_bundle import acquire
from .operations import run


def main():
    bundle=acquire(ROOT/"models/bge")
    run(["docker","build","--build-arg","SOURCE_REVISION="+revision(),"-f","infra/local/Dockerfile","-t","scaleproof:local","."],timeout=900)
    image=json.loads(run(["docker","image","inspect","scaleproof:local"]).stdout)[0]
    identity=dict(source_revision=revision(),image_identity=image["Id"],model_digest=bundle["bundle_digest"],model_bundle=bundle,timeout_seconds=5)
    write_json(ROOT/"artifacts/raw/image.json",identity)
    return identity


if __name__ == "__main__": main()
