from app.core import ColonyMindEngine
import random

import numpy as np
import pytest


def test_engine_starts_without_learned_structure() -> None:
    engine = ColonyMindEngine(seed=17)
    state = engine.state()
    assert state["metrics"]["activeCells"] == 0
    assert state["metrics"]["activeOrganisms"] == 0


def test_seed_and_steps_are_deterministic() -> None:
    first = ColonyMindEngine(seed=42)
    second = ColonyMindEngine(seed=42)
    first.step(80)
    second.step(80)
    assert first.state_hash() == second.state_hash()


def test_hidden_evaluation_is_read_only() -> None:
    engine = ColonyMindEngine(seed=42)
    engine.step(80)
    before = engine.state_hash()
    result = engine.evaluate_hidden()
    assert result["modelModified"] is False
    assert engine.state_hash() == before


def test_ablation_is_read_only() -> None:
    engine = ColonyMindEngine(seed=42)
    engine.step(80)
    organism_id = next(iter(engine.organisms))
    before = engine.state_hash()
    result = engine.ablate(organism_id)
    assert result["modelModified"] is False
    assert engine.state_hash() == before


def test_evaluators_do_not_change_the_next_learning_steps() -> None:
    baseline = ColonyMindEngine(seed=23)
    inspected = ColonyMindEngine(seed=23)
    baseline.step(96)
    inspected.step(96)

    inspected.evaluate_hidden()
    inspected.ablate(next(iter(inspected.organisms)))

    baseline.step(36)
    inspected.step(36)
    assert inspected.state_hash() == baseline.state_hash()


def test_novel_unlabeled_stimuli_can_form_a_colony() -> None:
    engine = ColonyMindEngine(seed=20260718)
    state = engine.step(240)
    assert state["metrics"]["activeOrganisms"] >= 2
    assert state["metrics"]["activeColonies"] >= 1
    organism_ids = {organism["id"] for organism in state["organisms"]}
    assert all(set(colony["member_ids"]).issubset(organism_ids) for colony in state["colonies"])


def test_public_stimulus_is_a_label_free_retina() -> None:
    engine = ColonyMindEngine(seed=42)
    vector, public, private_label = engine._sample()

    assert private_label in ("circle", "triangle", "square")
    assert "visualShape" not in public
    assert public["retinaSide"] == 64
    assert len(public["retinaPixels"]) == 64 * 64
    assert vector.shape == (64 * 64,)
    assert public["renderMode"] in ("filled", "outline")
    assert 0.38 <= public["scale"] <= 0.82


def test_retina_changes_with_scale_rotation_noise_and_position() -> None:
    engine = ColonyMindEngine(seed=42)
    first = engine._retina_for("triangle", 0.0, 0.42, 0.01, 0.0, 0.0, 0.0, random.Random(7))
    transformed = engine._retina_for("triangle", 1.1, 0.78, 0.10, 0.18, 0.12, -0.08, random.Random(7))

    assert float(np.mean(np.abs(first - transformed))) > 0.08


def test_retina_supports_filled_and_outline_stimuli() -> None:
    engine = ColonyMindEngine(seed=42)
    filled = engine._retina_for("circle", 0.0, 0.72, 0.0, 0.0, 0.0, 0.0, random.Random(7), "filled")
    outline = engine._retina_for("circle", 0.0, 0.72, 0.0, 0.0, 0.0, 0.0, random.Random(7), "outline")

    assert 0.0 < float(np.sum(outline)) < float(np.sum(filled)) * 0.55
    assert float(np.mean(np.abs(filled - outline))) > 0.12


def test_information_habitat_spreads_different_retinal_inputs() -> None:
    engine = ColonyMindEngine(seed=42)
    coordinates = [engine._information_coordinates(engine._sample()[0]) for _ in range(36)]
    xs, ys = zip(*coordinates)

    assert max(xs) - min(xs) > 15.0
    assert max(ys) - min(ys) > 15.0


def test_external_auditor_labels_normalized_outline_drawings() -> None:
    engine = ColonyMindEngine(seed=42)
    for shape, rotation in (("circle", 0.0), ("square", 0.37), ("triangle", 0.37)):
        drawing = engine._retina_for(
            shape,
            rotation,
            0.72,
            0.0,
            0.0,
            0.04,
            -0.03,
            random.Random(1),
            "outline",
        )
        result = engine.audit_drawing(drawing.tolist())

        assert result["externalAuditor"]["drawnLabel"] == shape
        assert result["externalAuditor"]["confidence"] > 0.5


def test_drawing_audit_probes_the_learner_without_modifying_it() -> None:
    engine = ColonyMindEngine(seed=20260718)
    engine.step(120)
    drawing = engine._retina_for("triangle", 0.2, 0.72, 0.0, 0.0, 0.0, 0.0, random.Random(3), "outline")
    before = engine.state_hash()
    result = engine.audit_drawing(drawing.tolist())

    assert result["ecosystemResponse"]["organismId"] is not None
    assert result["modelModified"] is False
    assert result["stateHashBefore"] == before == result["stateHashAfter"]


def test_drawing_audit_rejects_an_empty_retina() -> None:
    engine = ColonyMindEngine(seed=42)

    with pytest.raises(ValueError, match="complete shape"):
        engine.audit_drawing([0.0] * engine.vector_size)


def test_performance_report_contains_structure_and_drawing_evidence() -> None:
    engine = ColonyMindEngine(seed=20260718)
    engine.step(48)
    drawing = engine._retina_for("square", 0.2, 0.72, 0.0, 0.0, 0.0, 0.0, random.Random(4), "outline")
    audit = engine.audit_drawing(drawing.tolist())
    before = engine.state_hash()
    report = engine.report()

    assert report["schema"] == "colonymind.performance-report.v2"
    assert report["simulation"]["stateHash"] == before == engine.state_hash()
    assert report["performance"]["cells"]["active"] == len(engine.cells)
    assert report["performance"]["cells"]["prototypeUpdateOperations"] > 0
    assert report["performance"]["population"]["activeOrganisms"] == len(engine.organisms)
    assert report["performance"]["colonies"]["active"] == len(engine.colonies)
    assert report["performance"]["structuralAdaptations"]["byType"]["CELL_BIRTH"] >= 1
    assert report["performance"]["drawAndAudit"]["trials"] == 1
    assert report["performance"]["drawAndAudit"]["results"][0]["auditId"] == audit["auditId"]
    assert report["performance"]["drawAndAudit"]["results"][0]["externalAuditor"]["drawnLabel"] == "square"
    assert report["recommendations"]
