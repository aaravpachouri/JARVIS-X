from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.goal_decomposer import GoalDecomposer
from backend.intent_decomposer import DecomposedIntent
from automation.computer_planner import (
    ComputerPlan,
    ComputerPlanner,
)


############################################################
# RUNTIME PLAN
############################################################

@dataclass
class RuntimePlan:

    request: str = ""

    intent: Optional[
        DecomposedIntent
    ] = None

    computer_plan: Optional[
        ComputerPlan
    ] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# RUNTIME PLANNER
############################################################

class RuntimePlanner:

    """
    Connects the existing reasoning components to the runtime.

    It plans.

    It does NOT execute tasks.

    Execution remains the responsibility of TaskOrchestrator.
    """

    def __init__(
        self,
        brain,
    ):

        self.brain = brain

        self.goal_decomposer = (
            GoalDecomposer(
                brain
            )
        )

        self.computer_planner = (
            ComputerPlanner()
        )

    ########################################################
    # PLAN
    ########################################################

    def plan(
        self,
        request: str,
        mode: str = "COMPUTER",
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> RuntimePlan:

        request = str(
            request or ""
        ).strip()

        if not request:

            raise ValueError(
                "Runtime planning request cannot be empty."
            )

        mode = str(
            mode or "COMPUTER"
        ).strip().upper()

        context = dict(
            context or {}
        )

        ####################################################
        # Semantic intent decomposition
        ####################################################

        intent = (
            self.goal_decomposer.decompose(
                request,
                context=context,
            )
        )

        ####################################################
        # Computer-specific planning
        ####################################################

        computer_plan = None

        if mode == "COMPUTER":

            computer_plan = (
                self.computer_planner.create_plan(
                    intent.primary_goal,
                    context=context,
                )
            )

        return RuntimePlan(
            request=request,
            intent=intent,
            computer_plan=computer_plan,
            metadata={
                "mode": mode,
                "planner": "RuntimePlanner",
            },
        )

    ########################################################
    # ORCHESTRATOR STEP DATA
    ########################################################

    def task_steps(
        self,
        plan: RuntimePlan,
    ) -> list[dict[str, Any]]:

        if plan.intent is None:

            return []

        steps = []

        for subgoal in (
            plan.intent.subgoals
        ):

            dependencies = list(
                subgoal.dependencies
            )

            executor = (
                "COMPUTER_AGENT"
                if str(
                    subgoal.goal_type
                    or ""
                ).lower().strip()
                ==
                "computer"
                else ""
            )

            steps.append(
                {
                    "description":
                        subgoal.description,

                    "executor":
                        executor,

                    "dependencies":
                        dependencies,

                    "metadata": {
                        "subgoal_id":
                            subgoal.subgoal_id,

                        "goal_type":
                            subgoal.goal_type,

                        "priority":
                            subgoal.priority,

                        "constraints":
                            list(
                                subgoal.constraints
                            ),
                    },
                }
            )

        ####################################################
        # If the local model produced no subgoals, preserve
        # the original objective as one step.
        ####################################################

        if not steps:

            steps.append(
                {
                    "description":
                        plan.intent.primary_goal,

                    "executor":
                        "COMPUTER_AGENT",

                    "dependencies": [],

                    "metadata": {
                        "fallback":
                            True,
                    },
                }
            )

        return steps

    ########################################################
    # SUMMARY
    ########################################################

    def summary(
        self,
        plan: RuntimePlan,
    ) -> dict[str, Any]:

        return {
            "request":
                plan.request,

            "primary_goal":
                (
                    plan.intent.primary_goal
                    if plan.intent
                    else ""
                ),

            "subgoals":
                len(
                    plan.intent.subgoals
                )
                if plan.intent
                else 0,

            "computer_stages":
                (
                    list(
                        plan.computer_plan.stages
                    )
                    if plan.computer_plan
                    else []
                ),

            "metadata":
                dict(
                    plan.metadata
                ),
        }