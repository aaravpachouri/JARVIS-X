from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Goal:

    goal_id: str

    title: str

    description: str = ""

    status: str = "ACTIVE"

    priority: int = 50

    created_at: float = field(
        default_factory=time.time
    )

    updated_at: float = field(
        default_factory=time.time
    )

    due_at: Optional[float] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    progress: float = 0.0

    def set_progress(
        self,
        progress: float,
    ):

        self.progress = max(
            0.0,
            min(
                1.0,
                float(
                    progress
                    or
                    0.0
                ),
            ),
        )

        if self.progress >= 1.0:

            self.progress = 1.0

            self.status = "COMPLETED"

        self.updated_at = time.time()

    def complete(
        self,
    ):

        self.progress = 1.0

        self.status = "COMPLETED"

        self.updated_at = time.time()

    def pause(
        self,
    ):

        self.status = "PAUSED"

        self.updated_at = time.time()

    def cancel(
        self,
    ):

        self.status = "CANCELLED"

        self.updated_at = time.time()

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "goal_id":
                self.goal_id,

            "title":
                self.title,

            "description":
                self.description,

            "status":
                self.status,

            "priority":
                self.priority,

            "created_at":
                self.created_at,

            "updated_at":
                self.updated_at,

            "due_at":
                self.due_at,

            "metadata":
                dict(
                    self.metadata
                ),

            "progress":
                self.progress,
        }


class GoalContext:

    """
    Phase 8.9 foundation: explicit goal/intent context.

    This is intentionally separate from:
        - ConversationContext: what is being discussed
        - MemoryRuntimeCoordinator: what should be remembered
        - Computer workflows: how computer actions execute

    GoalContext answers:
        "What is the user currently trying to accomplish?"

    It supports:
        - active goals
        - priorities
        - progress
        - due times
        - metadata
        - goal history
    """

    MAX_GOALS = 100

    def __init__(self):

        self.goals: dict[
            str,
            Goal
        ] = {}

        self.active_goal_id: str = ""

        self.history: list[
            dict[str, Any]
        ] = []

    ############################################################
    # CREATE
    ############################################################

    def create_goal(
        self,
        title: str,
        *,
        description: str = "",
        priority: int = 50,
        due_at: Optional[float] = None,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> Goal:

        title = str(
            title
            or
            ""
        ).strip()

        if not title:

            raise ValueError(
                "Goal title cannot be empty."
            )

        goal = Goal(
            goal_id=str(
                uuid.uuid4()
            ),

            title=title,

            description=str(
                description
                or
                ""
            ).strip(),

            priority=max(
                0,
                min(
                    100,
                    int(
                        priority
                    ),
                ),
            ),

            due_at=due_at,

            metadata=dict(
                metadata
                or
                {}
            ),
        )

        self.goals[
            goal.goal_id
        ] = goal

        self.active_goal_id = (
            goal.goal_id
        )

        self._record(
            "goal_created",
            goal.to_dict(),
        )

        self._trim()

        return goal

    ############################################################
    # ACTIVE GOAL
    ############################################################

    def active_goal(
        self,
    ) -> Optional[Goal]:

        if not self.active_goal_id:

            return None

        return self.goals.get(
            self.active_goal_id
        )

    def set_active(
        self,
        goal_id: str,
    ) -> bool:

        goal = self.goals.get(
            str(
                goal_id
                or
                ""
            ).strip()
        )

        if goal is None:

            return False

        if goal.status != "ACTIVE":

            return False

        self.active_goal_id = (
            goal.goal_id
        )

        self._record(
            "goal_activated",
            {
                "goal_id":
                    goal.goal_id
            },
        )

        return True

    ############################################################
    # PROGRESS
    ############################################################

    def update_progress(
        self,
        goal_id: str,
        progress: float,
    ) -> bool:

        goal = self.goals.get(
            str(
                goal_id
                or
                ""
            ).strip()
        )

        if goal is None:

            return False

        previous = (
            goal.progress
        )

        goal.set_progress(
            progress
        )

        self._record(
            "goal_progress",
            {
                "goal_id":
                    goal.goal_id,

                "previous":
                    previous,

                "current":
                    goal.progress,
            },
        )

        return True

    def complete_goal(
        self,
        goal_id: str,
    ) -> bool:

        goal = self.goals.get(
            str(
                goal_id
                or
                ""
            ).strip()
        )

        if goal is None:

            return False

        goal.complete()

        if (
            self.active_goal_id
            ==
            goal.goal_id
        ):

            self.active_goal_id = ""

        self._record(
            "goal_completed",
            {
                "goal_id":
                    goal.goal_id
            },
        )

        return True

    ############################################################
    # READ
    ############################################################

    def get(
        self,
        goal_id: str,
    ) -> Optional[Goal]:

        return self.goals.get(
            str(
                goal_id
                or
                ""
            ).strip()
        )

    def active(
        self,
    ) -> list[Goal]:

        goals = [
            goal
            for goal
            in self.goals.values()
            if goal.status == "ACTIVE"
        ]

        goals.sort(
            key=lambda goal: (
                goal.priority,
                goal.updated_at,
            ),
            reverse=True,
        )

        return goals

    ############################################################
    # CONTEXT
    ############################################################

    def compact_context(
        self,
        limit: int = 10,
    ) -> dict[str, Any]:

        goals = self.active()

        return {
            "active_goal":
                (
                    self.active_goal().to_dict()
                    if self.active_goal() is not None
                    else
                    None
                ),

            "goals":
                [
                    goal.to_dict()
                    for goal
                    in goals[
                        :max(
                            0,
                            int(
                                limit
                            ),
                        )
                    ]
                ],
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "active_goal_id":
                self.active_goal_id,

            "goals":
                [
                    goal.to_dict()
                    for goal
                    in self.goals.values()
                ],

            "history":
                list(
                    self.history[
                        -30:
                    ]
                ),
        }

    ############################################################
    # INTERNAL
    ############################################################

    def _record(
        self,
        event: str,
        data: dict[str, Any],
    ):

        self.history.append(
            {
                "timestamp":
                    time.time(),

                "event":
                    str(
                        event
                    ),

                "data":
                    dict(
                        data
                    ),
            }
        )

        if len(
            self.history
        ) > 100:

            del self.history[
                :-
                100
            ]

    def _trim(
        self,
    ):

        if len(
            self.goals
        ) <= self.MAX_GOALS:

            return

        completed = [
            goal
            for goal
            in self.goals.values()
            if goal.status
            in {
                "COMPLETED",
                "CANCELLED",
            }
        ]

        completed.sort(
            key=lambda goal:
                goal.updated_at
        )

        remove_count = (
            len(
                self.goals
            )
            -
            self.MAX_GOALS
        )

        for goal in completed[
            :remove_count
        ]:

            self.goals.pop(
                goal.goal_id,
                None,
            )


def create_goal_context() -> GoalContext:

    return GoalContext()