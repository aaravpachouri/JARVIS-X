from __future__ import annotations
from typing import Any, Optional
from core.goal_context import GoalContext
from core.goal_detection import GoalDetection
from core.goal_decomposition import GoalDecomposer
from core.goal_task_planner import GoalTaskPlanner
from core.goal_progress_tracker import GoalProgressTracker
from core.persistent_goal_store import PersistentGoalStore

class GoalRuntimeCoordinator:
    """Unified Phase 8.9 goal/intent runtime facade."""
    def __init__(self, *, goal_context=None, detector=None, decomposer=None,
                 task_planner=None, persistent_store=None):
        self.context = goal_context or GoalContext()
        self.detector = detector or GoalDetection()
        self.decomposer = decomposer or GoalDecomposer()
        self.task_planner = task_planner or GoalTaskPlanner()
        self.store = persistent_store or PersistentGoalStore()
        self.progress = GoalProgressTracker(self.context)

    def detect(self, command):
        active = self.context.active_goal()
        return self.detector.detect(
            command,
            existing_goal=active.to_dict() if active else None
        )

    def establish_goal(self, command):
        detection = self.detect(command)
        if not detection.get("goal_detected"):
            return {"created": False, "detection": detection}
        if detection.get("continuation"):
            active = self.context.active_goal()
            return {"created": False, "continued": active is not None,
                    "goal": active.to_dict() if active else None,
                    "detection": detection}
        goal = self.context.create_goal(
            detection.get("title", "Untitled goal"),
            description=detection.get("description", command),
            priority=50,
        )
        self.store.save(goal)
        return {"created": True, "goal": goal.to_dict(), "detection": detection}

    def plan_goal(self, goal_id: Optional[str] = None):
        goal = self.context.get(goal_id or self.context.active_goal_id)
        if goal is None:
            return {"planned": False, "error": "No active goal is available."}
        steps = self.decomposer.decompose(goal.title, context={"goal": goal.to_dict()})
        tasks = self.task_planner.plan(goal, steps, context={"goal": goal.to_dict()})
        self.progress.register_tasks(goal.goal_id, tasks)
        return {"planned": True, "goal": goal.to_dict(),
                "steps": [s.to_dict() for s in steps],
                "tasks": [t.to_dict() for t in tasks]}

    def task_started(self, task_id): self.progress.mark_running(task_id)

    def task_completed(self, task_id, result=None):
        self.progress.mark_completed(task_id, result)
        goal = self.context.active_goal()
        if not goal: return None
        state = self.progress.update_goal_progress(goal.goal_id)
        self.store.save(goal)
        return state

    def task_failed(self, task_id, error=None):
        self.progress.mark_failed(task_id, error)
        goal = self.context.active_goal()
        if not goal: return None
        state = self.progress.update_goal_progress(goal.goal_id)
        self.store.save(goal)
        return state

    def next_ready_task(self, tasks):
        return self.progress.next_ready_task(tasks)

    def persist_active_goal(self):
        goal = self.context.active_goal()
        return self.store.save(goal) if goal else None

    def restore_active_goals(self, limit=20):
        return self.store.active(limit)

    def compact_context(self):
        return {"goal": self.context.compact_context(),
                "progress": self.progress.snapshot()}

    def snapshot(self):
        return {"goal_context": self.context.snapshot(),
                "progress": self.progress.snapshot(),
                "persisted_active_goals": self.store.active(20)}