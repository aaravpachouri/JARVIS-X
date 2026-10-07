from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from automation.runtime_planner import (
    RuntimePlanner,
    RuntimePlan,
)

from automation.runtime_task_bridge import (
    RuntimeTaskBridge,
)

from automation.runtime_state import (
    RuntimeState,
    RuntimeStateSynchronizer,
)

from backend.task_orchestrator import (
    TaskOrchestrator,
)


############################################################
# END-TO-END RESULT
############################################################

@dataclass
class EndToEndResult:

    success: bool = False

    answer: str = ""

    task_id: Optional[str] = None

    state: Optional[
        RuntimeState
    ] = None

    plan: Optional[
        RuntimePlan
    ] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# END-TO-END RUNNER
############################################################

class EndToEndTaskRunner:

    """
    Connects the Phase 5 reasoning stack to the Phase 7
    runtime execution stack.

    This is the runtime coordinator.

    It does not replace:
        - AIBrain
        - TaskOrchestrator
        - ComputerUseAgent

    It connects them.
    """

    def __init__(
        self,
        brain,
        orchestrator: TaskOrchestrator,
    ):

        self.brain = brain

        self.orchestrator = (
            orchestrator
        )

        self.planner = RuntimePlanner(
            brain
        )

        self.bridge = RuntimeTaskBridge(
            orchestrator
        )

        self.state = (
            RuntimeStateSynchronizer()
        )

    ########################################################
    # RUN
    ########################################################

    def run(
        self,
        request: str,
        execution_id: int = 0,
    ) -> EndToEndResult:

        request = str(
            request or ""
        ).strip()

        if not request:

            return EndToEndResult(
                success=False,
                answer=(
                    "No request was provided."
                ),
            )

        ####################################################
        # PLAN
        ####################################################

        try:

            plan = self.planner.plan(
                request,
                mode="COMPUTER",
                context={
                    "execution_id":
                        execution_id,
                },
            )

        except Exception as exc:

            return EndToEndResult(
                success=False,
                answer=(
                    "I could not build a plan for "
                    f"that task: {exc}"
                ),
            )

        ####################################################
        # BUILD ORCHESTRATOR TASK
        ####################################################

        try:

            task = self.bridge.build_task(
                plan,
                metadata={
                    "execution_id":
                        execution_id,
                    "source":
                        "EndToEndTaskRunner",
                },
            )

        except Exception as exc:

            return EndToEndResult(
                success=False,
                answer=(
                    "I could not create the runtime task: "
                    f"{exc}"
                ),
                plan=plan,
            )

        ####################################################
        # START
        ####################################################

        if not self.orchestrator.start_task(
            task.task_id
        ):

            return EndToEndResult(
                success=False,
                answer=(
                    "I could not start the runtime task."
                ),
                task_id=task.task_id,
                plan=plan,
            )

        self.state.sync(
            self.orchestrator.task_snapshot(
                task.task_id
            ),
            execution_id,
        )

        ####################################################
        # EXECUTE READY STEPS
        #
        # We intentionally execute one ready step at a time.
        # ComputerUseAgent already performs its own internal
        # observe → action → verify loop.
        ####################################################

        while True:

            snapshot = (
                self.orchestrator.task_snapshot(
                    task.task_id
                )
            )

            if snapshot is None:

                return EndToEndResult(
                    success=False,
                    answer=(
                        "The runtime task disappeared "
                        "before completion."
                    ),
                    task_id=task.task_id,
                    plan=plan,
                    state=self.state.state,
                )

            self.state.sync(
                snapshot,
                execution_id,
            )

            ################################################
            # Terminal state
            ################################################

            status = str(
                snapshot.get(
                    "status",
                    "",
                )
                or ""
            ).upper()

            if status == "CANCELLED":

                return EndToEndResult(
                    success=False,
                    answer=(
                        "The task was cancelled."
                    ),
                    task_id=task.task_id,
                    plan=plan,
                    state=self.state.state,
                )

            ################################################
            # Failure
            ################################################

            if status == "FAILED":

                return EndToEndResult(
                    success=False,
                    answer=(
                        snapshot.get(
                            "error",
                            "",
                        )
                        or
                        "The task failed."
                    ),
                    task_id=task.task_id,
                    plan=plan,
                    state=self.state.state,
                )

            ################################################
            # Already complete
            ################################################

            if status == "COMPLETED":

                return EndToEndResult(
                    success=True,
                    answer=str(
                        snapshot.get(
                            "result",
                            "",
                        )
                        or
                        "The task is complete."
                    ),
                    task_id=task.task_id,
                    plan=plan,
                    state=self.state.state,
                )

            ################################################
            # Find the next executable step.
            ################################################

            ready = (
                self.orchestrator.ready_steps(
                    task.task_id
                )
            )

            if not ready:

                ################################################
                # No ready steps but not terminal means the
                # plan is not executable in its current form.
                ################################################

                self.orchestrator.fail_task(
                    task.task_id,
                    (
                        "No ready executable step remains "
                        "for the current plan."
                    ),
                )

                continue

            step = ready[0]

            ################################################
            # Current runtime context
            ################################################

            context = {
                "execution_id":
                    execution_id,

                "runtime_state":
                    self.state.reasoning_context(),

                "plan":
                    plan.metadata,

                "subgoal_id":
                    step.metadata.get(
                        "subgoal_id"
                    ),

                "constraints":
                    list(
                        step.metadata.get(
                            "constraints",
                            [],
                        )
                        or []
                    ),
            }

            ################################################
            # Execute
            ################################################

            result = (
                self.orchestrator.execute_step(
                    task_id=task.task_id,
                    step_id=step.step_id,
                    context=context,
                )
            )

            ################################################
            # Re-sync after execution.
            ################################################

            snapshot = (
                self.orchestrator.task_snapshot(
                    task.task_id
                )
            )

            self.state.sync(
                snapshot,
                execution_id,
            )

            ################################################
            # Step failure
            ################################################

            if not result.success:

                if not self.orchestrator.active_task():

                    return EndToEndResult(
                        success=False,
                        answer=(
                            result.error
                            or
                            "The task failed."
                        ),
                        task_id=task.task_id,
                        plan=plan,
                        state=self.state.state,
                    )

                continue

            ################################################
            # If all steps are now complete, explicitly
            # complete the orchestrator task.
            ################################################

            remaining = (
                self.orchestrator.ready_steps(
                    task.task_id
                )
            )

            snapshot = (
                self.orchestrator.task_snapshot(
                    task.task_id
                )
            )

            if snapshot is None:

                break

            all_terminal = all(
                str(
                    item.get(
                        "status",
                        "",
                    )
                    or ""
                ).upper()
                in {
                    "COMPLETED",
                    "SKIPPED",
                }
                for item in (
                    snapshot.get(
                        "steps",
                        [],
                    )
                    or []
                )
            )

            if all_terminal:

                self.orchestrator.complete_task(
                    task.task_id,
                    result.result,
                )

                break

            ################################################
            # Prevent unused-variable warnings while keeping
            # the state transition explicit.
            ################################################

            _ = remaining

        ####################################################
        # FINAL STATE
        ####################################################

        snapshot = (
            self.orchestrator.task_snapshot(
                task.task_id
            )
        )

        self.state.sync(
            snapshot,
            execution_id,
        )

        if snapshot and str(
            snapshot.get(
                "status",
                "",
            )
            or ""
        ).upper() == "COMPLETED":

            return EndToEndResult(
                success=True,
                answer=str(
                    snapshot.get(
                        "result",
                        "",
                    )
                    or
                    "The task completed successfully."
                ),
                task_id=task.task_id,
                plan=plan,
                state=self.state.state,
            )

        return EndToEndResult(
            success=False,
            answer=(
                snapshot.get(
                    "error",
                    "",
                )
                if snapshot
                else
                "The task did not reach a completed state."
            ),
            task_id=task.task_id,
            plan=plan,
            state=self.state.state,
        )