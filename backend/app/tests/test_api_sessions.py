from app.main import engine_for, engines, lock


def test_browser_sessions_have_independent_engines() -> None:
    with lock:
        engines.clear()
        first = engine_for("cm_first_session")
        second = engine_for("cm_second_session")
        first.step(36)

        assert first.step_count == 36
        assert second.step_count == 0
        assert first is not second


def test_session_registry_reuses_the_same_engine() -> None:
    with lock:
        engines.clear()
        first = engine_for("cm_persistent_session")
        first.step(12)

        assert engine_for("cm_persistent_session").state_hash() == first.state_hash()
