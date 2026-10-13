from backend.agent_state import AgentState


def test_cancel_marks_task_cancelled_not_failed():
    state = AgentState()
    state.start("Open calculator")

    state.cancel("User pressed Cancel")

    assert state.status == "cancelled"
    assert state.errors == ["User pressed Cancel"]
    assert not state.is_failed()
    assert not state.is_complete()


def test_cancelled_task_can_be_reset_for_next_task():
    state = AgentState()
    state.start("Open calculator")
    state.cancel("User pressed Cancel")

    state.start("Open browser")

    assert state.status == "running"
    assert state.goal == "Open browser"
    assert state.errors == []
    assert state.completed_at is None
