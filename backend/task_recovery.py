from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from backend.agent_recovery import AgentRecoveryPlanner

if TYPE_CHECKING:
    from backend.task_orchestrator import StepResult, TaskStep


class TaskRecoveryCoordinator:
    """
    Thin adapter between TaskOrchestrator and the existing
    AgentRecoveryPlanner.

    Phase 3.7 responsibilities:
        - classify failures
        - record failures
        - prevent repeated blocked routes
        - expose a bounded retry decision

    Dynamic replanning comes in Phase 3.8.
    """

    MAX_RETRIES = 2

    def __init__(self, planner: Optional[AgentRecoveryPlanner] = None):
        self.planner = planner or AgentRecoveryPlanner()
        self.retry_counts: dict[str, int] = {}

    def reset(self) -> None:
        self.planner.reset()
        self.retry_counts.clear()

    @staticmethod
    def _action_for_step(step: TaskStep) -> dict[str, Any]:
        return {
            "tool": str(step.executor or "").strip().upper(),
            "parameters": {"description": step.description},
        }

    def record_failure(self, step: TaskStep, result: Optional[StepResult] = None) -> dict[str, Any]:
        action = self._action_for_step(step)
        error = str(
            getattr(result, "error", "")
            or getattr(step, "error", "")
            or "Step failed."
        )
        failure_type = self.planner.classify_executor_failure(error)
        self.planner.record_failure(action, error, failure_type)

        key = str(step.step_id)
        self.retry_counts[key] = self.retry_counts.get(key, 0) + 1
        retry_count = self.retry_counts[key]
        blocked = self.planner.is_blocked(action)

        return {
            "retry_allowed": retry_count <= self.MAX_RETRIES and not blocked,
            "retry_count": retry_count,
            "max_retries": self.MAX_RETRIES,
            "failure_type": failure_type,
            "blocked": blocked,
            "error": error,
            "recovery_context": self.planner.model_context(),
        }

    def record_success(self, step: TaskStep) -> None:
        self.planner.record_success(self._action_for_step(step))

    def should_retry(self, step: TaskStep) -> bool:
        action = self._action_for_step(step)
        count = self.retry_counts.get(str(step.step_id), 0)
        return count < self.MAX_RETRIES and not self.planner.is_blocked(action)

    def context(self) -> dict[str, Any]:
        return self.planner.model_context()

    def __repr__(self) -> str:
        return f"<TaskRecoveryCoordinator retries={self.retry_counts!r}>"