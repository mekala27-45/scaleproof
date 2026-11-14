"""Executable synthetic mechanism demonstration, never operational evidence."""
import json
from pathlib import Path

duration, service, deadline, offered = 20., .25, 1., 10.
scheduled = [i/offered for i in range(int(duration*offered))]
available, timely = 0., 0
for arrival in scheduled:
    available = max(available, arrival)+service
    timely += available <= arrival+deadline
closed = int(duration/service)
result = {"mode":"synthetic_fault","mechanism":"idealized deterministic single server, no measured network or model",
          "open_loop":{"scheduled":len(scheduled),"deadline_successes":timely,"success_fraction":timely/len(scheduled)},
          "closed_loop":{"offered":closed,"deadline_successes":closed,"success_fraction":1},
          "finding":"Closed-loop demand fell to server completion rate, hiding the intended offered workload."}
assert len(scheduled)==200 and timely==6 and closed==80
target=Path("artifacts/investigations/closed-loop.json")
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result))
