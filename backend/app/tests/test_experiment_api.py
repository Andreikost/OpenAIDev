from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app, engine_for, experiment_designer, research_auditor
from app.tests.test_experiments import sample_proposal


def test_anonymous_experiment_api_derives_from_current_audit(monkeypatch) -> None:
    session_id = "cm_experiment_api_test"
    workspace_id = "exp_workspace_api_test"
    headers = {
        "X-ColonyMind-Session": session_id,
        "X-Experiment-Workspace": workspace_id,
    }
    with TestClient(app) as client:
        client.post("/api/step", headers=headers, json={"steps": 12}).raise_for_status()
        state_hash = engine_for(session_id).state_hash()
        monkeypatch.setattr(
            research_auditor,
            "cached_for_state",
            lambda requested_hash: {
                "snapshotStateHash": state_hash,
                "analysis": {"verdict": "promising but preliminary"},
            } if requested_hash == state_hash else None,
        )
        monkeypatch.setattr(
            experiment_designer,
            "propose",
            lambda audit, instruction, parent=None: (sample_proposal(), {"totalTokens": 700}),
        )

        created_response = client.post(
            "/api/experiments",
            headers=headers,
            json={"instruction": "replicate", "parentId": None},
        )
        assert created_response.status_code == 200
        created = created_response.json()
        assert created["persistent"] is False
        assert created["baselineId"] == "colonymind-build-week-baseline-v1"

        listed = client.get("/api/experiments", headers=headers).json()
        assert listed[0]["id"] == created["id"]

        baseline_delete = client.delete(
            "/api/experiments/colonymind-build-week-baseline-v1",
            headers=headers,
        )
        assert baseline_delete.status_code == 409

        deleted = client.delete(f"/api/experiments/{created['id']}", headers=headers)
        assert deleted.status_code == 200
        assert deleted.json()["baselinePreserved"] is True
