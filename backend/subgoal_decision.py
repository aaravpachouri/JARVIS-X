from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.intent_decomposer import (
    DecomposedIntent,
    SubGoal,
)


############################################################
# DECISION RESULT
############################################################

@dataclass
class SubgoalDecision:

    selected: Optional[SubGoal] = None

    alternatives: list[SubGoal] = field(
        default_factory=list
    )

    reason: str = ""

    confidence: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# DECISION ENGINE
############################################################

class SubgoalDecisionEngine:

    """
    Chooses which ready subgoal should be handled next.

    This component does NOT execute the subgoal.

    It only makes the next-objective decision.
    """

    def decide(
        self,
        intent: DecomposedIntent,
        ready: list[SubGoal],
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> SubgoalDecision:

        context = dict(
            context or {}
        )

        if not ready:

            return SubgoalDecision(
                reason=(
                    "No executable subgoals are currently ready."
                )
            )

        ####################################################
        # Score every ready subgoal.
        ####################################################

        scored = []

        for subgoal in ready:

            score = self._score(
                subgoal,
                context,
            )

            scored.append(
                (
                    score,
                    subgoal,
                )
            )

        ####################################################
        # Highest score first.
        ####################################################

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        selected_score, selected = scored[0]

        alternatives = [
            subgoal
            for _, subgoal
            in scored[1:]
        ]

        confidence = self._confidence(
            selected_score,
            len(
                scored
            ),
        )

        return SubgoalDecision(
            selected=selected,
            alternatives=alternatives,
            reason=(
                "Selected the highest-scoring ready "
                "subgoal."
            ),
            confidence=confidence,
            metadata={
                "scores": {
                    subgoal.subgoal_id:
                        score

                    for score, subgoal
                    in scored
                }
            },
        )

    ########################################################
    # SCORING
    ########################################################

    def _score(
        self,
        subgoal: SubGoal,
        context: dict[str, Any],
    ) -> float:

        score = 0.0

        ####################################################
        # Priority
        ####################################################

        score += (
            float(
                subgoal.priority
            )
            * 10.0
        )

        ####################################################
        # Verification steps should generally happen near
        # completion, but still remain available when needed.
        ####################################################

        goal_type = str(
            subgoal.goal_type
            or
            ""
        ).lower().strip()

        if goal_type == "verification":

            score += 2.0

        ####################################################
        # Context may explicitly identify an urgent objective.
        ####################################################

        preferred_ids = context.get(
            "preferred_subgoals",
            [],
        )

        if (
            subgoal.subgoal_id
            in
            preferred_ids
        ):

            score += 50.0

        ####################################################
        # Avoid a recently failed subgoal unless explicitly
        # preferred by the caller.
        ####################################################

        failed_ids = set(
            context.get(
                "failed_subgoals",
                [],
            )
            or []
        )

        if (
            subgoal.subgoal_id
            in
            failed_ids
        ):

            score -= 25.0

        ####################################################
        # Prefer concrete/actionable objectives over vague
        # catch-all objectives.
        ####################################################

        description = (
            subgoal.description.lower()
        )

        concrete_markers = (
            "open",
            "find",
            "read",
            "create",
            "save",
            "move",
            "rename",
            "check",
            "verify",
            "calculate",
            "search",
        )

        if any(
            marker in description
            for marker in concrete_markers
        ):

            score += 3.0

        return score

    ########################################################
    # CONFIDENCE
    ########################################################

    @staticmethod
    def _confidence(
        score: float,
        count: int,
    ) -> float:

        if count <= 1:

            return 0.95

        # Simple bounded confidence estimate.
        value = (
            0.65
            +
            min(
                max(
                    score / 100.0,
                    0.0,
                ),
                0.30,
            )
        )

        return round(
            min(
                value,
                0.95,
            ),
            3,
        )