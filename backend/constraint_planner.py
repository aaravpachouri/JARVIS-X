from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.intent_decomposer import (
    DecomposedIntent,
    SubGoal,
)


############################################################
# CONSTRAINT
############################################################

@dataclass
class Constraint:

    name: str = ""

    description: str = ""

    constraint_type: str = "general"

    priority: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# CONSTRAINT RESULT
############################################################

@dataclass
class ConstraintCheck:

    allowed: bool = True

    violations: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# CONSTRAINT PLANNER
############################################################

class ConstraintPlanner:

    """
    Maintains and checks constraints for complex reasoning.

    This layer does not execute actions.

    It determines whether a proposed operation is compatible
    with the constraints attached to the overall objective.
    """

    def __init__(self):

        self.constraints: list[
            Constraint
        ] = []

    ########################################################
    # REGISTER
    ########################################################

    def add(
        self,
        description: str,
        constraint_type: str = "general",
        priority: int = 0,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> Constraint:

        constraint = Constraint(
            name=(
                f"constraint_"
                f"{len(self.constraints) + 1}"
            ),
            description=str(
                description or ""
            ).strip(),
            constraint_type=str(
                constraint_type or "general"
            ).strip(),
            priority=int(
                priority
            ),
            metadata=dict(
                metadata or {}
            ),
        )

        if not constraint.description:

            raise ValueError(
                "Constraint description cannot be empty."
            )

        self.constraints.append(
            constraint
        )

        return constraint

    ########################################################
    # LOAD FROM INTENT
    ########################################################

    def load_intent(
        self,
        intent: DecomposedIntent,
    ) -> list[Constraint]:

        self.constraints.clear()

        for index, description in enumerate(
            intent.global_constraints,
            start=1,
        ):

            self.add(
                description=description,
                priority=index,
            )

        for subgoal in (
            intent.subgoals
        ):

            for description in (
                subgoal.constraints
            ):

                self.add(
                    description=description,
                    priority=(
                        subgoal.priority
                    ),
                    metadata={
                        "subgoal_id":
                            subgoal.subgoal_id,
                    },
                )

        return list(
            self.constraints
        )

    ########################################################
    # CHECK
    ########################################################

    def check(
        self,
        action: Any,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> ConstraintCheck:

        context = dict(
            context or {}
        )

        description = self._describe(
            action
        ).lower()

        violations = []
        warnings = []

        for constraint in self.constraints:

            rule = (
                constraint.description.lower()
            )

            ################################################
            # Destructive operations
            ################################################

            if (
                any(
                    marker in rule
                    for marker in (
                        "do not delete",
                        "never delete",
                        "don't delete",
                    )
                )
                and
                "delete" in description
            ):

                violations.append(
                    constraint.description
                )

                continue

            ################################################
            # Modification
            ################################################

            if (
                (
                    "do not modify"
                    in
                    rule
                )
                and
                (
                    "modify"
                    in
                    description
                    or
                    "edit"
                    in
                    description
                )
            ):

                violations.append(
                    constraint.description
                )

                continue

            ################################################
            # General warning conditions
            ################################################

            if (
                "verify"
                in
                rule
                and
                (
                    "verify"
                    not in
                    description
                )
            ):

                warnings.append(
                    constraint.description
                )

        return ConstraintCheck(
            allowed=not bool(
                violations
            ),
            violations=violations,
            warnings=warnings,
            metadata={
                "action":
                    description,
                "constraint_count":
                    len(
                        self.constraints
                    ),
            },
        )

    ########################################################
    # ALLOWED?
    ########################################################

    def allowed(
        self,
        action: Any,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> bool:

        return self.check(
            action,
            context,
        ).allowed

    ########################################################
    # CONTEXT
    ########################################################

    def reasoning_context(
        self,
    ) -> dict[str, Any]:

        return {
            "constraints": [
                {
                    "name":
                        item.name,

                    "description":
                        item.description,

                    "type":
                        item.constraint_type,

                    "priority":
                        item.priority,

                    "metadata":
                        dict(
                            item.metadata
                        ),
                }

                for item
                in self.constraints
            ]
        }

    ########################################################
    # DESCRIPTION
    ########################################################

    @staticmethod
    def _describe(
        action: Any,
    ) -> str:

        if isinstance(
            action,
            str,
        ):

            return action

        if isinstance(
            action,
            dict,
        ):

            return " ".join(
                str(value)
                for value
                in action.values()
            )

        return str(
            action
        )