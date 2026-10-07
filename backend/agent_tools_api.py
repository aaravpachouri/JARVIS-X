from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentTask:
    goal: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentTaskAPI:
    """Small stable interface between UI/voice layers and the autonomous agent."""

    def __init__(self, agent):
        self.agent = agent

    def submit(self, goal: str, **metadata):
        task = AgentTask(goal=str(goal).strip(), metadata=metadata)
        if not task.goal:
            raise ValueError("Agent task cannot be empty")
        return self.agent.run(task.goal)

    def is_complex(self, goal: str) -> bool:
        return self.agent.shouldHandle(goal)