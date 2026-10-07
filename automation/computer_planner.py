from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


############################################################
# COMPUTER PLAN
############################################################

@dataclass
class ComputerPlan:

    goal: str = ""

    stages: list[str] = field(
        default_factory=list
    )

    current_stage: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    ########################################################
    # VALIDATION
    ########################################################

    def validate(self):

        self.goal = str(
            self.goal or ""
        ).strip()

        self.stages = [
            str(stage).strip()
            for stage in self.stages
            if str(stage).strip()
        ]

        if not self.goal:

            raise ValueError(
                "Computer plan goal cannot be empty."
            )

        if not self.stages:

            raise ValueError(
                "Computer plan must contain at least one stage."
            )

        self.current_stage = max(
            0,
            min(
                self.current_stage,
                len(self.stages) - 1
            )
        )

    ########################################################
    # CURRENT STAGE
    ########################################################

    def current(self) -> str:

        self.validate()

        return self.stages[
            self.current_stage
        ]

    ########################################################
    # ADVANCE
    ########################################################

    def advance(self) -> bool:

        self.validate()

        if (
            self.current_stage
            >=
            len(self.stages) - 1
        ):

            return False

        self.current_stage += 1

        return True

    ########################################################
    # REMAINING
    ########################################################

    def remaining(self) -> list[str]:

        self.validate()

        return self.stages[
            self.current_stage:
        ]

    ########################################################
    # COMPLETE
    ########################################################

    def is_complete(self) -> bool:

        self.validate()

        return (
            self.current_stage
            ==
            len(self.stages) - 1
        )


############################################################
# MULTI-STAGE PLANNER
############################################################

class ComputerPlanner:

    """
    Universal multi-stage planning layer.

    It creates a high-level sequence of objectives.

    It does NOT choose individual mouse/keyboard actions.
    The existing ComputerUseAgent remains responsible for that.
    """

    def create_plan(
        self,
        goal: str,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> ComputerPlan:

        goal = str(
            goal or ""
        ).strip()

        if not goal:

            raise ValueError(
                "Computer goal cannot be empty."
            )

        context = dict(
            context or {}
        )

        ####################################################
        # Initial generic stage.
        #
        # Complex semantic decomposition will be introduced
        # by the next intelligence layer without changing the
        # ComputerPlan contract.
        ####################################################

        stages = [
            "Understand and inspect the current computer state.",
            "Execute the actions required to advance the user's goal.",
            "Verify the requested final outcome.",
        ]

        plan = ComputerPlan(
            goal=goal,
            stages=stages,
            metadata={
                "context": context,
                "planner": "ComputerPlanner",
            },
        )

        plan.validate()

        return plan

    ########################################################
    # CONTEXT FOR COMPUTER AGENT
    ########################################################

    def build_context(
        self,
        plan: ComputerPlan,
    ) -> dict[str, Any]:

        plan.validate()

        return {
            "goal": plan.goal,
            "current_stage":
                plan.current(),
            "remaining_stages":
                plan.remaining(),
            "stage_index":
                plan.current_stage,
            "stage_count":
                len(plan.stages),
            "metadata":
                dict(plan.metadata),
        }