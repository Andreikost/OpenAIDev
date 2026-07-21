from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

from app.experiments import (
    BASELINE_CORE_SHA256,
    BASELINE_ID,
    ExperimentDesigner,
    ExperimentProposal,
    ExperimentProtocol,
    ExperimentRegistry,
    _advance_engine_to,
    evaluate_protocol,
    run_experiment,
)
from app.auth import AuthUser
from app.variant_engine import KernelVariantSpec, create_variant_engine


def sample_proposal() -> ExperimentProposal:
    return ExperimentProposal.model_validate(
        {
            "title": "Replicate the hidden evaluation across two seeds",
            "shortLabel": "Two-seed replication",
            "hypothesis": "Hidden-label alignment persists across independent initial conditions.",
            "rationale": "The research audit identifies single-seed evidence as the highest-priority uncertainty.",
            "protocol": {
                "experimentType": "multi_seed_replication",
                "seeds": [20260718, 20260719],
                "trainingSteps": 240,
                "samplesPerShape": 8,
                "nuisanceProfile": "baseline",
                "checkpoints": [],
            },
            "successCriteria": [
                "Mean hidden-evaluator purity is at least 0.75.",
                "Every evaluator state hash is preserved.",
            ],
            "changesFromParent": ["Run the immutable learner under two preregistered seeds."],
            "judgeExplanation": "This version tests reproducibility without changing the submitted learner.",
        }
    )


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def parse(self, **kwargs: object) -> SimpleNamespace:
        self.kwargs = kwargs
        return SimpleNamespace(
            output_parsed=sample_proposal(),
            usage=SimpleNamespace(input_tokens=500, output_tokens=200, total_tokens=700),
        )


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_baseline_core_fingerprint_is_frozen() -> None:
    core_path = Path(__file__).parents[1] / "core.py"
    normalized = core_path.read_text(encoding="utf-8").replace("\r\n", "\n").encode()
    assert hashlib.sha256(normalized).hexdigest() == BASELINE_CORE_SHA256


def test_experiment_designer_uses_structured_outputs_without_tools() -> None:
    client = FakeClient()
    designer = ExperimentDesigner(client=client)  # type: ignore[arg-type]

    proposal, usage = designer.propose(
        {"analysis": {"verdict": "promising but preliminary"}},
        "Use two seeds and preserve the baseline.",
    )

    request = client.responses.kwargs
    assert request["model"] == "gpt-5.6-sol"
    assert request["text_format"] is ExperimentProposal
    assert request["store"] is False
    assert "tools" not in request
    assert proposal.protocol.seeds == [20260718, 20260719]
    assert usage == {"inputTokens": 500, "outputTokens": 200, "totalTokens": 700}


def test_protocol_normalizes_explanatory_checkpoints_and_vps_compute() -> None:
    protocol = ExperimentProtocol.model_validate(
        {
            "experimentType": "multi_seed_replication",
            "seeds": [1, 2, 3, 4, 5],
            "trainingSteps": 2400,
            "samplesPerShape": 24,
            "nuisanceProfile": "mixed",
            "checkpoints": [240],
        }
    )

    assert protocol.trainingSteps == 1440
    assert protocol.checkpoints == []
    assert len(protocol.seeds) * protocol.trainingSteps == 7200


def test_learning_curve_receives_safe_default_checkpoints() -> None:
    protocol = ExperimentProtocol.model_validate(
        {
            "experimentType": "learning_curve",
            "seeds": [17, 17],
            "trainingSteps": 240,
            "samplesPerShape": 8,
            "nuisanceProfile": "baseline",
            "checkpoints": [],
        }
    )

    assert len(protocol.seeds) == 2
    assert protocol.checkpoints == [120, 240]


def test_isolated_runner_reports_nmi_ari_and_preserves_evaluator_state() -> None:
    result = run_experiment(sample_proposal())

    assert result["baselineId"] == BASELINE_ID
    assert result["baselinePreserved"] is True
    assert len(result["runs"]) == 2
    assert set(result["aggregate"]) == {"purity", "nmi", "ari", "fragmentation"}
    assert all(run["final"]["stateHashBefore"] == run["final"]["stateHashAfter"] for run in result["runs"])
    assert all(run["actualTrainingSteps"] == 240 for run in result["runs"])
    assert all(item["status"] == "passed" for item in result["criteria"])


def test_advance_engine_chunks_requests_beyond_core_batch_limit() -> None:
    engine = create_variant_engine(17, KernelVariantSpec())
    advancement = _advance_engine_to(engine, 480)

    assert engine.step_count == 480
    assert advancement == {"requestedFrom": 0, "requestedTo": 480, "actualStep": 480, "engineCalls": 2}


def test_extended_shape_vocabulary_is_balanced_and_read_only() -> None:
    variant = KernelVariantSpec(shapes=["circle", "triangle", "square", "pentagon", "star", "cross"])
    engine = create_variant_engine(23, variant)
    engine.step(24)
    protocol = sample_proposal().protocol
    evaluation = evaluate_protocol(engine, protocol)

    assert evaluation["sampleCount"] == 48
    assert evaluation["shapeCounts"] == {shape: 8 for shape in variant.shapes}
    assert evaluation["modelModified"] is False


def test_matched_arms_keep_identical_stimuli_when_structural_rng_diverges() -> None:
    control = create_variant_engine(31, KernelVariantSpec())
    variant = create_variant_engine(31, KernelVariantSpec(mechanisms=["memory_gated_growth"]))
    for _ in range(20):
        variant.rng.random()

    control_vector, control_public, control_label = control._sample()
    variant_vector, variant_public, variant_label = variant._sample()

    assert control_label == variant_label
    assert control_public["rotation"] == variant_public["rotation"]
    assert control_public["renderMode"] == variant_public["renderMode"]
    assert (control_vector == variant_vector).all()


def test_derived_kernel_runs_a_matched_policy_control() -> None:
    data = sample_proposal().model_dump()
    data["kernel"] = {
        "mode": "derived_copy",
        "shapes": ["circle", "triangle", "square"],
        "parameterOverrides": {"microNoveltyThreshold": 0.016},
        "changeSummary": ["Test a bounded micro-detail threshold."],
    }
    result = run_experiment(ExperimentProposal.model_validate(data))

    assert result["controlAggregate"] is not None
    assert result["comparison"] is not None
    assert result["kernelProvenance"]["generatedCodeExecuted"] is False
    assert result["kernelProvenance"]["appliedParameterOverrides"] == {"microNoveltyThreshold": 0.016}
    assert result["baselinePreserved"] is True


def test_anonymous_workspaces_are_ephemeral_and_isolated(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    registry = ExperimentRegistry()
    record = registry.create("workspace_one", None, sample_proposal(), "replicate", BASELINE_ID)

    assert registry.list("workspace_one", None)[0].id == record.id
    assert registry.list("workspace_two", None) == []
    assert registry.delete("workspace_one", None, BASELINE_ID) is False
    assert registry.delete("workspace_one", None, record.id) is True


def test_authenticated_versions_persist_in_database(monkeypatch, tmp_path) -> None:
    database_path = (tmp_path / "experiments.sqlite3").as_posix()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    registry = ExperimentRegistry()
    user = AuthUser(id="google-subject-1", email="researcher@example.com")

    record = registry.create(
        "ignored_for_authenticated_users",
        user,
        sample_proposal(),
        "replicate across seeds",
        BASELINE_ID,
        {"totalTokens": 700},
    )

    restored_registry = ExperimentRegistry()
    restored = restored_registry.list("another_workspace", user)
    assert restored[0].id == record.id
    assert restored[0].persistent is True
    assert restored[0].generationUsage == {"totalTokens": 700}
    assert restored_registry.delete("another_workspace", user, record.id) is True
