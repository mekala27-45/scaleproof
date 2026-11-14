"""Small explicit source/artifact ruleset. Never emits matching secret values."""
import ast
import re
import subprocess
import sys
from pathlib import Path
from .common import ROOT, write_json, now

RULES={
    "private_key":re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "credential_uri":re.compile(rb"postgres(?:ql)?://[^\s:/]+:[^\s@]+@"),
    "github_token":re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    "neon_password":re.compile(rb"npg_[A-Za-z0-9]{15,}")
}
PUBLIC={"api","storage","policy","common"}
EXECUTION={"operations","load","serving","inference","bootstrap","run_pairs","recover_pod","cleanup","build_image"}
def boundary(root=ROOT):
    pending=["api"]; seen=set()
    while pending:
        module=pending.pop()
        if module in seen: continue
        seen.add(module)
        tree=ast.parse((root/"scaleproof"/(module+".py")).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.level==1 and node.module:
                target=node.module.split(".")[0]
                if target in EXECUTION: raise ValueError("Public dependency reaches execution module: "+target)
                if target not in PUBLIC: raise ValueError("Unreviewed public dependency: "+target)
                pending.append(target)
    return sorted(seen)

def scan(paths):
    findings=[]
    for path in paths:
        if path.is_file() and path.stat().st_size<20_000_000:
            body=path.read_bytes()
            for name,pattern in RULES.items():
                if pattern.search(body): findings.append({"file":str(path.relative_to(ROOT)),"rule":name})
    return findings

def main():
    image="--image" in sys.argv
    paths=list(ROOT.rglob("*.py"))+[ROOT/"requirements.txt"] if image else [ROOT/p for p in subprocess.check_output(["git","ls-files"],cwd=ROOT,text=True).splitlines()]
    paths=[p for p in paths if "node_modules" not in p.parts and ".git" not in p.parts]
    findings=scan(paths)
    report={"schema_version":1,"mode":"image_scan" if image else "source_scan","observed_at":now(),"rules":list(RULES),"files_scanned":len(paths),"findings":findings,"public_dependencies":boundary(),"limit":"Pattern and import-boundary checks only; not a general security certificate."}
    if not image: write_json(ROOT/"artifacts/checks/security.json",report)
    import json
    print(json.dumps(report))
    if findings: raise SystemExit(1)
if __name__=="__main__": main()
