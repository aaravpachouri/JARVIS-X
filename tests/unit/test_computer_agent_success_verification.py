"""Regression tests for the adapter without loading the desktop runtime.

The full ComputerUseAgent imports OS-specific automation dependencies. These
contract tests inject a lightweight placeholder because they always supply a
fake agent and must remain runnable in the dependency-light CI environment.
"""
import sys
from types import ModuleType, SimpleNamespace


computer_agent_module = ModuleType("backend.computer_agent")


class UnusedComputerUseAgent:
    def __init__(self, *args, **kwargs):
        raise AssertionError(
            "Tests must inject FakeComputerAgent instead of creating the real agent."
        )


computer_agent_module.ComputerUseAgent = UnusedComputerUseAgent
sys.modules.setdefault("backend.computer_agent", computer_agent_module)

from automation.executors.computer_agent_executor import ComputerAgentExecutor
from backend.task_orchestrator import TaskStep


class FakeComputerAgent:
    def __init__(self, status, result="Finished"):
        self.state = SimpleNamespace(status=status)
        self.result = result
        self.cancelled = False

    def shouldHandle(self, goal):
        return bool(goal)

    def run(self, goal):
        return self.result

    def is_cancelled(self):
        return self.cancelled

    def cancel(self, reason):
        self.cancelled = True

    def clear_cancel(self):
        self.cancelled = False


def make_step():
    return TaskStep(
        description="Open the calculator",
        executor="COMPUTER_AGENT",
    )


def test_nonempty_result_is_not_success_when_agent_state_failed():
    executor = ComputerAgentExecutor(
        agent=FakeComputerAgent("failed", "I could not safely complete that task.")
    )

    result = executor.execute(make_step())

    assert result.success is False
    assert "did not verify task completion" in result.error
    assert result.metadata["agent_status"] == "failed"
    assert result.metadata["computer_task"]["status"] == "FAILED"


def test_agent_must_report_completed_for_success():
    executor = ComputerAgentExecutor(
        agent=FakeComputerAgent("completed", "Calculator is open.")
    )

    result = executor.execute(make_step())

    assert result.success is True
    assert result.metadata["verified"] is True
    assert result.metadata["computer_task"]["status"] == "COMPLETED"


def test_missing_agent_status_fails_closed():
    agent = FakeComputerAgent("", "Maybe it worked.")
    executor = ComputerAgentExecutor(agent=agent)

    result = executor.execute(make_step())

    assert result.success is False
    assert result.metadata["agent_status"] == "unknown"


def test_none_result_fails_even_if_agent_claims_completed():
    executor = ComputerAgentExecutor(
        agent=FakeComputerAgent("completed", None)
    )

    result = executor.execute(make_step())

    assert result.success is False
    assert "returned no result" in result.error
