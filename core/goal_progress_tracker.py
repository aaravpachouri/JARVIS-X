from __future__ import annotations

import time


class GoalProgressTracker:
    """
    Tracks task outcomes and converts them into goal progress/status.
    """

    def __init__(self, goal_context):
        self.goals = goal_context
        self.task_states = {}
        self.task_results = {}
        self.updated_at = time.time()

    def register_tasks(self, goal_id, tasks):
        task_ids = []

        for task in tasks:
            task_id = str(getattr(task, "task_id", "") or "").strip()
            if task_id:
                self.task_states[task_id] = "PENDING"
                task_ids.append(task_id)

        self.updated_at = time.time()

        return {
            "goal_id": goal_id,
            "task_ids": task_ids,
            "task_count": len(task_ids),
        }

    def mark_running(self, task_id):
        self._set(task_id, "RUNNING")

    def mark_completed(self, task_id, result=None):
        self.task_results[str(task_id)] = result
        self._set(task_id, "COMPLETED")

    def mark_failed(self, task_id, error=None):
        self.task_results[str(task_id)] = error
        self._set(task_id, "FAILED")

    def mark_cancelled(self, task_id, reason=None):
        self.task_results[str(task_id)] = reason
        self._set(task_id, "CANCELLED")

    def update_goal_progress(self, goal_id):
        states = list(self.task_states.values())

        completed = sum(state == "COMPLETED" for state in states)
        progress = completed / len(states) if states else 0.0

        goal = self.goals.get(goal_id)

        if any(state == "FAILED" for state in states):
            status = "BLOCKED"
        elif any(state == "CANCELLED" for state in states):
            status = "PAUSED"
        elif progress >= 1.0 and states:
            status = "COMPLETED"
        else:
            status = "ACTIVE"

        self.goals.update_progress(goal_id, progress)

        if goal is not None:
            goal.status = status
            goal.updated_at = time.time()

        self.updated_at = time.time()

        return {
            "goal_id": goal_id,
            "progress": progress,
            "status": status,
            "task_count": len(states),
        }

    def next_ready_task(self, tasks):
        completed = {
            task_id
            for task_id, state in self.task_states.items()
            if state == "COMPLETED"
        }

        for task in sorted(tasks, key=lambda item: getattr(item, "order", 0)):
            task_id = str(getattr(task, "task_id", "") or "")

            if self.task_states.get(task_id, "PENDING") != "PENDING":
                continue

            dependencies = list(getattr(task, "dependencies", []) or [])

            if all(dep in completed for dep in dependencies):
                return task

        return None

    def snapshot(self):
        return {
            "task_states": dict(self.task_states),
            "task_results": dict(self.task_results),
            "updated_at": self.updated_at,
        }

    def _set(self, task_id, state):
        self.task_states[str(task_id)] = str(state).upper()
        self.updated_at = time.time()