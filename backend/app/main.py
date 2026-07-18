from __future__ import annotations

import threading
from typing import Any

from fastapi import FastAPI, HTTPException
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
engine = ColonyMindEngine()
lock = threading.RLock()


@app.get("/health")
def health() -> dict[str, Any]:
    with lock:
        return {"ok": True, "service": "colonymind-api", "stepCount": engine.step_count, "stateHash": engine.state_hash()}


@app.get("/api/state")
def state() -> dict[str, Any]:
    with lock:
        return engine.state()


@app.post("/api/step")
def step(payload: StepRequest) -> dict[str, Any]:
    with lock:
        return engine.step(payload.steps)


@app.post("/api/reset")
def reset(payload: ResetRequest) -> dict[str, Any]:
    with lock:
        engine.reset(payload.seed)
        return engine.state()


@app.post("/api/evaluate")
def evaluate() -> dict[str, Any]:
    with lock:
        return engine.evaluate_hidden()


@app.post("/api/ablate")
def ablate(payload: AblationRequest) -> dict[str, Any]:
    with lock:
        try:
            return engine.ablate(payload.organism_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=f"Unknown organism: {error.args[0]}") from error


@app.get("/api/report")
def report() -> dict[str, Any]:
    with lock:
        return engine.report()
