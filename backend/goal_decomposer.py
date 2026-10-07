from __future__ import annotations

import json
from typing import Any, Optional

from backend.intent_decomposer import (
    DecomposedIntent,
    IntentDecomposer,
)


class GoalDecomposer:

    """
    Uses the local AI brain to turn a complex request into
    meaningful subgoals.

    This layer does NOT execute anything.

    It only produces structured reasoning data for the
    planner/orchestrator.
    """

    SYSTEM_PROMPT = """
You are the goal-decomposition component of JARVIS X.

Your job is to decompose a user's complex request into the
smallest meaningful objectives required to accomplish the
overall goal.

Rules:

1. Preserve the user's actual intent.
2. Do not invent unnecessary tasks.
3. Do not describe individual mouse clicks or keystrokes.
4. Each subgoal should represent a meaningful objective.
5. Identify dependencies between subgoals.
6. Keep the number of subgoals reasonably small.
7. If the request is already simple, return one subgoal.
8. Do not execute anything.
9. Return ONLY valid JSON.

Required JSON structure:

{
    "primary_goal": "overall objective",
    "subgoals": [
        {
            "description": "meaningful objective",
            "goal_type": "research|computer|reasoning|creation|verification|other",
            "priority": 0,
            "dependencies": [],
            "constraints": []
        }
    ],
    "global_constraints": [],
    "requested_result": ""
}
""".strip()

    def __init__(
        self,
        brain,
    ):

        self.brain = brain

    ########################################################
    # DECOMPOSE
    ########################################################

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

        prompt = self._build_prompt(
            request,
            context,
        )

        raw = self.brain.local.json(
            prompt,
            system=self.SYSTEM_PROMPT,
        )

        if not isinstance(
            raw,
            dict,
        ):

            raise ValueError(
                "Goal decomposer returned invalid data."
            )

        intent = (
            self._build_intent(
                request,
                raw,
                context,
            )
        )

        return intent

    ########################################################
    # PROMPT
    ########################################################

    @staticmethod
    def _build_prompt(
        request: str,
        context: dict[str, Any],
    ) -> str:

        return f"""
USER REQUEST:
{request}

CURRENT CONTEXT:
{json.dumps(
    context,
    ensure_ascii=False,
    default=str,
)}

Decompose the request into meaningful objectives.
""".strip()

    ########################################################
    # BUILD INTENT
    ########################################################

    def _build_intent(
        self,
        request: str,
        data: dict[str, Any],
        context: dict[str, Any],
    ) -> DecomposedIntent:

        primary_goal = str(
            data.get(
                "primary_goal",
                request,
            )
            or request
        ).strip()

        intent = DecomposedIntent(
            request=request,
            primary_goal=primary_goal,
            global_constraints=list(
                data.get(
                    "global_constraints",
                    [],
                )
                or []
            ),
            requested_result=str(
                data.get(
                    "requested_result",
                    "",
                )
                or ""
            ).strip(),
            metadata={
                "context": context,
                "source": "LOCAL_BRAIN",
            },
        )

        decomposer = IntentDecomposer()

        subgoals = data.get(
            "subgoals",
            [],
        )

        if not isinstance(
            subgoals,
            list,
        ):

            subgoals = []

        for index, item in enumerate(
            subgoals,
            start=1,
        ):

            if not isinstance(
                item,
                dict,
            ):

                continue

            description = str(
                item.get(
                    "description",
                    "",
                )
                or ""
            ).strip()

            if not description:

                continue

            dependencies = list(
                item.get(
                    "dependencies",
                    [],
                )
                or []
            )

            constraints = list(
                item.get(
                    "constraints",
                    [],
                )
                or []
            )

            goal_type = str(
                item.get(
                    "goal_type",
                    "other",
                )
                or "other"
            ).strip()

            priority = self._safe_priority(
                item.get(
                    "priority",
                    index,
                ),
                index,
            )

            subgoal = decomposer.add_subgoal(
                intent,
                description=description,
                goal_type=goal_type,
                priority=priority,
                dependencies=dependencies,
                constraints=constraints,
            )

            subgoal.metadata[
                "order"
            ] = index

        ####################################################
        # Safe fallback for simple requests.
        ####################################################

        if not intent.subgoals:

            decomposer.add_subgoal(
                intent,
                description=primary_goal,
                goal_type="other",
                priority=1,
            )

        ####################################################
        # Normalize dependency references.
        #
        # The model may return indexes such as:
        #   [1]
        #   ["1"]
        #
        # Convert them to actual subgoal IDs.
        ####################################################

        self._normalize_dependencies(
            intent
        )

        intent.validate()

        decomposer.validate_dependencies(
            intent
        )

        return intent

    ########################################################
    # DEPENDENCY NORMALIZATION
    ########################################################

    @staticmethod
    def _normalize_dependencies(
        intent: DecomposedIntent,
    ) -> None:

        subgoals = intent.subgoals

        id_map = {
            str(index + 1):
                subgoal.subgoal_id

            for index, subgoal
            in enumerate(subgoals)
        }

        for subgoal in subgoals:

            normalized = []

            for dependency in (
                subgoal.dependencies
            ):

                dependency_text = str(
                    dependency
                ).strip()

                if dependency_text in id_map:

                    dependency_text = (
                        id_map[
                            dependency_text
                        ]
                    )

                if (
                    dependency_text
                    in
                    {
                        item.subgoal_id
                        for item in subgoals
                    }
                ):

                    if (
                        dependency_text
                        !=
                        subgoal.subgoal_id
                    ):

                        normalized.append(
                            dependency_text
                        )

            subgoal.dependencies = list(
                dict.fromkeys(
                    normalized
                )
            )

    ########################################################
    # PRIORITY
    ########################################################

    @staticmethod
    def _safe_priority(
        value,
        fallback: int,
    ) -> int:

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return int(
                fallback
            )