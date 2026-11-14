import os
import platform
import shutil
import sys
from .common import ROOT, envelope, write_json
from .operations import run


def main():
    tools={}
    for name,args in {"docker":["version","--format","{{json .Server}}"],"kind":["version"],"kubectl":["version","--client","-o","json"],"git":["--version"]}.items():
        try:
            result=run([name,*args],check=False,timeout=20)
            tools[name]=dict(available=result.returncode==0,output=result.stdout[:4000],error=result.stderr[:1000])
        except (OSError,RuntimeError) as exc: tools[name]=dict(available=False,error=str(exc))
    record=envelope("host-probe","local_probe",dict(os=platform.platform(),python=sys.version,cpu_count=os.cpu_count(),tools=tools))
    write_json(ROOT/"artifacts/raw/environment.json",record)
    return record


if __name__ == "__main__": main()
