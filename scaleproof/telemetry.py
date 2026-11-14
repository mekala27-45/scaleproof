"""Append-only per-pod records on the owned node, independent of HTTP and log rotation."""
import json
import os
from pathlib import Path
import re

def append_event(record):
    directory=os.getenv("SCALEPROOF_EVENT_DIR")
    if not directory: return
    pod=record["pod_uid"]
    if not re.fullmatch(r"[A-Za-z0-9-]{1,64}",pod): raise ValueError("Invalid pod evidence identity")
    body=(json.dumps(record,sort_keys=True,separators=(",",":"))+"\n").encode()
    descriptor=os.open(Path(directory)/(pod+".jsonl"),os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
    try:
        if os.write(descriptor,body)!=len(body): raise OSError("Incomplete server event write")
    finally: os.close(descriptor)
