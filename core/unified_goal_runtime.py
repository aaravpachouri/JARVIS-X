from __future__ import annotations

from typing import Any, Optional

from core.goal_runtime_coordinator import GoalRuntimeCoordinator
from core.goal_continuity import GoalContinuityManager
from core.goal_context_injector import GoalContextInjector


class UnifiedGoalRuntime:
    """Final Phase 8.9 facade for goal/intent runtime."""

    def __init__(
        self,
        runtime: Optional[GoalRuntimeCoordinator] = None,
        *,
        conversation_context=None,
    ):
        self.runtime = runtime or GoalRuntimeCoordinator()
        self.continuity = GoalContinuityManager(
            self.runtime,
            conversation_context=conversation_context,
        )
        self.injector = GoalContextInjector(self.continuity)

    def resolve_command(self, command: str):
        return self.continuity.resolve_command(command)

    def establish(self, command: str):
        return self.runtime.establish_goal(command)

    def plan_active_goal(self):
        return self.runtime.plan_goal()

    def task_started(self, task_id: str):
        return self.runtime.task_started(task_id)

    def task_completed(self, task_id: str, result: Any = None):
        return self.runtime.task_completed(task_id, result)

    def task_failed(self, task_id: str, error: Any = None):
        return self.runtime.task_failed(task_id, error)

    def next_ready_task(self, tasks):
        return self.runtime.next_ready_task(tasks)

    def switch_goal(self, goal_id: str) -> bool:
        return self.continuity.switch_goal(goal_id)

    def complete_active_goal(self) -> bool:
        return self.continuity.complete_active_goal()

    def augment_reasoning_context(
        self,
        query: str,
        existing_context=None,
    ):
        return self.injector.augment(
            query,
            existing_context=existing_context,
        )

    def goal_text_for_model(self, query: str) -> str:
        return self.injector.format_for_model(query)

    def compact_context(self) -> dict[str, Any]:
        return {
            "goal": self.continuity.compact_context(),
            "runtime": self.runtime.compact_context(),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime.snapshot(),
            "continuity": self.continuity.snapshot(),
        }


def create_goal_runtime(*, conversation_context=None):
    return UnifiedGoalRuntime(
        conversation_context=conversation_context
    )