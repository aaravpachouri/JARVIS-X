from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


############################################################
# MULTI-APPLICATION WORKFLOW CONTEXT
############################################################


@dataclass
class WorkflowStage:

    name: str

    application: str = ""

    objective: str = ""

    status: str = "PENDING"

    started_at: Optional[float] = None

    completed_at: Optional[float] = None

    result: Any = None

    error: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def start(
        self,
    ):

        self.status = "RUNNING"

        self.started_at = (
            time.monotonic()
        )

        self.error = ""

    def complete(
        self,
        result: Any = None,
    ):

        self.status = "COMPLETED"

        self.completed_at = (
            time.monotonic()
        )

        self.result = result

    def fail(
        self,
        error: str,
    ):

        self.status = "FAILED"

        self.completed_at = (
            time.monotonic()
        )

        self.error = str(
            error
            or
            ""
        )

    def cancel(
        self,
        reason: str = "",
    ):

        self.status = "CANCELLED"

        self.completed_at = (
            time.monotonic()
        )

        self.error = str(
            reason
            or
            "Workflow cancelled."
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                self.name,

            "application":
                self.application,

            "objective":
                self.objective,

            "status":
                self.status,

            "started_at":
                self.started_at,

            "completed_at":
                self.completed_at,

            "result":
                self.result,

            "error":
                self.error,

            "metadata":
                dict(
                    self.metadata
                ),
        }


class MultiAppWorkflowContext:

    """
    Runtime context for multi-application computer workflows.

    Example:

        Chrome
          ↓
        download file
          ↓
        File Explorer
          ↓
        move file
          ↓
        Word
          ↓
        create document
          ↓
        save

    This class tracks the workflow and application transitions.
    It does not execute computer actions itself.

    ComputerUseAgent remains the decision/execution authority.
    """

    MAX_HISTORY = 100

    def __init__(
        self,
        goal: str = "",
    ):

        self.workflow_id = str(
            uuid.uuid4()
        )

        self.goal = str(
            goal
            or
            ""
        ).strip()

        self.status = "IDLE"

        self.created_at = (
            time.monotonic()
        )

        self.updated_at = (
            self.created_at
        )

        self.stages: list[
            WorkflowStage
        ] = []

        self.current_index = -1

        self.active_application = ""

        self.previous_application = ""

        self.application_history: list[
            dict[str, Any]
        ] = []

        self.variables: dict[
            str,
            Any
        ] = {}

        self.artifacts: dict[
            str,
            Any
        ] = {}

        self.history: list[
            dict[str, Any]
        ] = []

        self.cancel_requested = False

        self.cancel_reason = ""

    ############################################################
    # WORKFLOW
    ############################################################

    def start(
        self,
    ):

        self.status = "RUNNING"

        self.updated_at = (
            time.monotonic()
        )

    def complete(
        self,
    ):

        self.status = "COMPLETED"

        self.updated_at = (
            time.monotonic()
        )

    def fail(
        self,
        reason: str,
    ):

        self.status = "FAILED"

        self.updated_at = (
            time.monotonic()
        )

        self.record(
            "workflow_failed",
            {
                "reason":
                    str(
                        reason
                    )
            }
        )

    def request_cancel(
        self,
        reason: str = "Workflow cancelled by user.",
    ):

        self.cancel_requested = True

        self.cancel_reason = str(
            reason
            or
            "Workflow cancelled by user."
        )

        self.status = "CANCELLING"

        self.updated_at = (
            time.monotonic()
        )

        self.record(
            "cancel_requested",
            {
                "reason":
                    self.cancel_reason
            }
        )

    def is_cancelled(
        self,
    ) -> bool:

        return bool(
            self.cancel_requested
        )

    ############################################################
    # STAGES
    ############################################################

    def add_stage(
        self,
        name: str,
        application: str = "",
        objective: str = "",
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> WorkflowStage:

        stage = WorkflowStage(
            name=str(
                name
                or
                ""
            ).strip(),

            application=str(
                application
                or
                ""
            ).strip(),

            objective=str(
                objective
                or
                ""
            ).strip(),

            metadata=dict(
                metadata
                or
                {}
            ),
        )

        self.stages.append(
            stage
        )

        self.updated_at = (
            time.monotonic()
        )

        self.record(
            "stage_added",
            {
                "stage":
                    stage.name,

                "application":
                    stage.application,
            }
        )

        return stage

    def current_stage(
        self,
    ) -> Optional[WorkflowStage]:

        if (
            self.current_index < 0
            or
            self.current_index >= len(
                self.stages
            )
        ):

            return None

        return self.stages[
            self.current_index
        ]

    def start_next_stage(
        self,
    ) -> Optional[WorkflowStage]:

        if self.cancel_requested:

            return None

        next_index = (
            self.current_index
            +
            1
        )

        if next_index >= len(
            self.stages
        ):

            return None

        self.current_index = (
            next_index
        )

        stage = self.stages[
            self.current_index
        ]

        stage.start()

        self.updated_at = (
            time.monotonic()
        )

        if stage.application:

            self.switch_application(
                stage.application
            )

        self.record(
            "stage_started",
            {
                "stage":
                    stage.name,

                "application":
                    stage.application,
            }
        )

        return stage

    def complete_current_stage(
        self,
        result: Any = None,
    ) -> Optional[WorkflowStage]:

        stage = (
            self.current_stage()
        )

        if stage is None:
            return None

        stage.complete(
            result
        )

        self.updated_at = (
            time.monotonic()
        )

        self.record(
            "stage_completed",
            {
                "stage":
                    stage.name,

                "application":
                    stage.application,
            }
        )

        return stage

    def fail_current_stage(
        self,
        error: str,
    ) -> Optional[WorkflowStage]:

        stage = (
            self.current_stage()
        )

        if stage is None:
            return None

        stage.fail(
            error
        )

        self.status = "FAILED"

        self.updated_at = (
            time.monotonic()
        )

        self.record(
            "stage_failed",
            {
                "stage":
                    stage.name,

                "error":
                    str(
                        error
                    ),
            }
        )

        return stage

    def has_more_stages(
        self,
    ) -> bool:

        return (
            self.current_index
            +
            1
            <
            len(
                self.stages
            )
        )

    ############################################################
    # APPLICATION TRANSITIONS
    ############################################################

    def switch_application(
        self,
        application: str,
    ):

        application = str(
            application
            or
            ""
        ).strip()

        if not application:
            return

        if (
            self.active_application
            ==
            application
        ):

            return

        self.previous_application = (
            self.active_application
        )

        self.active_application = (
            application
        )

        transition = {
            "from":
                self.previous_application,

            "to":
                self.active_application,

            "timestamp":
                time.monotonic(),
        }

        self.application_history.append(
            transition
        )

        self.record(
            "application_switch",
            transition,
        )

    ############################################################
    # VARIABLES / ARTIFACTS
    ############################################################

    def set_variable(
        self,
        name: str,
        value: Any,
    ):

        key = str(
            name
            or
            ""
        ).strip()

        if not key:
            return

        self.variables[
            key
        ] = value

        self.updated_at = (
            time.monotonic()
        )

    def get_variable(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        return self.variables.get(
            str(
                name
                or
                ""
            ).strip(),
            default,
        )

    def add_artifact(
        self,
        name: str,
        value: Any,
    ):

        key = str(
            name
            or
            ""
        ).strip()

        if not key:
            return

        self.artifacts[
            key
        ] = value

        self.updated_at = (
            time.monotonic()
        )

        self.record(
            "artifact_added",
            {
                "name":
                    key
            }
        )

    ############################################################
    # HISTORY
    ############################################################

    def record(
        self,
        event: str,
        data: Optional[
            dict[str, Any]
        ] = None,
    ):

        self.history.append(
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
            self.history
        ) > self.MAX_HISTORY:

            del self.history[
                :-
                self.MAX_HISTORY
            ]

    ############################################################
    # CONTEXT
    ############################################################

    def compact_context(
        self,
    ) -> dict[str, Any]:

        current = (
            self.current_stage()
        )

        return {
            "workflow_id":
                self.workflow_id,

            "goal":
                self.goal,

            "status":
                self.status,

            "current_application":
                self.active_application,

            "previous_application":
                self.previous_application,

            "current_stage":
                (
                    current.name
                    if current
                    else
                    ""
                ),

            "current_stage_status":
                (
                    current.status
                    if current
                    else
                    ""
                ),

            "stage_index":
                self.current_index,

            "stage_count":
                len(
                    self.stages
                ),

            "variables":
                dict(
                    self.variables
                ),

            "artifacts":
                dict(
                    self.artifacts
                ),

            "cancel_requested":
                self.cancel_requested,
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            **self.compact_context(),

            "stages":
                [
                    stage.to_dict()
                    for stage
                    in self.stages
                ],

            "application_history":
                list(
                    self.application_history
                ),

            "history":
                list(
                    self.history[
                        -20:
                    ]
                ),
        }


def create_workflow(
    goal: str,
) -> MultiAppWorkflowContext:

    workflow = (
        MultiAppWorkflowContext(
            goal
        )
    )

    workflow.start()

    return workflow