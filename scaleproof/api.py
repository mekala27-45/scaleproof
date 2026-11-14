"""Public deterministic policy API. No cluster or inference imports."""
import json
import os
from pathlib import Path
from typing import Annotated, Literal
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from .common import ROOT, read_json
from .storage import Store, StoreError


class Workload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    schema_version: Literal[1]
    low_rps: Annotated[float, Field(strict=True)]
    high_rps: Annotated[float, Field(strict=True)]
    duration_seconds: StrictInt
    warmup_seconds: StrictInt
    high_start_seconds: StrictInt
    high_end_seconds: StrictInt
    min_replicas: StrictInt
    max_replicas: StrictInt
    request_timeout_seconds: Annotated[float, Field(strict=True)]


def create_app(store=None, origin=None):
    live = os.getenv("SCALEPROOF_MODE") == "live"
    store = store or Store(os.getenv("DATABASE_URL", str(ROOT / "artifacts/private/receipts.db")), live)
    origin = origin or os.getenv("ALLOWED_ORIGIN", "http://127.0.0.1:5173")
    app = FastAPI(title="Scaleproof admission API", docs_url=None, redoc_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_credentials=True,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Idempotency-Key"])

    @app.middleware("http")
    async def boundary(request, call_next):
        if request.method == "POST":
            if request.headers.get("origin") not in (None, origin):
                return Response("Origin is not allowed.", status_code=403)
            if request.headers.get("content-type", "").split(";")[0] != "application/json":
                return Response("Use application/json.", status_code=415)
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 4096:
                    return Response("Request body exceeds 4096 bytes.", status_code=413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(StoreError)
    async def storage_error(request, exc):
        return Response(json.dumps({"detail": exc.message}), status_code=exc.status, media_type="application/json")

    @app.get("/health")
    def health():
        return {"status": "alive", "inference": False, "load_execution": False}

    @app.get("/ready")
    def ready():
        try:
            store.ready()
        except Exception:
            raise HTTPException(503, "Receipt storage is unavailable.")
        return {"status": "ready", "mode": "deterministic_live" if live else "deterministic_local"}

    @app.post("/v1/sessions", status_code=201)
    def session(response: Response):
        token = store.new_session()
        response.set_cookie("scaleproof_session", token, max_age=86400, secure=live, httponly=True,
                            samesite="none" if live else "lax", path="/")
        return {"expires_in_seconds": 86400, "workload_check_budget": 50}

    @app.post("/v1/workload-checks")
    def workload(payload: Workload, request: Request):
        try:
            return store.create(request.cookies.get("scaleproof_session", ""),
                                request.headers.get("Idempotency-Key", ""), payload.model_dump())
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    @app.get("/v1/workload-checks/{receipt_id}")
    def receipt(receipt_id: str, request: Request):
        if len(receipt_id) != 32 or any(ch not in "0123456789abcdef" for ch in receipt_id):
            raise HTTPException(404, "Receipt not found in this session.")
        return store.get(request.cookies.get("scaleproof_session", ""), receipt_id)

    @app.get("/v1/experiments/{experiment_id}")
    def experiment(experiment_id: str):
        if experiment_id != "core-v1":
            raise HTTPException(404, "Unknown experiment.")
        return read_json(ROOT / "artifacts/manifests/core-v1.json")

    return app


app = create_app()
