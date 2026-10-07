from __future__ import annotations

import time
from typing import Any, Optional


class WorkflowCancellation:

    """
    Cooperative cancellation controller for multi-application
    workflows.

    Cancellation is propagated through workflow state. This layer
    does not force-kill threads or computer processes.
    """

    def __init__(self):

        self.requested = False

        self.reason = ""

        self.requested_at: Optional[
            float
        ] = None

        self.acknowledged = False

        self.acknowledged_at: Optional[
            float
        ] = None

    ############################################################
    # REQUEST
    ############################################################

    def request(
        self,
        reason: str = "Workflow cancelled by user.",
    ) -> dict[str, Any]:

        self.requested = True

        self.reason = str(
            reason
            or
            "Workflow cancelled by user."
        )

        self.requested_at = (
            time.monotonic()
        )

        self.acknowledged = False

        self.acknowledged_at = None

        return self.snapshot()

    ############################################################
    # PROPAGATE
    ############################################################

    def propagate(
        self,
        workflow=None,
    ) -> bool:

        if not self.requested:

            return False

        if workflow is not None:

            try:

                workflow.request_cancel(
                    self.reason
                )

            except Exception:
                pass

        return True

    ############################################################
    # CHECK
    ############################################################

    def is_requested(
        self,
    ) -> bool:

        return bool(
            self.requested
        )

    def checkpoint(
        self,
        workflow=None,
    ) -> bool:

        if workflow is not None:

            try:

                if workflow.is_cancelled():

                    self.requested = True

                    self.reason = (
                        workflow.cancel_reason
                        or
                        self.reason
                        or
                        "Workflow cancelled."
                    )

            except Exception:
                pass

        return self.requested

    ############################################################
    # ACKNOWLEDGE
    ############################################################

    def acknowledge(
        self,
        workflow=None,
    ) -> dict[str, Any]:

        if workflow is not None:

            try:

                stage = (
                    workflow.current_stage()
                )

                if (
                    stage is not None
                    and
                    stage.status
                    ==
                    "RUNNING"
                ):

                    stage.cancel(
                        self.reason
                    )

            except Exception:
                pass

        self.acknowledged = True

        self.acknowledged_at = (
            time.monotonic()
        )

        return self.snapshot()

    ############################################################
    # CLEAR
    ############################################################

    def clear(
        self,
    ):

        self.requested = False

        self.reason = ""

        self.requested_at = None

        self.acknowledged = False

        self.acknowledged_at = None

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "requested":
                self.requested,

            "reason":
                self.reason,

            "requested_at":
                self.requested_at,

            "acknowledged":
                self.acknowledged,

            "acknowledged_at":
                self.acknowledged_at,
        }