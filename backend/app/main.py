from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .core import ColonyMindEngine


class StepRequest(BaseModel):
    steps: int = Field(default=1, ge=1, le=240)


class ResetRequest(BaseModel):
    seed: int = Field(default=20260718, ge=1, le=2_147_483_647)


class AblationRequest(BaseModel):
    organism_id: str


app = FastAPI(title="ColonyMind API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
lock = threading.RLock()
engines: OrderedDict[str, ColonyMindEngine] = OrderedDict()
MAX_SESSIONS = 64
SessionId = Annotated[
    str,
    Header(alias="X-ColonyMind-Session", min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
]


def engine_for(session_id: str) -> ColonyMindEngine:
    engine = engines.get(session_id)
    if engine is None:
        if len(engines) >= MAX_SESSIONS:
            engines.popitem(last=False)
        engine = ColonyMindEngine()
        engines[session_id] = engine
    else:
        engines.move_to_end(session_id)
    return engine


@app.get("/health")
def health() -> dict[str, Any]:
    with lock:
        return {"ok": True, "service": "colonymind-api", "activeSessions": len(engines), "sessionIsolation": True}


@app.get("/api/state")
def state(session_id: SessionId) -> dict[str, Any]:
    with lock:
        return engine_for(session_id).state()


@app.post("/api/step")
def step(payload: StepRequest, session_id: SessionId) -> dict[str, Any]:
    with lock:
        return engine_for(session_id).step(payload.steps)


@app.post("/api/reset")
def reset(payload: ResetRequest, session_id: SessionId) -> dict[str, Any]:
    with lock:
        engine = engine_for(session_id)
        engine.reset(payload.seed)
        return engine.state()


@app.post("/api/evaluate")
def evaluate(session_id: SessionId) -> dict[str, Any]:
    with lock:
        return engine_for(session_id).evaluate_hidden()


@app.post("/api/ablate")
def ablate(payload: AblationRequest, session_id: SessionId) -> dict[str, Any]:
    with lock:
        try:
            return engine_for(session_id).ablate(payload.organism_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=f"Unknown organism: {error.args[0]}") from error


@app.get("/api/report")
def report(session_id: SessionId) -> dict[str, Any]:
    with lock:
        return engine_for(session_id).report()
