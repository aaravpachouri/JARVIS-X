from __future__ import annotations

import time
from typing import Any, Optional


class ApplicationTransitionGuard:
    """
    Controls whether a multi-application workflow may safely
    transition into its next application.

    This class does not launch or focus applications itself.
    It validates the transition state and produces a transition
    contract for the existing application/browser executors.
    """

    def __init__(
        self,
        settle_time: float = 0.20,
    ):

        self.settle_time = max(
            0.0,
            float(
                settle_time
            ),
        )

        self.current_application = ""

        self.previous_application = ""

        self.last_transition_at = 0.0

    ############################################################
    # PLAN TRANSITION
    ############################################################

    def plan_transition(
        self,
        current_application: str,
        next_application: str,
    ) -> dict[str, Any]:

        current = str(
            current_application
            or
            ""
        ).strip()

        next_app = str(
            next_application
            or
            ""
        ).strip()

        ########################################################
        # No target application.
        ########################################################

        if not next_app:

            return {
                "allowed":
                    False,

                "required":
                    False,

                "reason":
                    "Next application was not specified.",
            }

        ########################################################
        # Already in requested application.
        ########################################################

        if (
            current
            and
            current.lower()
            ==
            next_app.lower()
        ):

            return {
                "allowed":
                    True,

                "required":
                    False,

                "current":
                    current,

                "next":
                    next_app,

                "reason":
                    "Already in the requested application.",
            }

        return {
            "allowed":
                True,

            "required":
                True,

            "current":
                current,

            "next":
                next_app,

            "reason":
                "Application transition required.",
        }

    ############################################################
    # BEGIN
    ############################################################

    def begin(
        self,
        current_application: str,
        next_application: str,
    ) -> dict[str, Any]:

        plan = self.plan_transition(
            current_application,
            next_application,
        )

        if not plan.get(
            "allowed",
            False,
        ):

            return plan

        if not plan.get(
            "required",
            False,
        ):

            self.current_application = (
                str(
                    next_application
                    or
                    ""
                ).strip()
            )

            return plan

        self.previous_application = (
            str(
                current_application
                or
                ""
            ).strip()
        )

        self.current_application = (
            str(
                next_application
                or
                ""
            ).strip()
        )

        self.last_transition_at = (
            time.monotonic()
        )

        return {
            **plan,

            "started":
                True,

            "started_at":
                self.last_transition_at,
        }

    ############################################################
    # SETTLE
    ############################################################

    def can_continue(
        self,
        observed_application: str = "",
    ) -> dict[str, Any]:

        observed = str(
            observed_application
            or
            ""
        ).strip()

        elapsed = (
            time.monotonic()
            -
            self.last_transition_at
        )

        target = self.current_application

        application_matches = (
            bool(
                target
            )
            and
            bool(
                observed
            )
            and
            target.lower()
            ==
            observed.lower()
        )

        if not target:

            return {
                "ready":
                    True,

                "application_matches":
                    True,

                "reason":
                    "No application transition is pending.",
            }

        if (
            elapsed
            <
            self.settle_time
        ):

            return {
                "ready":
                    False,

                "application_matches":
                    application_matches,

                "reason":
                    "Application transition is still settling.",

                "wait":
                    self.settle_time - elapsed,
            }

        ########################################################
        # Once the settle interval has elapsed, a known observed
        # application must match the requested target.
        ########################################################

        if observed:

            return {
                "ready":
                    application_matches,

                "application_matches":
                    application_matches,

                "reason":
                    (
                        "Target application is active."
                        if application_matches
                        else
                        (
                            "Target application is not active. "
                            f"Expected '{target}', observed '{observed}'."
                        )
                    ),
            }

        return {
            "ready":
                False,

            "application_matches":
                False,

            "reason":
                "Target application has not been observed yet.",
        }

    ############################################################
    # COMPLETE
    ############################################################

    def complete(
        self,
        observed_application: str = "",
    ) -> dict[str, Any]:

        readiness = self.can_continue(
            observed_application
        )

        if not readiness.get(
            "ready",
            False,
        ):

            return {
                "success":
                    False,

                **readiness,
            }

        self.previous_application = (
            self.current_application
        )

        return {
            "success":
                True,

            "application":
                self.current_application,

            "reason":
                "Application transition completed.",
        }

    ############################################################
    # RESET
    ############################################################

    def reset(
        self,
    ):

        self.current_application = ""

        self.previous_application = ""

        self.last_transition_at = 0.0