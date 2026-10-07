from __future__ import annotations

from typing import Any, Optional

from core.proactive_action_coordinator import ProactiveActionCoordinator
from core.proactive_notification_manager import ProactiveNotificationManager


class ProactiveRuntimeCoordinator:

    """
    Final runtime facade for Phase 8.10 proactive intelligence.

    Combines:
        - trigger/opportunity generation
        - ranking
        - approval policy
        - notification delivery state

    It remains suggestion-first. Actual computer execution is
    delegated to the existing runtime after explicit approval or
    an existing automation policy.
    """

    def __init__(
        self,
        *,
        action_coordinator: Optional[
            ProactiveActionCoordinator
        ] = None,
        notifications: Optional[
            ProactiveNotificationManager
        ] = None,
    ):

        self.actions = (
            action_coordinator
            or
            ProactiveActionCoordinator()
        )

        self.notifications = (
            notifications
            or
            ProactiveNotificationManager()
        )

    ############################################################
    # REFRESH
    ############################################################

    def refresh(
        self,
        *,
        goal_context=None,
        memory_context=None,
        runtime_context=None,
    ) -> dict[str, Any]:

        state = self.actions.refresh(
            goal_context=goal_context,
            memory_context=memory_context,
            runtime_context=runtime_context,
        )

        created = []

        ranked = state.get(
            "opportunities",
            [],
        )

        ########################################################
        # Only create user-facing notifications for high-quality
        # opportunities. Approval still remains a separate gate.
        ########################################################

        for ranked_item in ranked:

            if not isinstance(
                ranked_item,
                dict,
            ):
                continue

            opportunity = ranked_item.get(
                "opportunity"
            )

            score = float(
                ranked_item.get(
                    "score",
                    0.0,
                )
                or
                0.0
            )

            if (
                opportunity is None
                or
                score < 0.55
            ):

                continue

            notification = (
                self.notifications.from_opportunity(
                    opportunity
                )
            )

            if notification is not None:

                created.append(
                    notification
                )

        return {
            **state,

            "notifications":
                [
                    item.to_dict()
                    for item
                    in created
                ],
        }

    ############################################################
    # TOP NOTIFICATION
    ############################################################

    def next_notification(
        self,
    ):

        pending = (
            self.notifications.pending(
                1
            )
        )

        return (
            pending[0]
            if pending
            else
            None
        )

    ############################################################
    # APPROVAL
    ############################################################

    def approve(
        self,
        opportunity,
        *,
        action_type: str = "",
        explicit_automation: bool = False,
    ) -> dict[str, Any]:

        return self.actions.evaluate(
            opportunity,
            action_type=action_type,
            user_approved=True,
            explicit_automation=explicit_automation,
        )

    def dismiss_notification(
        self,
        notification_id: str,
    ) -> bool:

        return self.notifications.dismiss(
            notification_id
        )

    def mark_notification_delivered(
        self,
        notification_id: str,
    ) -> bool:

        return self.notifications.mark_delivered(
            notification_id
        )

    ############################################################
    # CONTEXT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "notifications":
                self.notifications.snapshot(),

            "proactive":
                {
                    "pending":
                        [
                            item
                            for item
                            in self.actions.engine.snapshot().get(
                                "opportunities",
                                [],
                            )
                        ]
                },
        }