from __future__ import annotations

from typing import Any, Optional

from backend.task_orchestrator import (
    Task,
    TaskOrchestrator,
)

from automation.runtime_planner import (
    RuntimePlan,
)


class RuntimeTaskBridge:

    """
    Converts a RuntimePlan into a real TaskOrchestrator task.

    This bridge only translates planning structures into
    executable task structures.

    It does not execute the task.
    """

    def __init__(
        self,
        orchestrator: TaskOrchestrator,
    ):

        self.orchestrator = orchestrator

    ########################################################
    # BUILD TASK
    ########################################################

    def build_task(
        self,
        plan: RuntimePlan,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> Task:

        if plan is None:

            raise ValueError(
                "Runtime plan cannot be None."
            )

        intent = plan.intent

        if intent is None:

            raise ValueError(
                "Runtime plan does not contain an intent."
            )

        intent.validate()

        ####################################################
        # Create the actual orchestrator task.
        ####################################################

        task = (
            self.orchestrator.create_task(
                goal=intent.primary_goal,
                metadata={
                    "source": "RuntimeTaskBridge",
                    "request":
                        plan.request,
                    "planner_metadata":
                        dict(
                            plan.metadata
                        ),
                    **dict(
                        metadata or {}
                    ),
                },
            )
        )

        ####################################################
        # Map semantic subgoal IDs → runtime step IDs.
        ####################################################

        step_id_map: dict[
            str,
            str,
        ] = {}

        ####################################################
        # First pass:
        # create every step without dependencies.
        ####################################################

        for subgoal in (
            intent.subgoals
        ):

            executor = self._executor_for(
                subgoal.goal_type
            )

            step = (
                self.orchestrator.add_step(
                    task_id=task.task_id,
                    description=subgoal.description,
                    executor=executor,
                    dependencies=[],
                    metadata={
                        "subgoal_id":
                            subgoal.subgoal_id,

                        "goal_type":
                            subgoal.goal_type,

                        "priority":
                            subgoal.priority,

                        "constraints":
                            list(
                                subgoal.constraints
                            ),
                    },
                )
            )

            step_id_map[
                subgoal.subgoal_id
            ] = step.step_id

        ####################################################
        # Second pass:
        # translate subgoal dependencies into real step IDs.
        ####################################################

        for subgoal in (
            intent.subgoals
        ):

            step_id = step_id_map.get(
                subgoal.subgoal_id
            )

            if not step_id:

                continue

            step = task.get_step(
                step_id
            )

            if step is None:

                continue

            translated = []

            for dependency in (
                subgoal.dependencies
            ):

                runtime_id = step_id_map.get(
                    dependency
                )

                if (
                    runtime_id
                    and
                    runtime_id != step.step_id
                ):

                    translated.append(
                        runtime_id
                    )

            step.dependencies = list(
                dict.fromkeys(
                    translated
                )
            )

        ####################################################
        # Fallback for an empty semantic plan.
        ####################################################

        if not task.steps:

            step = (
                self.orchestrator.add_step(
                    task_id=task.task_id,
                    description=intent.primary_goal,
                    executor=(
                        "COMPUTER_AGENT"
                    ),
                    dependencies=[],
                    metadata={
                        "fallback":
                            True,
                    },
                )
            )

            step_id_map[
                "fallback"
            ] = step.step_id

        ####################################################
        # Store the mapping for later runtime inspection.
        ####################################################

        task.metadata[
            "subgoal_to_step"
        ] = dict(
            step_id_map
        )

        return task

    ########################################################
    # EXECUTOR MAPPING
    ########################################################

    @staticmethod
    def _executor_for(
        goal_type: str,
    ) -> str:

        goal_type = str(
            goal_type or ""
        ).strip().lower()

        if goal_type == "computer":

            return "COMPUTER_AGENT"

        ####################################################
        # Leave non-computer reasoning goals unassigned for
        # now. Phase 7.4+ will connect those to the appropriate
        # runtime capabilities.
        ####################################################

        return ""

    ########################################################
    # READY STEPS
    ########################################################

    def ready_steps(
        self,
        task: Task,
    ):

        return (
            self.orchestrator.ready_steps(
                task.task_id
            )
        )

    ########################################################
    # MAPPING
    ########################################################

    @staticmethod
    def mapping(
        task: Task,
    ) -> dict[str, str]:

        return dict(
            task.metadata.get(
                "subgoal_to_step",
                {}
            )
        )

    ########################################################
    # SNAPSHOT
    ########################################################

    def snapshot(
        self,
        task: Task,
    ) -> dict[str, Any]:

        return (
            self.orchestrator.task_snapshot(
                task.task_id
            )
            or {}
        )