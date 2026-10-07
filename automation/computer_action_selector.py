from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


############################################################
# ACTION CANDIDATE
############################################################

@dataclass
class ActionCandidate:

    tool: str = ""

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    reason: str = ""

    confidence: float = 0.0

    risk: float = 0.0

    expected_outcome: str = ""


############################################################
# ACTION SELECTION RESULT
############################################################

@dataclass
class ActionSelection:

    selected: Optional[
        ActionCandidate
    ] = None

    alternatives: list[
        ActionCandidate
    ] = field(
        default_factory=list
    )

    reason: str = ""

    confidence: float = 0.0


############################################################
# ACTION SELECTOR
############################################################

class ComputerActionSelector:

    """
    Lightweight decision layer for computer actions.

    It ranks candidate actions supplied by the reasoning layer.

    It does NOT execute actions.
    """

    def select(
        self,
        candidates: list[
            ActionCandidate
        ],
        observation: Optional[
            dict[str, Any]
        ] = None,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> ActionSelection:

        observation = dict(
            observation or {}
        )

        context = dict(
            context or {}
        )

        if not candidates:

            return ActionSelection(
                reason="No action candidates were supplied."
            )

        valid = [
            candidate
            for candidate in candidates
            if self._valid(candidate)
        ]

        if not valid:

            return ActionSelection(
                reason="No valid action candidates were supplied."
            )

        ########################################################
        # Rank candidates.
        #
        # Higher confidence is better.
        # Lower risk is better.
        ########################################################

        ranked = sorted(
            valid,
            key=lambda item: (
                -float(
                    item.confidence
                ),
                float(
                    item.risk
                ),
            ),
        )

        selected = ranked[0]

        ########################################################
        # Basic uncertainty gate.
        ########################################################

        uncertainty = observation.get(
            "uncertainty",
            []
        )

        if (
            uncertainty
            and
            selected.confidence < 0.75
        ):

            return ActionSelection(
                selected=None,
                alternatives=ranked,
                reason=(
                    "Screen interpretation is uncertain "
                    "and no candidate has sufficient confidence."
                ),
                confidence=selected.confidence,
            )

        ########################################################
        # Respect an explicit action-risk threshold.
        ########################################################

        max_risk = context.get(
            "max_action_risk",
            0.80,
        )

        try:

            max_risk = float(
                max_risk
            )

        except (
            TypeError,
            ValueError,
        ):

            max_risk = 0.80

        if selected.risk > max_risk:

            return ActionSelection(
                selected=None,
                alternatives=ranked,
                reason=(
                    "Best candidate exceeds the allowed "
                    "action-risk threshold."
                ),
                confidence=selected.confidence,
            )

        return ActionSelection(
            selected=selected,
            alternatives=ranked[1:],
            reason=(
                selected.reason
                or
                "Highest-confidence safe action selected."
            ),
            confidence=selected.confidence,
        )

    ########################################################
    # VALIDATION
    ########################################################

    @staticmethod
    def _valid(
        candidate: ActionCandidate,
    ) -> bool:

        if not isinstance(
            candidate,
            ActionCandidate,
        ):

            return False

        if not str(
            candidate.tool or ""
        ).strip():

            return False

        try:

            confidence = float(
                candidate.confidence
            )

            risk = float(
                candidate.risk
            )

        except (
            TypeError,
            ValueError,
        ):

            return False

        return (
            0.0 <= confidence <= 1.0
            and
            0.0 <= risk <= 1.0
        )