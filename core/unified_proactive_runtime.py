from __future__ import annotations

from typing import Any, Optional

from core.proactive_runtime_coordinator import ProactiveRuntimeCoordinator
from core.proactive_cadence_policy import ProactiveCadencePolicy


class UnifiedProactiveRuntime:

    """
    Final Phase 8.10 integration facade.

    Adds cadence/noise control around ProactiveRuntimeCoordinator.
    Actual execution remains delegated to the existing JARVIS
    runtime after approval.
    """

    def __init__(
        self,
        runtime: Optional[
            ProactiveRuntimeCoordinator
        ] = None,
        cadence: Optional[
            ProactiveCadencePolicy
        ] = None,
    ):

        self.runtime = (
            runtime
            or
            ProactiveRuntimeCoordinator()
        )

        self.cadence = (
            cadence
            or
            ProactiveCadencePolicy()
        )

    def refresh(
        self,
        *,
        goal_context=None,
        memory_context=None,
        runtime_context=None,
    ) -> dict[str, Any]:

        state = self.runtime.refresh(
            goal_context=goal_context,
            memory_context=memory_context,
            runtime_context=runtime_context,
        )

        allowed_notifications = []

        for item in state.get(
            "notifications",
            [],
        ):

            policy = self.cadence.allow(
                item
            )

            if not policy.get(
                "allowed",
                False,
            ):
                continue

            allowed_notifications.append(
                {
                    "notification":
                        item,

                    "policy":
                        policy,
                }
            )

        for item in allowed_notifications:

            self.cadence.record(
                item.get(
                    "notification"
                )
            )

        return {
            **state,

            "allowed_notifications":
                allowed_notifications,

            "cadence":
                self.cadence.snapshot(),
        }

    def approve(
        self,
        opportunity,
        *,
        action_type: str = "",
        explicit_automation: bool = False,
    ):

        return self.runtime.approve(
            opportunity,
            action_type=action_type,
            explicit_automation=explicit_automation,
        )

    def next_notification(
        self,
    ):

        allowed = self.refresh().get(
            "allowed_notifications",
            [],
        )

        return (
            allowed[0]
            if allowed
            else
            None
        )

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "runtime":
                self.runtime.snapshot(),

            "cadence":
                self.cadence.snapshot(),
        }