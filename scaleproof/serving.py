"""One bounded admission worker per pod. CPU work stays off the event loop."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
import json
import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .common import ROOT, canonical, now, revision
from .inference import Kernel
from .telemetry import append_event


def log(event, **fields):
    record = {"event": event, "observed_at": now(), "pod_uid": os.getenv("POD_UID", "local")}
    record.update(fields)
    append_event(record)
    print(json.dumps(record), flush=True)


@dataclass
class Job:
    request_id: str
    query: str
    admitted: float
    future: asyncio.Future
    include_embedding: bool = False
    expired: bool = False


class InferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(min_length=1, max_length=1000)
    request_id: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9:_-]+$")
    timeout_seconds: float = Field(ge=1, le=10)
    include_embedding: bool = False


@asynccontextmanager
async def lifespan(app):
    begin = time.monotonic()
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="encoder")
    loop = asyncio.get_running_loop()
    kernel = await loop.run_in_executor(pool, Kernel, os.getenv("MODEL_DIRECTORY", str(ROOT / "models/bge")))
    queue = asyncio.Queue(maxsize=8)
    app.state.ready = True
    app.state.queue = queue
    app.state.kernel = kernel
    app.state.accepting = True
    log("model_ready", model_digest=kernel.encoder.manifest["bundle_digest"], corpus_digest=kernel.corpus_digest, startup_seconds=time.monotonic()-begin)

    async def worker():
        while True:
            job = await queue.get()
            if job is None:
                queue.task_done()
                break
            started = time.monotonic()
            log("started", request_id=job.request_id, queue_wait_ms=(started-job.admitted)*1000)
            try:
                result = await loop.run_in_executor(pool, kernel.retrieve, job.query)
                result.update(request_id=job.request_id, pod_uid=os.getenv("POD_UID", "local"), source_revision=revision(),
                              image_identity=os.getenv("IMAGE_IDENTITY", "unavailable"), queue_wait_ms=(started-job.admitted)*1000,
                              service_ms=(time.monotonic()-started)*1000)
                log("finished", request_id=job.request_id, late=job.expired, **{k:v for k,v in result.items() if k not in ("embedding", "request_id")})
                if not job.include_embedding:
                    result.pop("embedding", None)
                if not job.future.done():
                    job.future.set_result(result)
            except Exception as exc:
                log("inference_error", request_id=job.request_id, error=type(exc).__name__)
                if not job.future.done():
                    job.future.set_exception(RuntimeError("Actual encoder failed"))
            finally:
                queue.task_done()
    task = asyncio.create_task(worker())
    try:
        yield
    finally:
        app.state.accepting = False
        app.state.ready = False
        try:
            await asyncio.wait_for(queue.join(), timeout=25)
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            pool.shutdown(wait=True)


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "alive"}


@app.get("/ready")
def ready():
    if not getattr(app.state, "ready", False):
        raise HTTPException(503, "Model is not ready")
    return {"status": "ready", "pod_uid": os.getenv("POD_UID", "local"), "model_digest": app.state.kernel.encoder.manifest["bundle_digest"], "corpus_digest": app.state.kernel.corpus_digest}


@app.post("/infer")
async def infer(payload: InferenceRequest):
    if not app.state.accepting:
        raise HTTPException(503, "Worker is draining")
    job = Job(payload.request_id, payload.query, time.monotonic(), asyncio.get_running_loop().create_future(), payload.include_embedding)
    try:
        app.state.queue.put_nowait(job)
    except asyncio.QueueFull:
        log("overload", request_id=payload.request_id)
        raise HTTPException(429, "Admission queue is full")
    log("admitted", request_id=payload.request_id)
    try:
        return await asyncio.wait_for(asyncio.shield(job.future), timeout=payload.timeout_seconds)
    except asyncio.TimeoutError:
        job.expired = True
        log("server_deadline", request_id=payload.request_id)
        raise HTTPException(504, "Request deadline reached; late completion remains in the server ledger")
    except asyncio.CancelledError:
        job.expired = True
        raise
