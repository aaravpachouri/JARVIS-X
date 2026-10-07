from __future__ import annotations

from typing import Any, Optional


############################################################
# RECOVERY DECISION
############################################################

class ComputerRecoveryDecision:

    RETRY = "RETRY"
    ALTERNATIVE = "ALTERNATIVE"
    WAIT = "WAIT"
    ABORT = "ABORT"

    def __init__(
        self,
        action: str,
        reason: str = "",
        guidance: Optional[
            dict[str, Any]
        ] = None,
    ):

        self.action = action

        self.reason = str(
            reason or ""
        ).strip()

        self.guidance = dict(
            guidance or {}
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "action": self.action,
            "reason": self.reason,
            "guidance": dict(
                self.guidance
            ),
        }


############################################################
# COMPUTER RECOVERY
############################################################

class ComputerRecoveryAdvisor:

    """
    Converts existing recovery state into a compact strategy
    recommendation for the computer reasoning layer.

    It does not execute actions and does not replace
    AgentRecoveryPlanner.
    """

    MAX_RETRIES = 2

    def advise(
        self,
        recovery: Optional[
            dict[str, Any]
        ] = None,
        last_action: Optional[
            dict[str, Any]
        ] = None,
        observation: Optional[
            dict[str, Any]
        ] = None,
    ) -> ComputerRecoveryDecision:

        recovery = dict(
            recovery or {}
        )

        last_action = dict(
            last_action or {}
        )

        observation = dict(
            observation or {}
        )

        ####################################################
        # Blocked tools
        ####################################################

        blocked_tools = set(
            recovery.get(
                "blocked_tools",
                [],
            )
            or []
        )

        tool = str(
            last_action.get(
                "tool",
                "",
            )
        ).upper().strip()

        if (
            tool
            and
            tool in blocked_tools
        ):

            return ComputerRecoveryDecision(
                action=(
                    ComputerRecoveryDecision
                    .ALTERNATIVE
                ),
                reason=(
                    f"{tool} is blocked by the "
                    "existing recovery planner."
                ),
                guidance={
                    "avoid_tool": tool,
                    "choose_different_strategy": True,
                },
            )

        ####################################################
        # Exact failed routes
        ####################################################

        failed_signatures = (
            recovery.get(
                "failed_signatures",
                [],
            )
            or []
        )

        if last_action:

            signature = self._signature(
                last_action
            )

            if signature in failed_signatures:

                return ComputerRecoveryDecision(
                    action=(
                        ComputerRecoveryDecision
                        .ALTERNATIVE
                    ),
                    reason=(
                        "The exact route has already failed."
                    ),
                    guidance={
                        "avoid_exact_route": True,
                        "choose_different_strategy": True,
                    },
                )

        ####################################################
        # Recent semantic failure
        ####################################################

        semantic = (
            recovery.get(
                "recent_semantic_failures",
                [],
            )
            or []
        )

        if semantic:

            latest = semantic[-1]

            return ComputerRecoveryDecision(
                action=(
                    ComputerRecoveryDecision
                    .ALTERNATIVE
                ),
                reason=(
                    "The previous action was executed, "
                    "but its expected screen outcome "
                    "was not observed."
                ),
                guidance={
                    "failure_type": "semantic",
                    "avoid_same_route": True,
                    "latest_failure": latest,
                },
            )

        ####################################################
        # Executor failure
        ####################################################

        executor_failures = (
            recovery.get(
                "recent_executor_failures",
                [],
            )
            or []
        )

        if executor_failures:

            latest = executor_failures[-1]

            return ComputerRecoveryDecision(
                action=(
                    ComputerRecoveryDecision
                    .RETRY
                ),
                reason=(
                    "The executor failed before the "
                    "intended computer state was reached."
                ),
                guidance={
                    "failure_type": "executor",
                    "latest_failure": latest,
                    "retry_count":
                        self._retry_count(
                            recovery
                        ),
                },
            )

        ####################################################
        # Unknown / ambiguous observation
        ####################################################

        uncertainty = (
            observation.get(
                "uncertainty",
                [],
            )
            or []
        )

        if uncertainty:

            return ComputerRecoveryDecision(
                action=(
                    ComputerRecoveryDecision
                    .WAIT
                ),
                reason=(
                    "The current screen observation "
                    "is uncertain."
                ),
                guidance={
                    "wait_for_stable_observation": True,
                    "uncertainty": uncertainty,
                },
            )

        ####################################################
        # Retry budget
        ####################################################

        retry_count = self._retry_count(
            recovery
        )

        if retry_count >= self.MAX_RETRIES:

            return ComputerRecoveryDecision(
                action=(
                    ComputerRecoveryDecision
                    .ABORT
                ),
                reason=(
                    "Recovery retry limit reached."
                ),
                guidance={
                    "retry_limit":
                        self.MAX_RETRIES,
                },
            )

        ####################################################
        # Default
        ####################################################

        return ComputerRecoveryDecision(
            action=(
                ComputerRecoveryDecision
                .RETRY
            ),
            reason=(
                "No blocked route detected; "
                "a bounded retry is allowed."
            ),
            guidance={
                "retry_count":
                    retry_count,
            },
        )

    ########################################################
    # HELPERS
    ########################################################

    @staticmethod
    def _retry_count(
        recovery: dict[str, Any],
    ) -> int:

        failures = (
            recovery.get(
                "recent_executor_failures",
                [],
            )
            or []
        )

        semantic = (
            recovery.get(
                "recent_semantic_failures",
                [],
            )
            or []
        )

        return len(
            failures
        ) + len(
            semantic
        )

    @staticmethod
    def _signature(
        action: dict[str, Any],
    ) -> str:

        tool = str(
            action.get(
                "tool",
                "",
            )
        ).upper().strip()

        parameters = action.get(
            "parameters",
            {},
        )

        return (
            f"{tool}|"
            f"{parameters}"
        )