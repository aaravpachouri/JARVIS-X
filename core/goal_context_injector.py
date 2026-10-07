from __future__ import annotations

from typing import Any


class GoalContextInjector:

    """
    Adds goal context to an existing reasoning context without
    overwriting the brain's normal conversation/context pipeline.

    Goal context is supplied under its own namespace so the existing
    reasoning system remains authoritative for immediate conversational
    meaning.
    """

    def __init__(
        self,
        goal_continuity,
    ):

        self.goals = (
            goal_continuity
        )

    ############################################################
    # AUGMENT
    ############################################################

    def augment(
        self,
        query: str,
        existing_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        context = dict(
            existing_context
            or
            {}
        )

        goal_context = (
            self.goals.compact_context()
        )

        ########################################################
        # Do not force an unrelated command into a goal.
        ########################################################

        context[
            "jarvis_goal"
        ] = {
            "active":
                goal_context.get(
                    "active_goal"
                ),

            "goal_available":
                goal_context.get(
                    "goal_available",
                    False,
                ),

            "goal_id":
                goal_context.get(
                    "goal_id",
                    "",
                ),
        }

        return context

    ############################################################
    # FORMAT
    ############################################################

    def format_for_model(
        self,
        query: str,
    ) -> str:

        context = (
            self.goals.compact_context()
        )

        goal = context.get(
            "active_goal"
        )

        if not isinstance(
            goal,
            dict,
        ):

            return ""

        title = str(
            goal.get(
                "title",
                "",
            )
            or
            ""
        ).strip()

        description = str(
            goal.get(
                "description",
                "",
            )
            or
            ""
        ).strip()

        if not title and not description:

            return ""

        lines = [
            "Active user goal:",
        ]

        if title:

            lines.append(
                f"- Goal: {title}"
            )

        if description:

            lines.append(
                f"- Objective: {description}"
            )

        progress = goal.get(
            "progress",
            0.0,
        )

        try:

            percent = int(
                float(
                    progress
                    or
                    0.0
                )
                *
                100
            )

        except Exception:

            percent = 0

        lines.append(
            f"- Progress: {percent}%"
        )

        return "\n".join(
            lines
        ).strip()

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return self.goals.snapshot()