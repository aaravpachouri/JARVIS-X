from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class GoalTask:
    task_id: str
    title: str
    description: str = ""
    order: int = 0
    status: str = "PENDING"
    dependencies: list[str] = field(default_factory=list)
    application: str = ""
    action_type: str = "EXECUTE"
    parameters: dict[str, Any] = field(default_factory=dict)
    goal_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "status": self.status,
            "dependencies": list(self.dependencies),
            "application": self.application,
            "action_type": self.action_type,
            "parameters": dict(self.parameters),
            "goal_id": self.goal_id,
            "metadata": dict(self.metadata),
        }


class GoalTaskPlanner:
    def __init__(self, planner: Optional[Callable[..., Any]] = None):
        self.planner = planner

    def plan(self, goal, steps, *, context=None):
        goal_id = str(getattr(goal, "goal_id", "") or "")

        if self.planner is not None:
            try:
                planned = self.planner(goal, steps, context or {})
                normalized = self._normalize(planned, goal_id)
                if normalized:
                    return normalized
            except Exception as exc:
                print("[GoalTaskPlanner] Planner fallback:", exc)

        tasks = []

        for index, step in enumerate(steps):
            title = str(getattr(step, "title", "") or "").strip()
            description = str(getattr(step, "description", "") or "").strip()
            application = str(getattr(step, "application", "") or "").strip()

            action_type = self._infer_action_type(
                title,
                description,
                application,
            )

            tasks.append(
                GoalTask(
                    task_id=str(uuid.uuid4()),
                    title=title or f"Goal task {index + 1}",
                    description=description,
                    order=int(getattr(step, "order", index) or index),
                    dependencies=list(getattr(step, "dependencies", []) or []),
                    application=application,
                    action_type=action_type,
                    parameters={
                        "goal_step": title,
                        "description": description,
                        "action_type": action_type,
                    },
                    goal_id=goal_id,
                    metadata=dict(getattr(step, "metadata", {}) or {}),
                )
            )

        tasks.sort(key=lambda item: item.order)
        return tasks

    @staticmethod
    def _infer_action_type(title, description, application):
        text = f"{title} {description} {application}".lower()

        checks = (
            (("verify",), "VERIFY"),
            (("open", "navigate"), "OPEN"),
            (("download",), "DOWNLOAD"),
            (("find", "locate"), "FIND"),
            (("move",), "MOVE"),
            (("copy",), "COPY"),
            (("rename",), "RENAME"),
            (("delete", "remove"), "DELETE"),
            (("save",), "SAVE"),
            (("create", "write", "make"), "CREATE"),
        )

        for words, action in checks:
            if any(word in text for word in words):
                return action

        return "EXECUTE"

    @staticmethod
    def _normalize(planned, goal_id):
        if not isinstance(planned, (list, tuple)):
            return []

        tasks = []

        for index, item in enumerate(planned):
            if isinstance(item, GoalTask):
                tasks.append(item)
                continue

            if not isinstance(item, dict):
                continue

            title = str(item.get("title", item.get("name", "")) or "").strip()
            if not title:
                continue

            tasks.append(
                GoalTask(
                    task_id=str(item.get("task_id", uuid.uuid4())),
                    title=title,
                    description=str(item.get("description", "") or ""),
                    order=int(item.get("order", index)),
                    status=str(item.get("status", "PENDING") or "PENDING"),
                    dependencies=list(item.get("dependencies", []) or []),
                    application=str(item.get("application", "") or ""),
                    action_type=str(item.get("action_type", "EXECUTE") or "EXECUTE"),
                    parameters=dict(item.get("parameters", {}) or {}),
                    goal_id=str(item.get("goal_id", goal_id) or goal_id),
                    metadata=dict(item.get("metadata", {}) or {}),
                )
            )

        tasks.sort(key=lambda item: item.order)
        return tasks


def plan_goal_tasks(goal, steps):
    return GoalTaskPlanner().plan(goal, steps)