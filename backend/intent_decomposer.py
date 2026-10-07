from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4


############################################################
# SUBGOAL
############################################################

@dataclass
class SubGoal:

    subgoal_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    description: str = ""

    goal_type: str = ""

    priority: int = 0

    dependencies: list[str] = field(
        default_factory=list
    )

    constraints: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:

        self.description = str(
            self.description or ""
        ).strip()

        self.goal_type = str(
            self.goal_type or ""
        ).strip()

        if not self.description:

            raise ValueError(
                "Subgoal description cannot be empty."
            )


############################################################
# DECOMPOSED INTENT
############################################################

@dataclass
class DecomposedIntent:

    request: str = ""

    primary_goal: str = ""

    subgoals: list[SubGoal] = field(
        default_factory=list
    )

    global_constraints: list[str] = field(
        default_factory=list
    )

    requested_result: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:

        self.request = str(
            self.request or ""
        ).strip()

        self.primary_goal = str(
            self.primary_goal or ""
        ).strip()

        if not self.request:

            raise ValueError(
                "Intent request cannot be empty."
            )

        if not self.primary_goal:

            raise ValueError(
                "Primary goal cannot be empty."
            )

        for subgoal in self.subgoals:

            subgoal.validate()


############################################################
# INTENT DECOMPOSER
############################################################

class IntentDecomposer:

    """
    Converts one user request into a structured goal and
    potential subgoals.

    This layer does NOT execute anything.

    It establishes the representation that later reasoning
    layers will use for planning and decision-making.
    """

    def decompose(
        self,
        request: str,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> DecomposedIntent:

        request = str(
            request or ""
        ).strip()

        if not request:

            raise ValueError(
                "Request cannot be empty."
            )

        context = dict(
            context or {}
        )

        ####################################################
        # Phase 5.1 foundation:
        #
        # Keep the original request intact and create one
        # primary goal. More advanced semantic splitting will
        # be introduced in the next reasoning stages.
        ####################################################

        intent = DecomposedIntent(
            request=request,

            primary_goal=request,

            subgoals=[],

            global_constraints=[],

            requested_result="",

            metadata={
                "context": context,
                "decomposer": "IntentDecomposer",
            },
        )

        intent.validate()

        return intent

    ########################################################
    # ADD SUBGOAL
    ########################################################

    def add_subgoal(
        self,
        intent: DecomposedIntent,
        description: str,
        goal_type: str = "",
        priority: int = 0,
        dependencies: Optional[
            list[str]
        ] = None,
        constraints: Optional[
            list[str]
        ] = None,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> SubGoal:

        subgoal = SubGoal(
            description=description,

            goal_type=goal_type,

            priority=int(
                priority
            ),

            dependencies=list(
                dependencies or []
            ),

            constraints=list(
                constraints or []
            ),

            metadata=dict(
                metadata or {}
            ),
        )

        subgoal.validate()

        intent.subgoals.append(
            subgoal
        )

        return subgoal

    ########################################################
    # DEPENDENCY CHECK
    ########################################################

    @staticmethod
    def validate_dependencies(
        intent: DecomposedIntent,
    ) -> None:

        known_ids = {
            subgoal.subgoal_id
            for subgoal in intent.subgoals
        }

        for subgoal in intent.subgoals:

            for dependency in (
                subgoal.dependencies
            ):

                if dependency not in known_ids:

                    raise ValueError(
                        "Unknown subgoal dependency: "
                        f"{dependency}"
                    )

                if (
                    dependency
                    ==
                    subgoal.subgoal_id
                ):

                    raise ValueError(
                        "A subgoal cannot depend "
                        "on itself."
                    )

    ########################################################
    # REASONING CONTEXT
    ########################################################

    def build_reasoning_context(
        self,
        intent: DecomposedIntent,
    ) -> dict[str, Any]:

        intent.validate()

        self.validate_dependencies(
            intent
        )

        return {
            "request":
                intent.request,

            "primary_goal":
                intent.primary_goal,

            "subgoals": [
                {
                    "id":
                        subgoal.subgoal_id,

                    "description":
                        subgoal.description,

                    "goal_type":
                        subgoal.goal_type,

                    "priority":
                        subgoal.priority,

                    "dependencies":
                        list(
                            subgoal.dependencies
                        ),

                    "constraints":
                        list(
                            subgoal.constraints
                        ),

                    "metadata":
                        dict(
                            subgoal.metadata
                        ),
                }

                for subgoal
                in intent.subgoals
            ],

            "global_constraints":
                list(
                    intent.global_constraints
                ),

            "requested_result":
                intent.requested_result,

            "metadata":
                dict(
                    intent.metadata
                ),
        }