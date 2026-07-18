from app.core import ColonyMindEngine
import random

import numpy as np


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
    assert public["retinaSide"] == 16
    assert len(public["retinaPixels"]) == 16 * 16
    assert vector.shape == (16 * 16,)
    assert 0.38 <= public["scale"] <= 0.82


def test_retina_changes_with_scale_rotation_noise_and_position() -> None:
    engine = ColonyMindEngine(seed=42)
    first = engine._retina_for("triangle", 0.0, 0.42, 0.01, 0.0, 0.0, 0.0, random.Random(7))
    transformed = engine._retina_for("triangle", 1.1, 0.78, 0.10, 0.18, 0.12, -0.08, random.Random(7))

    assert float(np.mean(np.abs(first - transformed))) > 0.08
