from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


############################################################
# GOAL UNDERSTANDING RESULT
############################################################

@dataclass
class ComputerGoal:

    original_request: str = ""

    goal: str = ""

    success_criteria: list[str] = field(
        default_factory=list
    )

    constraints: list[str] = field(
        default_factory=list
    )

    requested_result: str = ""

    context: dict[str, Any] = field(
        default_factory=dict
    )

    ########################################################
    # VALIDATION
    ########################################################

    def validate(self) -> None:

        self.original_request = str(
            self.original_request or ""
        ).strip()

        self.goal = str(
            self.goal or ""
        ).strip()

        self.success_criteria = [
            str(item).strip()
            for item in self.success_criteria
            if str(item).strip()
        ]

        self.constraints = [
            str(item).strip()
            for item in self.constraints
            if str(item).strip()
        ]

        self.requested_result = str(
            self.requested_result or ""
        ).strip()

        if not self.original_request:
            raise ValueError(
                "Original computer request cannot be empty."
            )

        if not self.goal:
            raise ValueError(
                "Computer goal cannot be empty."
            )


############################################################
# GOAL UNDERSTANDING
############################################################

class ComputerGoalUnderstanding:

    """
    Lightweight semantic layer for computer tasks.

    This layer does NOT execute computer actions.

    It prepares a structured objective for the ComputerUseAgent.
    """

    DEFAULT_CONSTRAINTS = [
        "Do not modify unrelated data.",
        "Do not delete data unless explicitly requested.",
        "Verify important results before reporting completion.",
    ]

    def understand(
        self,
        request: str,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> ComputerGoal:

        request = str(
            request or ""
        ).strip()

        if not request:
            raise ValueError(
                "Computer request cannot be empty."
            )

        context = dict(
            context or {}
        )

        ####################################################
        # Keep the first implementation deterministic.
        # The next intelligence layer can replace this with
        # local-model goal extraction without changing the
        # contract.
        ####################################################

        goal = request

        success_criteria = [
            "The requested computer objective is completed.",
            "The final computer state matches the user's request.",
            "The result is verified before reporting completion.",
        ]

        constraints = list(
            self.DEFAULT_CONSTRAINTS
        )

        requested_result = (
            "Report the final result clearly to the user."
        )

        understood = ComputerGoal(
            original_request=request,
            goal=goal,
            success_criteria=success_criteria,
            constraints=constraints,
            requested_result=requested_result,
            context=context,
        )

        understood.validate()

        return understood

    ########################################################
    # CONTRACT PAYLOAD
    ########################################################

    def to_contract_data(
        self,
        goal: ComputerGoal,
    ) -> dict[str, Any]:

        goal.validate()

        return {
            "goal": goal.goal,
            "success_criteria": list(
                goal.success_criteria
            ),
            "constraints": list(
                goal.constraints
            ),
            "context": dict(
                goal.context
            ),
            "requested_result": (
                goal.requested_result
            ),
        }

    ########################################################
    # MODEL PROMPT
    ########################################################

    def build_reasoning_context(
        self,
        goal: ComputerGoal,
    ) -> str:

        goal.validate()

        return f"""
COMPUTER TASK OBJECTIVE

Original request:
{goal.original_request}

Primary goal:
{goal.goal}

Success criteria:
{self._format_list(goal.success_criteria)}

Constraints:
{self._format_list(goal.constraints)}

Requested final result:
{goal.requested_result}

Additional context:
{goal.context}
""".strip()

    @staticmethod
    def _format_list(
        values: list[str],
    ) -> str:

        if not values:
            return "- None"

        return "\n".join(
            f"- {item}"
            for item in values
        )