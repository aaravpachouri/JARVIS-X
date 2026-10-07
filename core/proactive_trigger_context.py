from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ProactiveTrigger:

    trigger_id: str

    trigger_type: str

    title: str

    reason: str

    priority: int = 50

    confidence: float = 0.0

    created_at: float = field(
        default_factory=time.time
    )

    expires_at: Optional[float] = None

    goal_id: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    active: bool = True

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "trigger_id":
                self.trigger_id,

            "trigger_type":
                self.trigger_type,

            "title":
                self.title,

            "reason":
                self.reason,

            "priority":
                self.priority,

            "confidence":
                self.confidence,

            "created_at":
                self.created_at,

            "expires_at":
                self.expires_at,

            "goal_id":
                self.goal_id,

            "metadata":
                dict(
                    self.metadata
                ),

            "active":
                self.active,
        }


class ProactiveTriggerContext:

    """
    Runtime trigger registry for proactive intelligence.

    It converts available runtime signals into explicit trigger
    objects. It does not execute actions.

    Supported signal categories include:
        - goal progress
        - workflow state
        - deadlines
        - waiting/stalled states
        - user activity/context changes

    A later policy/ranking layer decides whether a trigger becomes
    an opportunity.
    """

    MAX_TRIGGERS = 200

    def __init__(self):

        self.triggers: dict[
            str,
            ProactiveTrigger
        ] = {}

    ############################################################
    # REGISTER
    ############################################################

    def register(
        self,
        trigger_type: str,
        title: str,
        reason: str,
        *,
        priority: int = 50,
        confidence: float = 0.0,
        goal_id: str = "",
        expires_at: Optional[float] = None,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> ProactiveTrigger:

        trigger = ProactiveTrigger(
            trigger_id=str(
                uuid.uuid4()
            ),

            trigger_type=str(
                trigger_type
                or
                "CUSTOM"
            ).strip().upper(),

            title=str(
                title
                or
                ""
            ).strip(),

            reason=str(
                reason
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

            confidence=max(
                0.0,
                min(
                    1.0,
                    float(
                        confidence
                        or
                        0.0
                    ),
                ),
            ),

            goal_id=str(
                goal_id
                or
                ""
            ).strip(),

            expires_at=expires_at,

            metadata=dict(
                metadata
                or
                {}
            ),
        )

        self.triggers[
            trigger.trigger_id
        ] = trigger

        self._trim()

        return trigger

    ############################################################
    # SIGNAL EXTRACTION
    ############################################################

    def update_from_context(
        self,
        *,
        goal_context: Optional[
            dict[str, Any]
        ] = None,
        workflow_context: Optional[
            dict[str, Any]
        ] = None,
        runtime_context: Optional[
            dict[str, Any]
        ] = None,
    ) -> list[ProactiveTrigger]:

        created = []

        goal_context = dict(
            goal_context
            or
            {}
        )

        workflow_context = dict(
            workflow_context
            or
            {}
        )

        runtime_context = dict(
            runtime_context
            or
            {}
        )

        ########################################################
        # GOAL SIGNALS
        ########################################################

        active_goal = goal_context.get(
            "active_goal"
        )

        if isinstance(
            active_goal,
            dict,
        ):

            status = str(
                active_goal.get(
                    "status",
                    ""
                )
                or
                ""
            ).upper()

            progress = float(
                active_goal.get(
                    "progress",
                    0.0
                )
                or
                0.0
            )

            goal_id = str(
                active_goal.get(
                    "goal_id",
                    ""
                )
                or
                ""
            )

            title = str(
                active_goal.get(
                    "title",
                    ""
                )
                or
                ""
            ).strip()

            due_at = active_goal.get(
                "due_at"
            )

            if (
                status == "ACTIVE"
                and
                progress < 1.0
            ):

                created.append(
                    self.register(
                        "GOAL_ACTIVE",
                        "Active goal needs continuation",
                        (
                            f"The goal '{title}' is still "
                            "in progress."
                        ),
                        priority=65,
                        confidence=0.80,
                        goal_id=goal_id,
                    )
                )

            if due_at:

                try:

                    remaining = (
                        float(
                            due_at
                        )
                        -
                        time.time()
                    )

                except Exception:

                    remaining = None

                if (
                    remaining is not None
                    and
                    0
                    <
                    remaining
                    <
                    86400.0
                    and
                    status == "ACTIVE"
                ):

                    created.append(
                        self.register(
                            "GOAL_DEADLINE",
                            "Goal deadline is approaching",
                            (
                                f"The goal '{title}' "
                                "has a deadline within 24 hours."
                            ),
                            priority=85,
                            confidence=0.88,
                            goal_id=goal_id,
                            metadata={
                                "seconds_remaining":
                                    remaining
                            },
                        )
                    )

        ########################################################
        # WORKFLOW SIGNALS
        ########################################################

        workflow = workflow_context.get(
            "workflow",
            workflow_context,
        )

        if isinstance(
            workflow,
            dict,
        ):

            workflow_status = str(
                workflow.get(
                    "status",
                    ""
                )
                or
                ""
            ).upper()

            if workflow_status in {
                "BLOCKED",
                "PAUSED",
                "WAITING",
            }:

                created.append(
                    self.register(
                        "WORKFLOW_BLOCKED",
                        "Workflow requires attention",
                        (
                            "A current computer workflow is "
                            f"{workflow_status.lower()}."
                        ),
                        priority=80,
                        confidence=0.84,
                    )
                )

        ########################################################
        # GENERIC RUNTIME SIGNAL
        ########################################################

        waiting = bool(
            runtime_context.get(
                "waiting_for_user",
                False,
            )
        )

        if waiting:

            created.append(
                self.register(
                    "WAITING_FOR_USER",
                    "JARVIS is waiting for user input",
                    "The current runtime is explicitly waiting for the user.",
                    priority=55,
                    confidence=0.92,
                )
            )

        return created

    ############################################################
    # ACTIVE / EXPIRE
    ############################################################

    def active(
        self,
        limit: int = 20,
    ) -> list[ProactiveTrigger]:

        now = time.time()

        result = []

        for trigger in self.triggers.values():

            if not trigger.active:
                continue

            if (
                trigger.expires_at is not None
                and
                now >= trigger.expires_at
            ):

                trigger.active = False

                continue

            result.append(
                trigger
            )

        result.sort(
            key=lambda item: (
                item.priority,
                item.confidence,
                item.created_at,
            ),
            reverse=True,
        )

        return result[
            :max(
                0,
                int(
                    limit
                ),
            )
        ]

    def deactivate(
        self,
        trigger_id: str,
    ) -> bool:

        trigger = self.triggers.get(
            str(
                trigger_id
                or
                ""
            ).strip()
        )

        if trigger is None:
            return False

        trigger.active = False

        return True

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "active":
                [
                    trigger.to_dict()
                    for trigger
                    in self.active(
                        100
                    )
                ]
        }

    ############################################################
    # INTERNAL
    ############################################################

    def _trim(
        self,
    ):

        if len(
            self.triggers
        ) <= self.MAX_TRIGGERS:
            return

        inactive = [
            trigger
            for trigger
            in self.triggers.values()
            if not trigger.active
        ]

        inactive.sort(
            key=lambda item:
                item.created_at
        )

        remove_count = (
            len(
                self.triggers
            )
            -
            self.MAX_TRIGGERS
        )

        for trigger in inactive[
            :remove_count
        ]:

            self.triggers.pop(
                trigger.trigger_id,
                None,
            )