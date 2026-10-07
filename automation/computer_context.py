from __future__ import annotations

from typing import Any, Optional


class ComputerContextBuilder:

    """
    Builds a compact reasoning context for the computer agent.

    It combines existing state rather than creating a second
    source of truth.
    """

    def build(
        self,
        state,
        observation: Optional[dict[str, Any]] = None,
        recovery: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:

        observation = dict(
            observation or {}
        )

        recovery = dict(
            recovery or {}
        )

        context = {
            "goal": getattr(
                state,
                "goal",
                "",
            ),

            "status": getattr(
                state,
                "status",
                "",
            ),

            "step": getattr(
                state,
                "step",
                0,
            ),

            "current_stage": (
                state.currentStage()
                if hasattr(
                    state,
                    "currentStage",
                )
                else ""
            ),

            "stages": list(
                getattr(
                    state,
                    "stages",
                    [],
                )
                or []
            ),

            "recent_history": (
                state.recent_history(8)
                if hasattr(
                    state,
                    "recent_history",
                )
                else []
            ),

            "recent_records": (
                state.recent_records(10)
                if hasattr(
                    state,
                    "recent_records",
                )
                else []
            ),

            "variables": dict(
                getattr(
                    state,
                    "variables",
                    {},
                )
                or {}
            ),

            "last_action": getattr(
                state,
                "last_action",
                None,
            ),

            "last_result": getattr(
                state,
                "last_result",
                None,
            ),

            "errors": list(
                getattr(
                    state,
                    "errors",
                    [],
                )
                or []
            )[-5:],

            "observation": observation,

            "recovery": recovery,
        }

        return self._compact(
            context
        )

    @staticmethod
    def _compact(
        context: dict[str, Any],
    ) -> dict[str, Any]:

        """
        Prevent context from growing without bound.
        """

        history = context.get(
            "recent_history",
            [],
        )

        if isinstance(
            history,
            list,
        ):

            context[
                "recent_history"
            ] = history[-8:]

        records = context.get(
            "recent_records",
            [],
        )

        if isinstance(
            records,
            list,
        ):

            context[
                "recent_records"
            ] = records[-10:]

        variables = context.get(
            "variables",
            {},
        )

        if isinstance(
            variables,
            dict,
        ):

            context[
                "variables"
            ] = dict(
                list(
                    variables.items()
                )[-20:]
            )

        errors = context.get(
            "errors",
            [],
        )

        if isinstance(
            errors,
            list,
        ):

            context[
                "errors"
            ] = errors[-5:]

        return context

    ########################################################
    # MODEL-FRIENDLY TEXT
    ########################################################

    def build_prompt_context(
        self,
        context: dict[str, Any],
    ) -> str:

        lines = [
            "CURRENT COMPUTER TASK CONTEXT:",
            "",
            f"Goal: {context.get('goal', '')}",
            f"Status: {context.get('status', '')}",
            f"Step: {context.get('step', 0)}",
            f"Current stage: {context.get('current_stage', '')}",
            "",
            "Recent history:",
        ]

        history = context.get(
            "recent_history",
            [],
        )

        if history:

            for item in history:

                lines.append(
                    f"- {item}"
                )

        else:

            lines.append(
                "- None"
            )

        lines.extend(
            [
                "",
                "Current observation:",
                str(
                    context.get(
                        "observation",
                        {},
                    )
                ),
                "",
                "Recovery information:",
                str(
                    context.get(
                        "recovery",
                        {},
                    )
                ),
            ]
        )

        errors = context.get(
            "errors",
            [],
        )

        if errors:

            lines.extend(
                [
                    "",
                    "Recent errors:",
                ]
            )

            for error in errors:

                lines.append(
                    f"- {error}"
                )

        return "\n".join(
            lines
        )