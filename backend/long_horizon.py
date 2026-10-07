from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.intent_decomposer import (
    DecomposedIntent,
    SubGoal,
)


############################################################
# LONG-HORIZON STATE
############################################################

@dataclass
class LongHorizonState:

    primary_goal: str = ""

    completed_subgoals: set[str] = field(
        default_factory=set
    )

    active_subgoal: Optional[str] = None

    failed_subgoals: set[str] = field(
        default_factory=set
    )

    important_facts: dict[str, Any] = field(
        default_factory=dict
    )

    remaining_objective: str = ""

    progress: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# LONG-HORIZON ENGINE
############################################################

class LongHorizonReasoner:

    """
    Maintains a bounded representation of long-running goals.

    It does not execute tasks.

    It tracks:
        - what has been completed
        - what is currently active
        - what failed
        - useful facts discovered during execution
        - how much of the overall objective remains
    """

    ########################################################
    # START
    ########################################################

    def start(
        self,
        intent: DecomposedIntent,
    ) -> LongHorizonState:

        intent.validate()

        state = LongHorizonState(
            primary_goal=intent.primary_goal,

            remaining_objective=(
                intent.primary_goal
            ),
        )

        self._update_progress(
            state,
            intent,
        )

        return state

    ########################################################
    # ACTIVATE SUBGOAL
    ########################################################

    def activate(
        self,
        state: LongHorizonState,
        subgoal: SubGoal,
    ) -> None:

        if (
            subgoal.subgoal_id
            in
            state.completed_subgoals
        ):

            return

        state.active_subgoal = (
            subgoal.subgoal_id
        )

    ########################################################
    # COMPLETE SUBGOAL
    ########################################################

    def complete(
        self,
        state: LongHorizonState,
        intent: DecomposedIntent,
        subgoal: SubGoal,
        result: Any = None,
    ) -> None:

        state.completed_subgoals.add(
            subgoal.subgoal_id
        )

        state.failed_subgoals.discard(
            subgoal.subgoal_id
        )

        if (
            state.active_subgoal
            ==
            subgoal.subgoal_id
        ):

            state.active_subgoal = None

        ####################################################
        # Preserve useful discovered information.
        ####################################################

        if result is not None:

            state.important_facts[
                subgoal.subgoal_id
            ] = result

        self._update_progress(
            state,
            intent,
        )

    ########################################################
    # FAIL SUBGOAL
    ########################################################

    def fail(
        self,
        state: LongHorizonState,
        intent: DecomposedIntent,
        subgoal: SubGoal,
        reason: str = "",
    ) -> None:

        state.failed_subgoals.add(
            subgoal.subgoal_id
        )

        if (
            state.active_subgoal
            ==
            subgoal.subgoal_id
        ):

            state.active_subgoal = None

        state.important_facts[
            f"failure:{subgoal.subgoal_id}"
        ] = str(
            reason or ""
        )

        self._update_progress(
            state,
            intent,
        )

    ########################################################
    # REMAINING OBJECTIVE
    ########################################################

    def remaining(
        self,
        state: LongHorizonState,
        intent: DecomposedIntent,
    ) -> list[SubGoal]:

        return [
            subgoal
            for subgoal
            in intent.subgoals
            if (
                subgoal.subgoal_id
                not in
                state.completed_subgoals
            )
        ]

    ########################################################
    # PROGRESS
    ########################################################

    def _update_progress(
        self,
        state: LongHorizonState,
        intent: DecomposedIntent,
    ) -> None:

        total = len(
            intent.subgoals
        )

        if total == 0:

            state.progress = 1.0

            state.remaining_objective = ""

            return

        completed = len(
            state.completed_subgoals
        )

        state.progress = (
            completed
            /
            total
        )

        remaining = self.remaining(
            state,
            intent,
        )

        if not remaining:

            state.remaining_objective = ""

            return

        state.remaining_objective = (
            "; ".join(
                subgoal.description
                for subgoal in remaining
            )
        )

    ########################################################
    # COMPLETION
    ########################################################

    def is_complete(
        self,
        state: LongHorizonState,
        intent: DecomposedIntent,
    ) -> bool:

        return (
            len(
                state.completed_subgoals
            )
            ==
            len(
                intent.subgoals
            )
            and
            len(
                intent.subgoals
            )
            > 0
        )

    ########################################################
    # REASONING CONTEXT
    ########################################################

    def build_context(
        self,
        state: LongHorizonState,
        intent: DecomposedIntent,
    ) -> dict[str, Any]:

        remaining = self.remaining(
            state,
            intent,
        )

        return {
            "primary_goal":
                state.primary_goal,

            "progress":
                round(
                    state.progress,
                    3,
                ),

            "active_subgoal":
                state.active_subgoal,

            "completed_subgoals":
                list(
                    state.completed_subgoals
                ),

            "failed_subgoals":
                list(
                    state.failed_subgoals
                ),

            "remaining_subgoals": [
                {
                    "id":
                        subgoal.subgoal_id,

                    "description":
                        subgoal.description,

                    "goal_type":
                        subgoal.goal_type,

                    "dependencies":
                        list(
                            subgoal.dependencies
                        ),
                }

                for subgoal
                in remaining
            ],

            "remaining_objective":
                state.remaining_objective,

            "important_facts":
                dict(
                    state.important_facts
                ),

            "metadata":
                dict(
                    state.metadata
                ),
        }