from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .core import ColonyMindEngine
from .auth import (
    AuthSession,
    AuthUser,
    GoogleLoginRequest,
    auth_config,
    issue_session,
    optional_user,
    verify_google_access_token,
)
from .experiments import (
    BASELINE_ID,
    ExperimentDesigner,
    ExperimentExecutor,
    ExperimentRecord,
    ExperimentRegistry,
    GenerateExperimentRequest,
    baseline_manifest,
)
from .research_auditor import ResearchAuditor, build_research_snapshot


class StepRequest(BaseModel):
    steps: int = Field(default=1, ge=1, le=240)


class ResetRequest(BaseModel):
    seed: int = Field(default=20260718, ge=1, le=2_147_483_647)


class AblationRequest(BaseModel):
    organism_id: str


PixelIntensity = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]


class DrawingAuditRequest(BaseModel):
    pixels: list[PixelIntensity] = Field(min_length=4096, max_length=4096)


app = FastAPI(title="ColonyMind API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
lock = threading.RLock()
engines: OrderedDict[str, ColonyMindEngine] = OrderedDict()
research_auditor = ResearchAuditor()
experiment_designer = ExperimentDesigner()
experiment_registry = ExperimentRegistry()
experiment_executor = ExperimentExecutor(experiment_registry)
MAX_SESSIONS = 64
SessionId = Annotated[
    str,
    Header(alias="X-ColonyMind-Session", min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
]
ExperimentWorkspaceId = Annotated[
    str,
    Header(alias="X-Experiment-Workspace", min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
]
OptionalUser = Annotated[AuthUser | None, Depends(optional_user)]


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
        return {
            "ok": True,
            "service": "colonymind-api",
            "activeSessions": len(engines),
            "sessionIsolation": True,
            "researchAuditorConfigured": research_auditor.configured,
            "researchAuditorModel": research_auditor.model,
            "experimentDesignerConfigured": experiment_designer.configured,
            "persistentExperimentsConfigured": experiment_registry.persistent.enabled,
            "immutableBaselineVerified": baseline_manifest()["verified"],
        }


@app.get("/api/auth/config")
def get_auth_config() -> dict[str, Any]:
    return auth_config(experiment_registry.persistent.enabled)


@app.post("/api/auth/google", response_model=AuthSession)
def google_login(payload: GoogleLoginRequest) -> AuthSession:
    return issue_session(verify_google_access_token(payload.accessToken))


@app.get("/api/auth/me")
def auth_me(user: OptionalUser) -> dict[str, Any]:
    return {"user": user}


@app.get("/api/experiments/baseline")
def experiment_baseline() -> dict[str, Any]:
    return baseline_manifest()


@app.get("/api/experiments", response_model=list[ExperimentRecord])
def list_experiments(workspace_id: ExperimentWorkspaceId, user: OptionalUser) -> list[ExperimentRecord]:
    try:
        return experiment_registry.list(workspace_id, user)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/experiments", response_model=ExperimentRecord)
def generate_experiment(
    payload: GenerateExperimentRequest,
    session_id: SessionId,
    workspace_id: ExperimentWorkspaceId,
    user: OptionalUser,
) -> ExperimentRecord:
    if not baseline_manifest()["verified"]:
        raise HTTPException(status_code=503, detail="The immutable baseline fingerprint could not be verified")
    with lock:
        engine = engine_for(session_id)
        state_hash = engine.state_hash()
    audit = research_auditor.cached_for_state(state_hash)
    if audit is None:
        raise HTTPException(status_code=409, detail="Run the GPT-5.6 Research Auditor for this state first")

    parent = None
    if payload.parentId:
        if payload.parentId == BASELINE_ID:
            parent = baseline_manifest()
        else:
            parent_record = experiment_registry.get(workspace_id, user, payload.parentId)
            if parent_record is None:
                raise HTTPException(status_code=404, detail="Parent experiment was not found")
            parent = parent_record.model_dump()
    try:
        proposal, usage = experiment_designer.propose(audit, payload.instruction, parent)
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="GPT-5.6 could not produce a safe experiment version") from error
    return experiment_registry.create(
        workspace_id,
        user,
        proposal,
        payload.instruction,
        payload.parentId or BASELINE_ID,
        usage,
    )


@app.post("/api/experiments/{experiment_id}/run", response_model=ExperimentRecord)
def execute_experiment(
    experiment_id: str,
    workspace_id: ExperimentWorkspaceId,
    user: OptionalUser,
) -> ExperimentRecord:
    if not baseline_manifest()["verified"]:
        raise HTTPException(status_code=503, detail="The immutable baseline fingerprint could not be verified")
    record = experiment_registry.get(workspace_id, user, experiment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Experiment was not found")
    return experiment_executor.submit(workspace_id, user, record)


@app.delete("/api/experiments/{experiment_id}")
def delete_experiment(
    experiment_id: str,
    workspace_id: ExperimentWorkspaceId,
    user: OptionalUser,
) -> dict[str, Any]:
    if experiment_id == BASELINE_ID:
        raise HTTPException(status_code=409, detail="The immutable baseline cannot be deleted")
    deleted = experiment_registry.delete(workspace_id, user, experiment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Experiment was not found")
    return {"deleted": True, "baselinePreserved": True}


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


@app.post("/api/audit-drawing")
def audit_drawing(payload: DrawingAuditRequest, session_id: SessionId) -> dict[str, Any]:
    with lock:
        try:
            return engine_for(session_id).audit_drawing(payload.pixels)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error


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
        engine = engine_for(session_id)
        performance_report = engine.report()
        state_hash = engine.state_hash()
    cached_audit = research_auditor.cached_for_state(state_hash)
    performance_report["externalResearchAudit"] = cached_audit
    return performance_report


@app.post("/api/research-audit")
def research_audit(session_id: SessionId) -> dict[str, Any]:
    # Materialize an immutable, aggregate-only snapshot while the engine is
    # locked. The network call receives no engine reference and runs after the
    # lock is released, so GPT-5.6 has no path back into the learning loop.
    with lock:
        engine = engine_for(session_id)
        state_hash_before = engine.state_hash()
        snapshot = build_research_snapshot(engine)
        state_hash_after = engine.state_hash()
    if state_hash_before != state_hash_after:
        raise HTTPException(status_code=500, detail="Research snapshot changed the learner state")

    try:
        result = research_auditor.analyze(snapshot, session_id)
    except RuntimeError as error:
        if "OPENAI_API_KEY" in str(error):
            raise HTTPException(status_code=503, detail="GPT-5.6 Research Auditor is not configured") from error
        raise HTTPException(status_code=502, detail="GPT-5.6 returned an invalid research audit") from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="GPT-5.6 Research Auditor is temporarily unavailable") from error

    with lock:
        current_hash = engine_for(session_id).state_hash()
    return {
        **result,
        "snapshotExtractionHashBefore": state_hash_before,
        "snapshotExtractionHashAfter": state_hash_after,
        "liveStateHashAtResponse": current_hash,
        "liveStateAdvancedDuringAudit": current_hash != state_hash_after,
    }
