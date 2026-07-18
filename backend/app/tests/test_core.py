from app.core import ColonyMindEngine


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
    engine = ColonyMindEngine(seed=42)
    state = engine.step(240)
    assert state["metrics"]["activeOrganisms"] >= 2
    assert state["metrics"]["activeColonies"] >= 1
