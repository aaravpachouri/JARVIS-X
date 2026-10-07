from __future__ import annotations

from typing import Any, Optional

from automation.computer_task_contract import (
    ComputerTaskContract,
    create_computer_task,
)

from backend.computer_agent import (
    ComputerUseAgent,
)

from backend.task_orchestrator import (
    StepResult,
    TaskExecutor,
    TaskStep,
)


class ComputerTaskAdapter:

    """
    Converts a TaskStep into the universal ComputerTaskContract.

    The contract describes WHAT must be achieved.

    ComputerUseAgent remains responsible for HOW to achieve it.
    """

    @staticmethod
    def from_step(
        step: TaskStep,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> ComputerTaskContract:

        context = dict(
            context or {}
        )

        metadata = dict(
            getattr(
                step,
                "metadata",
                {},
            )
            or {}
        )

        success_criteria = list(
            metadata.get(
                "success_criteria",
                [],
            )
            or []
        )

        constraints = list(
            metadata.get(
                "constraints",
                [],
            )
            or []
        )

        requested_result = str(
            metadata.get(
                "requested_result",
                "",
            )
            or ""
        ).strip()

        task_context = dict(
            context
        )

        return create_computer_task(
            goal=str(
                step.description
                or ""
            ).strip(),

            success_criteria=success_criteria,

            constraints=constraints,

            context=task_context,

            requested_result=requested_result,

            metadata={
                "task_step_id":
                    step.step_id,

                "executor":
                    step.executor,

                "source":
                    metadata.get(
                        "source",
                        "TaskOrchestrator",
                    ),
            },
        )


class ComputerAgentExecutor(
    TaskExecutor
):

    """
    Runtime adapter for the existing ComputerUseAgent.

    The executor receives a generic TaskStep, converts it into
    ComputerTaskContract, and then passes only the task objective
    to the existing computer-control kernel.

    No new computer-control implementation is introduced.
    """

    name = "COMPUTER_AGENT"

    def __init__(
        self,
        agent: Optional[
            ComputerUseAgent
        ] = None,
    ):

        self.agent = (
            agent
            if agent is not None
            else ComputerUseAgent()
        )

    ########################################################
    # CAN EXECUTE
    ########################################################

    def can_execute(
        self,
        step: TaskStep,
    ) -> bool:

        return (
            str(
                step.executor
                or ""
            ).strip().upper()
            ==
            self.name
        )

    ########################################################
    # EXECUTE
    ########################################################

    def execute(
        self,
        step: TaskStep,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> StepResult:

        context = dict(
            context or {}
        )

        ####################################################
        # Build universal computer-task contract.
        ####################################################

        try:

            computer_task = (
                ComputerTaskAdapter.from_step(
                    step,
                    context,
                )
            )

        except Exception as exc:

            return StepResult(
                success=False,
                error=(
                    "Could not build the computer "
                    f"task contract: {exc}"
                ),
                executor=self.name,
            )

        ####################################################
        # Respect cancellation before starting.
        ####################################################

        cancel_event = context.get(
            "cancel_event"
        )

        if (
            cancel_event is not None
            and
            hasattr(
                cancel_event,
                "is_set",
            )
            and
            cancel_event.is_set()
        ):

            try:

                self.agent.cancel(
                    "Task cancelled before computer execution."
                )

            except Exception:
                pass

            return StepResult(
                success=False,
                error=(
                    "Computer task was cancelled "
                    "before execution."
                ),
                executor=self.name,
                metadata={
                    "cancelled": True,
                    "computer_task":
                        computer_task.to_dict(),
                },
            )

        ####################################################
        # Start contract lifecycle.
        ####################################################

        computer_task.start()

        print(
            "[ComputerAgentExecutor] "
            "Computer task contract ready."
        )

        print(
            "[ComputerAgentExecutor] "
            f"Goal: {computer_task.goal}"
        )

        ####################################################
        # Existing ComputerUseAgent remains the actual
        # physical computer executor.
        ####################################################

        try:

            if not self.agent.shouldHandle(
                computer_task.goal
            ):

                computer_task.fail(
                    "ComputerUseAgent rejected the goal."
                )

                return StepResult(
                    success=False,
                    error=(
                        "ComputerUseAgent rejected "
                        "the computer goal."
                    ),
                    executor=self.name,
                    metadata={
                        "computer_task":
                            computer_task.to_dict(),
                    },
                )

            result = self.agent.run(
                computer_task.goal
            )

        except Exception as exc:

            computer_task.fail(
                str(
                    exc
                )
            )

            return StepResult(
                success=False,
                error=str(
                    exc
                ),
                executor=self.name,
                metadata={
                    "computer_task":
                        computer_task.to_dict(),
                },
            )

        ####################################################
        # Cooperative cancellation.
        ####################################################

        if self.agent.is_cancelled():

            computer_task.cancel(
                "Computer task was cancelled."
            )

            return StepResult(
                success=False,
                result=result,
                error=(
                    "Computer task was cancelled."
                ),
                executor=self.name,
                metadata={
                    "cancelled": True,
                    "computer_task":
                        computer_task.to_dict(),
                },
            )

        if result is None:

            computer_task.fail(
                "ComputerUseAgent returned no result."
            )

            return StepResult(
                success=False,
                error=(
                    "ComputerUseAgent returned no result."
                ),
                executor=self.name,
                metadata={
                    "computer_task":
                        computer_task.to_dict(),
                },
            )

        ####################################################
        # The existing ComputerUseAgent's successful run is
        # treated as the computer-layer completion result.
        ####################################################

        computer_task.complete(
            result
        )

        return StepResult(
            success=True,
            result=result,
            executor=self.name,
            verification=(
                "ComputerUseAgent completed the computer "
                "task through its existing execution and "
                "verification loop."
            ),
            metadata={
                "verified": True,
                "verification_source":
                    "ComputerUseAgent",
                "computer_task":
                    computer_task.to_dict(),
            },
        )

    ########################################################
    # CANCEL
    ########################################################

    def cancel(
        self,
        reason: str = "Task interrupted by user.",
    ) -> None:

        self.agent.cancel(
            reason
        )

    ########################################################
    # CLEAR CANCELLATION
    ########################################################

    def clear_cancel(
        self,
    ) -> None:

        self.agent.clear_cancel()

    ########################################################
    # STATE
    ########################################################

    def is_cancelled(
        self,
    ) -> bool:

        return self.agent.is_cancelled()

    def __repr__(
        self,
    ):

        return (
            "<ComputerAgentExecutor "
            f"agent={self.agent.__class__.__name__!r}>"
        )