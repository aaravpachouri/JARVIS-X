from __future__ import annotations

from typing import Any, Callable, Optional


class WorkflowStageExecutor:
    """
    Executes one stage of a MultiAppWorkflowContext.

    This is an orchestration adapter:
        - owns stage lifecycle
        - checks cancellation
        - calls an injected task runner
        - records result/error into workflow context

    It does NOT implement computer actions itself.
    The existing ComputerUseAgent / task runtime remains the
    actual execution authority.
    """

    def __init__(
        self,
        task_runner: Optional[Callable[..., Any]] = None,
    ):

        self.task_runner = (
            task_runner
        )

    ############################################################
    # RUNNER
    ############################################################

    def set_runner(
        self,
        task_runner: Callable[..., Any],
    ):

        self.task_runner = (
            task_runner
        )

    ############################################################
    # EXECUTE CURRENT STAGE
    ############################################################

    def execute_current(
        self,
        workflow,
        *,
        runner: Optional[Callable[..., Any]] = None,
    ) -> dict[str, Any]:

        if workflow is None:

            return {
                "success":
                    False,

                "error":
                    "No workflow context supplied.",
            }

        if workflow.is_cancelled():

            return {
                "success":
                    False,

                "cancelled":
                    True,

                "error":
                    workflow.cancel_reason
                    or
                    "Workflow was cancelled.",
            }

        stage = (
            workflow.current_stage()
        )

        if stage is None:

            return {
                "success":
                    False,

                "error":
                    "Workflow has no active stage.",
            }

        selected_runner = (
            runner
            or
            self.task_runner
        )

        if selected_runner is None:

            workflow.fail_current_stage(
                "No workflow task runner is configured."
            )

            return {
                "success":
                    False,

                "error":
                    "No workflow task runner is configured.",
            }

        if stage.status == "PENDING":

            stage = workflow.start_next_stage()

            if stage is None:

                return {
                    "success":
                        False,

                    "cancelled":
                        workflow.is_cancelled(),

                    "error":
                        "Could not start workflow stage.",
                }

        if stage.status != "RUNNING":

            return {
                "success":
                    False,

                "error":
                    (
                        "Stage is not executable in its current "
                        f"state: {stage.status}"
                    ),
            }

        ########################################################
        # Cancellation is checked again immediately before
        # handing control to the real computer-task runner.
        ########################################################

        if workflow.is_cancelled():

            stage.cancel(
                workflow.cancel_reason
            )

            return {
                "success":
                    False,

                "cancelled":
                    True,

                "error":
                    workflow.cancel_reason
                    or
                    "Workflow cancelled.",
            }

        try:

            result = self._call_runner(
                selected_runner,
                workflow,
                stage,
            )

        except Exception as exc:

            stage.fail(
                str(
                    exc
                )
            )

            workflow.status = "FAILED"

            workflow.record(
                "stage_executor_error",
                {
                    "stage":
                        stage.name,

                    "error":
                        str(
                            exc
                        ),
                }
            )

            return {
                "success":
                    False,

                "stage":
                    stage.name,

                "error":
                    str(
                        exc
                    ),
            }

        ########################################################
        # The runner may explicitly return a structured failure.
        ########################################################

        if (
            isinstance(
                result,
                dict,
            )
            and
            result.get(
                "success"
            ) is False
        ):

            error = str(
                result.get(
                    "error",
                    result.get(
                        "message",
                        "Workflow stage failed.",
                    ),
                )
                or
                "Workflow stage failed."
            )

            if result.get(
                "cancelled",
                False,
            ):

                stage.cancel(
                    error
                )

                return {
                    "success":
                        False,

                    "cancelled":
                        True,

                    "stage":
                        stage.name,

                    "error":
                        error,
                }

            stage.fail(
                error
            )

            workflow.status = "FAILED"

            return {
                "success":
                    False,

                "stage":
                    stage.name,

                "error":
                    error,

                "result":
                    result,
            }

        ########################################################
        # Stage completed.
        ########################################################

        stage_result = result

        if isinstance(
            result,
            dict,
        ):

            stage_result = result.get(
                "result",
                result,
            )

        workflow.complete_current_stage(
            stage_result
        )

        workflow.record(
            "stage_executor_completed",
            {
                "stage":
                    stage.name,

                "application":
                    stage.application,
            }
        )

        return {
            "success":
                True,

            "stage":
                stage.name,

            "application":
                stage.application,

            "result":
                result,
        }

    ############################################################
    # EXECUTE ALL REMAINING STAGES
    ############################################################

    def execute_remaining(
        self,
        workflow,
        *,
        runner: Optional[Callable[..., Any]] = None,
    ) -> dict[str, Any]:

        if workflow is None:

            return {
                "success":
                    False,

                "error":
                    "No workflow context supplied.",
            }

        if workflow.is_cancelled():

            return {
                "success":
                    False,

                "cancelled":
                    True,

                "error":
                    workflow.cancel_reason
                    or
                    "Workflow was cancelled.",
            }

        results = []

        ########################################################
        # Start the first pending stage when needed.
        ########################################################

        if (
            workflow.current_stage()
            is
            None
        ):

            if workflow.start_next_stage() is None:

                workflow.complete()

                return {
                    "success":
                        True,

                    "results":
                        [],
                }

        while True:

            if workflow.is_cancelled():

                stage = (
                    workflow.current_stage()
                )

                if stage is not None and stage.status == "RUNNING":

                    stage.cancel(
                        workflow.cancel_reason
                    )

                return {
                    "success":
                        False,

                    "cancelled":
                        True,

                    "results":
                        results,

                    "error":
                        workflow.cancel_reason
                        or
                        "Workflow was cancelled.",
                }

            result = self.execute_current(
                workflow,
                runner=runner,
            )

            results.append(
                result
            )

            if not result.get(
                "success",
                False,
            ):

                return {
                    "success":
                        False,

                    "results":
                        results,

                    "error":
                        result.get(
                            "error",
                            "Workflow stage failed.",
                        ),
                }

            if not workflow.has_more_stages():

                workflow.complete()

                workflow.record(
                    "workflow_completed",
                    {
                        "workflow_id":
                            workflow.workflow_id,
                    }
                )

                return {
                    "success":
                        True,

                    "results":
                        results,
                }

            ####################################################
            # Advance to next stage.
            ####################################################

            next_stage = (
                workflow.start_next_stage()
            )

            if next_stage is None:

                return {
                    "success":
                        False,

                    "results":
                        results,

                    "error":
                        "Could not start the next workflow stage.",
                }

    ############################################################
    # RUNNER ADAPTER
    ############################################################

    @staticmethod
    def _call_runner(
        runner,
        workflow,
        stage,
    ):

        """
        Support either:
            runner(stage)
        or:
            runner(workflow, stage)
        """

        try:

            return runner(
                workflow,
                stage,
            )

        except TypeError:

            return runner(
                stage
            )


def execute_workflow_stage(
    workflow,
    runner,
) -> dict[str, Any]:

    executor = (
        WorkflowStageExecutor(
            runner
        )
    )

    return executor.execute_current(
        workflow
    )