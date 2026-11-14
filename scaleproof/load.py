"""Bounded open-loop client. Public admission handlers cannot import this."""
import asyncio
import time
import httpx
from .schedule import verify


async def execute(schedule, run_id, timeout_seconds=5, target="http://127.0.0.1:18080", concurrency=64):
    verify(schedule)
    if target != "http://127.0.0.1:18080" or not 1 <= timeout_seconds <= 10 or not 1 <= concurrency <= 64:
        raise ValueError("Only the owned localhost target and bounded limits are permitted")
    start = time.monotonic()
    records, active = [], set()
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=0)
    async with httpx.AsyncClient(limits=limits, trust_env=False, follow_redirects=False) as client:
        async def dispatch(row):
            out = {**row, "request_id": run_id + ":" + row["id"], "dispatched_seconds": time.monotonic() - start}
            deadline = row["scheduled_seconds"] + timeout_seconds
            try:
                response = await client.post(target + "/infer", json={"query": row["query"], "request_id": out["request_id"], "timeout_seconds": timeout_seconds}, timeout=max(.001, deadline - (time.monotonic() - start)), headers={"Connection": "close"})
                out["finished_seconds"] = time.monotonic() - start
                out["http_status"] = response.status_code
                out["response_bytes"] = len(response.content)
                out["status"] = "completed" if response.status_code == 200 and out["finished_seconds"] <= deadline else "timeout" if response.status_code in (200, 504) else "rejected" if response.status_code == 429 else "error"
                if response.status_code == 200:
                    out["receipt"] = response.json()
            except httpx.TimeoutException:
                out.update(status="timeout", finished_seconds=time.monotonic() - start)
            except (httpx.HTTPError, ValueError) as exc:
                out.update(status="error", finished_seconds=time.monotonic() - start, error=type(exc).__name__)
            except asyncio.CancelledError:
                out.update(status="unfinished", finished_seconds=time.monotonic() - start)
            finally:
                records.append(out)

        for row in schedule["rows"]:
            await asyncio.sleep(max(0, start + row["scheduled_seconds"] - time.monotonic()))
            lag = time.monotonic() - start - row["scheduled_seconds"]
            if len(active) >= concurrency or lag > .1:
                records.append({**row, "request_id": run_id + ":" + row["id"], "status": "dispatch_failure", "dispatch_lag_seconds": lag,
                                "reason": "client_concurrency" if len(active) >= concurrency else "client_dispatch_lag"})
                continue
            task = asyncio.create_task(dispatch(row))
            active.add(task)
            task.add_done_callback(active.discard)
        remaining = start + schedule["duration_seconds"] - time.monotonic()
        if active:
            done, pending = await asyncio.wait(active, timeout=max(0, remaining))
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        # Keep the full declared no-arrival observation window.
        await asyncio.sleep(max(0, start + schedule["duration_seconds"] - time.monotonic()))
    return sorted(records, key=lambda r: r["id"])
