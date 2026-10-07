from __future__ import annotations

import time
from typing import Any, Optional


class WorkflowRecovery:

    """
    Recovery controller for multi-application workflows.

    It does not execute computer actions directly.
    It decides what the workflow runtime should do after a stage
    failure, transition failure, or verification failure.
    """

    MAX_RECOVERY_ATTEMPTS = 3

    def __init__(
        self,
        max_attempts: int = MAX_RECOVERY_ATTEMPTS,
    ):

        self.max_attempts = max(
            1,
            int(
                max_attempts
            ),
        )

        self.attempts = 0

        self.events: list[
            dict[str, Any]
        ] = []

        self.last_reason = ""

    ############################################################
    # RECORD
    ############################################################

    def record(
        self,
        event: str,
        data: Optional[
            dict[str, Any]
        ] = None,
    ):

        self.events.append(
            {
                "timestamp":
                    time.monotonic(),

                "event":
                    str(
                        event
                    ),

                "data":
                    dict(
                        data
                        or
                        {}
                    ),
            }
        )

        if len(
            self.events
        ) > 50:

            del self.events[
                :-
                50
            ]

    ############################################################
    # FAILURE
    ############################################################

    def handle_failure(
        self,
        workflow,
        stage,
        reason: str,
        *,
        verification_failed: bool = False,
        transition_failed: bool = False,
    ) -> dict[str, Any]:

        self.last_reason = str(
            reason
            or
            "Workflow stage failed."
        )

        self.attempts += 1

        self.record(
            "recovery_attempt",
            {
                "stage":
                    getattr(
                        stage,
                        "name",
                        "",
                    ),

                "attempt":
                    self.attempts,

                "reason":
                    self.last_reason,

                "verification_failed":
                    verification_failed,

                "transition_failed":
                    transition_failed,
            }
        )

        if workflow is not None:

            try:

                workflow.record(
                    "workflow_recovery",
                    {
                        "attempt":
                            self.attempts,

                        "reason":
                            self.last_reason,
                    }
                )

            except Exception:
                pass

        ########################################################
        # Hard stop after repeated failures.
        ########################################################

        if (
            self.attempts
            >=
            self.max_attempts
        ):

            if workflow is not None:

                try:

                    workflow.fail(
                        "Workflow recovery limit reached."
                    )

                except Exception:
                    pass

            return {
                "recover":
                    False,

                "terminal":
                    True,

                "attempt":
                    self.attempts,

                "strategy":
                    "STOP",

                "reason":
                    "Workflow recovery limit reached.",
            }

        ########################################################
        # Verification failure means re-observe/re-verify before
        # attempting a completely different action.
        ########################################################

        if verification_failed:

            strategy = (
                "REFRESH_AND_VERIFY"
            )

        ########################################################
        # Transition failure means re-establish the requested
        # application before continuing.
        ########################################################

        elif transition_failed:

            strategy = (
                "REESTABLISH_APPLICATION"
            )

        ########################################################
        # Generic stage failure: retry stage once, then use a
        # higher-level replanning route on later attempts.
        ########################################################

        elif self.attempts == 1:

            strategy = "RETRY_STAGE"

        else:

            strategy = "REPLAN_STAGE"

        return {
            "recover":
                True,

            "terminal":
                False,

            "attempt":
                self.attempts,

            "strategy":
                strategy,

            "reason":
                self.last_reason,
        }

    ############################################################
    # SUCCESS / RESET
    ############################################################

    def reset(
        self,
    ):

        self.attempts = 0

        self.last_reason = ""

        self.events.clear()

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "attempts":
                self.attempts,

            "max_attempts":
                self.max_attempts,

            "last_reason":
                self.last_reason,

            "events":
                list(
                    self.events[
                        -20:
                    ]
                ),
        }


def recover_workflow_stage(
    recovery: WorkflowRecovery,
    workflow,
    stage,
    reason: str,
) -> dict[str, Any]:

    return recovery.handle_failure(
        workflow,
        stage,
        reason,
    )