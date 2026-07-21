from __future__ import annotations

import json
from types import SimpleNamespace

from app.core import ColonyMindEngine
from app.research_auditor import ResearchAuditAnalysis, ResearchAuditor, build_experiment_research_snapshot, build_research_snapshot


def sample_analysis() -> ResearchAuditAnalysis:
    return ResearchAuditAnalysis.model_validate(
        {
            "headline": "A compact hierarchy is emerging",
            "verdict": "promising but preliminary",
            "judgeTakeaway": "The system grows from residual evidence without training labels.",
            "executiveSummary": "The current run supports a mechanism demo, not a general vision claim.",
            "findings": [
                {
                    "title": "Structure emerged",
                    "observation": "Resident organisms and cells are present.",
                    "evidence": ["structure.organisms.residentOrganisms=5"],
                    "interpretation": "Persistent residuals allocated capacity.",
                }
            ],
            "risks": [
                {
                    "severity": "high",
                    "issue": "Synthetic benchmark only",
                    "whyItMatters": "It does not demonstrate camera generalization.",
                }
            ],
            "nextExperiments": [
                {
                    "priority": "now",
                    "title": "Micro-layer ablation",
                    "hypothesis": "Micro-signatures prevent circle-square confusion.",
                    "protocol": "Compare matched seeded runs with and without the layer.",
                    "successMetric": "Higher ARI without disproportionate active compute.",
                }
            ],
            "publicationReadiness": {
                "stage": "proof of concept",
                "strongestEvidence": "Read-only hidden evaluation",
                "missingEvidence": "Baselines and standard datasets",
            },
            "resourceAssessment": {
                "status": "proxy only",
                "interpretation": "No electrical-energy claim is supported.",
            },
        }
    )


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def parse(self, **kwargs: object) -> SimpleNamespace:
        self.kwargs = kwargs
        return SimpleNamespace(
            id="resp_test_audit",
            model="gpt-5.6-sol-2026-07-01",
            output_parsed=sample_analysis(),
            usage=SimpleNamespace(input_tokens=700, output_tokens=240, total_tokens=940),
        )


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_snapshot_is_compact_read_only_and_excludes_sensitive_model_data() -> None:
    engine = ColonyMindEngine()
    engine.step(240)
    before = engine.state_hash()

    snapshot = build_research_snapshot(engine)
    serialized = json.dumps(snapshot)

    assert engine.state_hash() == before
    assert snapshot["simulation"]["stateHash"] == before
    assert snapshot["boundary"]["learningWriteAccess"] is False
    assert snapshot["boundary"]["rawRetinaShared"] is False
    assert "retinaPixels" not in serialized
    assert "normalizedPixels" not in serialized
    assert '"prototype":' not in serialized.lower()
    assert len(serialized) < 20_000


def test_version_snapshot_excludes_external_audit_recursion_and_preserves_provenance() -> None:
    record = {
        "id": "version-1",
        "version": 1,
        "status": "completed",
        "proposal": {"hypothesis": "A controlled branch improves NMI.", "acceptance": {"minNmi": 0.7}},
        "result": {
            "protocol": {"trainingSteps": 480},
            "kernel": {"mode": "derived_copy"},
            "kernelProvenance": {"generatedCodeExecuted": False},
            "aggregate": {"nmi": {"mean": 0.9}},
            "criteria": [{"status": "passed"}],
            "runs": [],
            "baselinePreserved": True,
            "externalAudit": {"should": "not be hashed recursively"},
        },
    }
    snapshot = build_experiment_research_snapshot(record)

    assert snapshot["schema"] == "colonymind-version-research-snapshot/v1"
    assert snapshot["boundary"]["generatedCodeExecuted"] is False
    assert snapshot["boundary"]["immutableBaselinePreserved"] is True
    assert "externalAudit" not in str(snapshot)


def test_structured_gpt_audit_uses_responses_api_without_tools_or_storage(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6-sol")
    client = FakeClient()
    auditor = ResearchAuditor(client=client)  # type: ignore[arg-type]
    engine = ColonyMindEngine()
    engine.step(48)
    snapshot = build_research_snapshot(engine)

    result = auditor.analyze(snapshot, "cm_test_session")
    request = client.responses.kwargs

    assert request["model"] == "gpt-5.6-sol"
    assert request["reasoning"] == {"effort": "medium"}
    assert request["text_format"] is ResearchAuditAnalysis
    assert request["store"] is False
    assert "tools" not in request
    assert "retinaPixels" not in str(request["input"])
    assert result["modelModified"] is False
    assert result["learningWriteAccess"] is False
    assert result["analysis"]["publicationReadiness"]["stage"] == "proof of concept"
    assert result["usage"]["totalTokens"] == 940

    cached = auditor.analyze(snapshot, "cm_test_session")
    assert cached["cached"] is True
