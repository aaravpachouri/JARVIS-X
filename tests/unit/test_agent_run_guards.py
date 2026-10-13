import pytest

from backend.agent_run_gate import AgentRunGate
from backend.consecutive_failure_guard import ConsecutiveFailureGuard


def test_run_gate_rejects_a_second_active_computer_loop():
    gate = AgentRunGate()

    assert gate.try_enter() is True
    assert gate.try_enter() is False

    gate.leave()

    assert gate.try_enter() is True
    gate.leave()


def test_consecutive_failure_guard_stops_at_limit_with_last_error():
    guard = ConsecutiveFailureGuard(limit=3)

    assert guard.record_failure("context overflow") is None
    assert guard.record_failure("context overflow") is None

    message = guard.record_failure("context overflow")

    assert guard.consecutive_failures == 3
    assert "3 consecutive local AI failures" in message
    assert "context overflow" in message


def test_success_resets_consecutive_failure_count():
    guard = ConsecutiveFailureGuard(limit=3)

    assert guard.record_failure("temporary error") is None
    guard.record_success()

    assert guard.consecutive_failures == 0
    assert guard.record_failure("temporary error") is None


def test_failure_guard_requires_positive_limit():
    with pytest.raises(ValueError):
        ConsecutiveFailureGuard(limit=0)
