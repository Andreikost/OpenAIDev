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
    assert state["metrics"]["residentOrganisms"] >= 2
    assert state["metrics"]["microColonies"] >= 1
    organism_ids = {organism["id"] for organism in state["organisms"]}
    assert all(set(colony["member_ids"]).issubset(organism_ids) for colony in state["colonies"])
    micro_ids = {micro["id"] for micro in state["microSignatures"]}
    assert all(set(colony["member_ids"]).issubset(micro_ids) for colony in state["microColonies"])


def test_every_resident_organism_ages_even_when_it_does_not_win() -> None:
    engine = ColonyMindEngine(seed=20260718)
    engine.step(240)

    assert len(engine.organisms) >= 2
    assert any(organism.wins < organism.age_steps for organism in engine.organisms.values())
    assert all(
        organism.age_steps == engine.step_count - organism.born_step
        for organism in engine.organisms.values()
    )


def test_organisms_mature_without_early_archival() -> None:
    engine = ColonyMindEngine(seed=20260718)
    state = engine.step(240)

    assert any(organism["lifecycleState"] == "mature" for organism in state["organisms"])
    assert engine.event_totals.get("ORGANISM_ARCHIVED", 0) == 0
    assert state["metrics"]["residentOrganisms"] == engine.event_totals["ORGANISM_BIRTH"]


def test_response_committee_is_relevance_driven_without_growth_caps() -> None:
    engine = ColonyMindEngine(seed=20260718)
    state = engine.step(240)

    assert state["metrics"]["activeOrganisms"] <= state["metrics"]["residentOrganisms"]
    assert state["metrics"]["activeCells"] <= state["metrics"]["residentCells"]
    assert not hasattr(engine, "max_processing_organisms")
    assert not hasattr(engine, "max_resident_organisms")
    assert not hasattr(engine, "response_committee_size")


def test_cell_and_organism_counts_have_no_fixed_growth_ceiling() -> None:
    engine = ColonyMindEngine(seed=11)
    vector, _public, _label = engine._sample()
    organism = engine._create_organism(vector, "OPEN_GROWTH_TEST")
    for _index in range(12):
        engine._create_cell(organism, vector, "OPEN_GROWTH_TEST")
    for _index in range(18):
        engine._create_organism(vector, "OPEN_GROWTH_TEST", organism)

    assert len(organism.cells) == 13
    assert len(engine.organisms) == 19


def test_fully_digested_information_becomes_memory_and_stops_growth() -> None:
    engine = ColonyMindEngine(seed=13)
    engine.step(1)
    organism = next(iter(engine.organisms.values()))
    vector = np.asarray(organism.specialization)
    intermediate = engine._intermediate_signature(vector, learn=False)[0]
    organism.digestion_evidence = engine.memory_evidence_required
    memory = engine._consolidate_or_recall_memory(organism, vector, intermediate, 0.01)
    cells_before = len(engine.cells)
    organisms_before = len(engine.organisms)
    organism.food_evidence = engine.residual_support_required + 10.0
    engine.residual_vectors[organism.id] = [vector.copy() for _index in range(8)]

    engine._structural_review(vector, intermediate, 0.01, organism, 0.0)

    assert memory is not None
    assert len(engine.memories) == 1
    assert len(engine.cells) == cells_before
    assert len(engine.organisms) == organisms_before
    assert engine.event_totals["MEMORY_CONSOLIDATED"] == 1


def test_dormant_memory_reactivates_for_familiar_information() -> None:
    engine = ColonyMindEngine(seed=19)
    engine.step(48)
    target = next(iter(engine.organisms.values()))
    target.lifecycle_state = "dormant"
    target.dormant_since = engine.step_count
    vector = np.asarray(target.specialization)

    engine._advance_lifecycle(vector)

    assert target.lifecycle_state == "mature"
    assert target.reactivations == 1
    assert engine.event_totals["ORGANISM_REACTIVATED"] == 1


def test_archive_requires_long_redundancy_and_replay_ablation_evidence() -> None:
    engine = ColonyMindEngine(seed=31)
    vector, _public, _label = engine._sample()
    engine._create_organism(vector, "TEST_MEMORY")
    target = engine._create_organism(vector, "TEST_REDUNDANT_MEMORY")
    engine.step_count = 6_000
    target.lifecycle_state = "dormant"
    target.age_steps = 6_000
    target.last_active_step = 0
    target.protected_until = 0
    target.low_value_steps = engine.low_value_grace
    target.utility = -0.1
    engine.replay_buffer = [vector.copy()]

    engine._archive_if_safe()

    assert target.id not in engine.organisms
    assert engine.event_totals["ORGANISM_ARCHIVED"] == 1
    assert engine.organism_archive[0]["replayAblationDelta"] <= 0.0


def test_minimum_lifespan_protects_even_redundant_dormant_memory() -> None:
    engine = ColonyMindEngine(seed=37)
    vector, _public, _label = engine._sample()
    engine._create_organism(vector, "TEST_MEMORY")
    target = engine._create_organism(vector, "TEST_PROTECTED_MEMORY")
    engine.step_count = 6_000
    target.lifecycle_state = "dormant"
    target.age_steps = 6_000
    target.last_active_step = 0
    target.protected_until = 7_000
    target.low_value_steps = engine.low_value_grace
    target.utility = -0.1
    engine.replay_buffer = [vector.copy()]

    engine._archive_if_safe()

    assert target.id in engine.organisms
    assert engine.event_totals.get("ORGANISM_ARCHIVED", 0) == 0


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


def test_intermediate_geometry_separates_circle_from_square_across_rotation() -> None:
    engine = ColonyMindEngine(seed=42)
    first_circle = engine._retina_for("circle", 0.0, 0.70, 0.02, 0.0, 0.03, -0.02, random.Random(7), "outline")
    rotated_circle = engine._retina_for("circle", 1.17, 0.70, 0.02, 0.0, 0.03, -0.02, random.Random(8), "outline")
    square = engine._retina_for("square", 0.61, 0.70, 0.02, 0.0, 0.03, -0.02, random.Random(9), "outline")

    first_signature = engine._fine_detail_signature(first_circle)
    rotated_signature = engine._fine_detail_signature(rotated_circle)
    square_signature = engine._fine_detail_signature(square)

    circle_distance = float(np.mean((first_signature - rotated_signature) ** 2))
    square_distance = float(np.mean((first_signature - square_signature) ** 2))
    assert circle_distance < square_distance * 0.35


def test_persistent_intermediate_food_grows_label_free_specialists() -> None:
    engine = ColonyMindEngine(seed=20260718)
    state = engine.step(240)

    assert state["metrics"]["microSignatures"] > 1
    assert state["metrics"]["microDigestedDetails"] > 0
    assert engine.event_totals.get("MICRO_SIGNATURE_BIRTH", 0) > 1
    assert engine.event_totals.get("ORGANISM_BIRTH", 0) >= 3


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

    assert report["schema"] == "colonymind.performance-report.v5"
    assert report["simulation"]["stateHash"] == before == engine.state_hash()
    assert report["performance"]["cells"]["resident"] == len(engine.cells)
    assert report["performance"]["cells"]["active"] <= len(engine.cells)
    assert report["performance"]["cells"]["prototypeUpdateOperations"] > 0
    assert report["performance"]["population"]["activeOrganisms"] <= len(engine.organisms)
    assert report["performance"]["population"]["residentOrganisms"] == len(engine.organisms)
    assert report["performance"]["population"]["lifecyclePolicy"]["minimumLifespan"] == 5_000
    assert report["performance"]["population"]["lifecyclePolicy"]["growthLimits"] is None
    assert "memories" in report["performance"]
    assert report["performance"]["intermediateLayer"]["microSignatures"] > 0
    assert report["performance"]["colonies"]["active"] == len(engine.colonies)
    assert report["performance"]["structuralAdaptations"]["byType"]["CELL_BIRTH"] >= 1
    assert report["performance"]["drawAndAudit"]["trials"] == 1
    assert report["performance"]["drawAndAudit"]["results"][0]["auditId"] == audit["auditId"]
    assert report["performance"]["drawAndAudit"]["results"][0]["externalAuditor"]["drawnLabel"] == "square"
    assert report["recommendations"]
