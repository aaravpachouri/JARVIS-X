from __future__ import annotations

from typing import Any, Callable, Optional

from automation.workflow_stage_executor import WorkflowStageExecutor
from automation.workflow_transition_guard import ApplicationTransitionGuard
from automation.cross_app_state_transfer import CrossAppStateTransfer
from automation.workflow_recovery import WorkflowRecovery
from automation.workflow_cancellation import WorkflowCancellation
from automation.multi_app_workflow_verification import (
    MultiAppWorkflowVerification,
)


class MultiAppWorkflowCoordinator:

    """
    Unified orchestration facade for Phase 8.6.

    Combines:
        - workflow/stage context
        - stage execution
        - application transitions
        - cross-app state transfer
        - recovery
        - cancellation
        - multi-app verification

    Actual computer actions remain delegated to the existing
    ComputerUseAgent/runtime.
    """

    def __init__(
        self,
        runner: Optional[
            Callable[..., Any]
        ] = None,
        verifier: Optional[
            Callable[..., Any]
        ] = None,
    ):

        self.stage_executor = (
            WorkflowStageExecutor(
                runner
            )
        )

        self.transition_guard = (
            ApplicationTransitionGuard()
        )

        self.state_transfer = (
            CrossAppStateTransfer()
        )

        self.recovery = (
            WorkflowRecovery()
        )

        self.cancellation = (
            WorkflowCancellation()
        )

        self.verification = (
            MultiAppWorkflowVerification(
                verifier
            )
        )

        self.workflow = None

    ############################################################
    # BIND
    ############################################################

    def bind(
        self,
        workflow,
    ):

        self.workflow = (
            workflow
        )

        self.state_transfer.import_from_workflow(
            workflow
        )

    ############################################################
    # NEXT STAGE
    ############################################################

    def prepare_next_stage(
        self,
    ) -> dict[str, Any]:

        if self.workflow is None:

            return {
                "success":
                    False,

                "error":
                    "No workflow is bound.",
            }

        if self.cancellation.checkpoint(
            self.workflow
        ):

            return {
                "success":
                    False,

                "cancelled":
                    True,

                "error":
                    self.cancellation.reason
                    or
                    "Workflow cancelled.",
            }

        stage = (
            self.workflow.current_stage()
        )

        if (
            stage is None
            and
            self.workflow.has_more_stages()
            is
            False
        ):

            stage = (
                self.workflow.start_next_stage()
            )

        if stage is None:

            return {
                "success":
                    False,

                "error":
                    "No next workflow stage is available.",
            }

        transition = (
            self.transition_guard.begin(
                self.workflow.active_application,
                stage.application,
            )
        )

        if not transition.get(
            "allowed",
            False,
        ):

            return {
                "success":
                    False,

                "error":
                    transition.get(
                        "reason",
                        "Application transition rejected.",
                    ),
            }

        return {
            "success":
                True,

            "stage":
                stage.to_dict(),

            "transition":
                transition,
        }

    ############################################################
    # EXECUTE CURRENT
    ############################################################

    def execute_current(
        self,
    ) -> dict[str, Any]:

        if self.workflow is None:

            return {
                "success":
                    False,

                "error":
                    "No workflow is bound.",
            }

        result = (
            self.stage_executor.execute_current(
                self.workflow
            )
        )

        if not result.get(
            "success",
            False,
        ):

            return result

        self.state_transfer.export_to_workflow(
            self.workflow
        )

        return result

    ############################################################
    # VERIFY CURRENT
    ############################################################

    def verify_current(
        self,
        observed_application: str = "",
        result: Any = None,
    ) -> dict[str, Any]:

        if self.workflow is None:

            return {
                "verified":
                    False,

                "reason":
                    "No workflow is bound.",
            }

        stage = (
            self.workflow.current_stage()
        )

        verification = (
            self.verification.verify_stage(
                self.workflow,
                stage,
                observed_application=(
                    observed_application
                ),
                result=result,
            )
        )

        if not verification.get(
            "verified",
            False,
        ):

            self.recovery.handle_failure(
                self.workflow,
                stage,
                verification.get(
                    "reason",
                    "Stage verification failed.",
                ),
                verification_failed=True,
            )

        return verification

    ############################################################
    # CANCEL
    ############################################################

    def cancel(
        self,
        reason: str = "Workflow cancelled by user.",
    ) -> dict[str, Any]:

        result = (
            self.cancellation.request(
                reason
            )
        )

        self.cancellation.propagate(
            self.workflow
        )

        self.cancellation.acknowledge(
            self.workflow
        )

        return result

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "workflow":
                (
                    self.workflow.snapshot()
                    if self.workflow is not None
                    else
                    None
                ),

            "transition":
                {
                    "current":
                        self.transition_guard.current_application,

                    "previous":
                        self.transition_guard.previous_application,
                },

            "recovery":
                self.recovery.snapshot(),

            "cancellation":
                self.cancellation.snapshot(),

            "verification":
                self.verification.snapshot(),

            "state_transfer":
                self.state_transfer.compact_context(),
        }