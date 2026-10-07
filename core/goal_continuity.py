from __future__ import annotations

import time
from typing import Any, Optional


class GoalContinuityManager:

    """
    Maintains goal continuity across conversational turns and
    application/task transitions.

    It does not replace ConversationContext or persistent goal
    storage. It bridges them so a new command can be interpreted
    relative to an existing active goal.
    """

    def __init__(
        self,
        goal_runtime,
        conversation_context=None,
    ):

        self.goals = goal_runtime

        self.conversation = (
            conversation_context
        )

        self.last_goal_id = ""

        self.last_update_at = time.time()

    ############################################################
    # RESOLVE
    ############################################################

    def resolve_command(
        self,
        command: str,
    ) -> dict[str, Any]:

        detection = self.goals.detect(
            command
        )

        active = (
            self.goals.context.active_goal()
        )

        ########################################################
        # Explicit new goal
        ########################################################

        if (
            detection.get(
                "goal_detected",
                False,
            )
            and
            not detection.get(
                "continuation",
                False,
            )
        ):

            established = (
                self.goals.establish_goal(
                    command
                )
            )

            goal = (
                self.goals.context.active_goal()
            )

            if goal is not None:

                self.last_goal_id = (
                    goal.goal_id
                )

            self.last_update_at = time.time()

            return {
                "type":
                    "NEW_GOAL",

                "goal":
                    (
                        goal.to_dict()
                        if goal is not None
                        else
                        None
                    ),

                "detection":
                    detection,

                "established":
                    established,
            }

        ########################################################
        # Continuation
        ########################################################

        if (
            active is not None
            and
            detection.get(
                "continuation",
                False,
            )
        ):

            self.last_goal_id = (
                active.goal_id
            )

            self.last_update_at = time.time()

            return {
                "type":
                    "GOAL_CONTINUATION",

                "goal":
                    active.to_dict(),

                "detection":
                    detection,
            }

        ########################################################
        # Non-goal/chat command while a goal is active.
        #
        # Keep the goal available as context, but do not force
        # unrelated chat into the goal.
        ########################################################

        if active is not None:

            return {
                "type":
                    "GOAL_CONTEXT_AVAILABLE",

                "goal":
                    active.to_dict(),

                "detection":
                    detection,
            }

        return {
            "type":
                "NO_ACTIVE_GOAL",

            "goal":
                None,

            "detection":
                detection,
        }

    ############################################################
    # GOAL SWITCHING
    ############################################################

    def switch_goal(
        self,
        goal_id: str,
    ) -> bool:

        changed = (
            self.goals.context.set_active(
                goal_id
            )
        )

        if changed:

            self.last_goal_id = (
                str(
                    goal_id
                )
            )

            self.last_update_at = time.time()

        return changed

    ############################################################
    # COMPLETE
    ############################################################

    def complete_active_goal(
        self,
    ) -> bool:

        goal = (
            self.goals.context.active_goal()
        )

        if goal is None:

            return False

        completed = (
            self.goals.context.complete_goal(
                goal.goal_id
            )
        )

        if completed:

            self.goals.store.save(
                goal
            )

            self.last_goal_id = ""

            self.last_update_at = time.time()

        return completed

    ############################################################
    # CONTEXT
    ############################################################

    def compact_context(
        self,
    ) -> dict[str, Any]:

        active = (
            self.goals.context.active_goal()
        )

        return {
            "active_goal":
                (
                    active.to_dict()
                    if active is not None
                    else
                    None
                ),

            "goal_id":
                (
                    active.goal_id
                    if active is not None
                    else
                    ""
                ),

            "goal_available":
                active is not None,

            "last_goal_id":
                self.last_goal_id,

            "updated_at":
                self.last_update_at,
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            **self.compact_context(),

            "runtime":
                self.goals.snapshot(),
        }