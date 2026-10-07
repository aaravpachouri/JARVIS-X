from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AgentState:
    """
    JARVIS X
    CENTRAL AUTONOMOUS TASK STATE

    This object is the single source of truth for the current
    computer-use task.

    Existing functionality is preserved:
        - goal
        - step
        - status
        - history
        - records
        - artifacts
        - variables
        - errors
        - start()
        - add_history()
        - add_record()
        - add_artifact()
        - fail()
        - complete()
        - snapshot()

    Additional state is added for:
        - multi-stage tasks
        - last executed action
        - last execution result
        - task completion timestamp
        - autonomous execution limits
    """

    # ==================================================
    # CORE TASK STATE
    # ==================================================

    goal: str = ""

    step: int = 0

    status: str = "idle"

    max_steps: int = 60

    # ==================================================
    # TASK STAGES
    # ==================================================

    current_stage: int = 0

    stages: list[str] = field(
        default_factory=list
    )

    # ==================================================
    # EXECUTION HISTORY
    # ==================================================

    history: list[dict[str, Any]] = field(
        default_factory=list
    )

    # ==================================================
    # GENERAL RECORDS
    # ==================================================

    records: list[dict[str, Any]] = field(
        default_factory=list
    )

    # ==================================================
    # CREATED / GENERATED ARTIFACTS
    # ==================================================

    artifacts: list[str] = field(
        default_factory=list
    )

    # ==================================================
    # PERSISTENT TASK VARIABLES
    # ==================================================

    variables: dict[str, Any] = field(
        default_factory=dict
    )

    # ==================================================
    # ERRORS
    # ==================================================

    errors: list[str] = field(
        default_factory=list
    )

    # ==================================================
    # LAST ACTION
    # ==================================================

    last_action: dict[str, Any] | None = None

    last_result: dict[str, Any] | None = None

    # ==================================================
    # TIMESTAMPS
    # ==================================================

    started_at: str | None = None

    completed_at: str | None = None

    # ==================================================
    # TASK START
    # ==================================================

    def start(
        self,
        goal: str
    ):
        """
        Start a completely new autonomous task.

        Existing behavior is preserved: all task-specific
        history, records, variables, artifacts and errors are
        cleared before a new goal begins.
        """

        self.goal = str(
            goal or ""
        ).strip()

        self.step = 0

        self.status = "running"

        self.current_stage = 0

        self.stages.clear()

        self.history.clear()

        self.records.clear()

        self.artifacts.clear()

        self.variables.clear()

        self.errors.clear()

        self.last_action = None

        self.last_result = None

        self.started_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        self.completed_at = None

    # ==================================================
    # STAGES
    # ==================================================

    def set_stages(
        self,
        stages
    ):
        """
        Store the planner's stages.

        Stages are descriptive only. They do not execute
        actions themselves.
        """

        if not isinstance(
            stages,
            list
        ):
            stages = []

        self.stages = [
            str(stage).strip()
            for stage in stages
            if str(stage).strip()
        ]

        self.current_stage = 0

    # ==================================================

    def startStage(
        self
    ):
        """
        Return the current stage.

        Kept in camelCase for compatibility with the
        existing ComputerUseAgent architecture.
        """

        if not self.stages:
            self.current_stage = 0
            return None

        self.current_stage = max(
            0,
            min(
                self.current_stage,
                len(self.stages) - 1
            )
        )

        return self.stages[
            self.current_stage
        ]

    # ==================================================

    def currentStage(
        self
    ):
        """
        Return the current stage name.
        """

        if not self.stages:
            return ""

        if (
            self.current_stage < 0
            or
            self.current_stage >= len(
                self.stages
            )
        ):
            return ""

        return self.stages[
            self.current_stage
        ]

    # ==================================================

    def advanceStage(
        self
    ):
        """
        Move to the next task stage.

        Returns:
            True  -> stage changed
            False -> already at final stage / no stages
        """

        if not self.stages:
            return False

        if (
            self.current_stage
            >= len(self.stages) - 1
        ):
            return False

        self.current_stage += 1

        return True

    # ==================================================

    def hasMoreStages(
        self
    ):
        """
        Check whether another stage remains after the
        current stage.
        """

        if not self.stages:
            return False

        return (
            self.current_stage
            < len(self.stages) - 1
        )

    # ==================================================
    # HISTORY
    # ==================================================

    def add_history(
        self,
        item
    ):
        """
        Add one execution event to task history.
        """

        if not isinstance(
            item,
            dict
        ):
            return

        self.history.append(
            dict(item)
        )

        # Keep enough history for autonomous recovery
        # without allowing unbounded memory growth.
        if len(
            self.history
        ) > 50:

            del self.history[:-50]

    # ==================================================

    def recent_history(
        self,
        count=10
    ):
        """
        Return the most recent execution history.
        """

        try:
            count = max(
                1,
                int(count)
            )
        except Exception:
            count = 10

        return self.history[
            -count:
        ]

    # ==================================================
    # RECORDS
    # ==================================================

    def add_record(
        self,
        record
    ):
        """
        Store a general-purpose task record.
        """

        if not isinstance(
            record,
            dict
        ):
            return

        self.records.append(
            dict(record)
        )

        if len(
            self.records
        ) > 100:

            del self.records[:-100]

    # ==================================================

    def recent_records(
        self,
        count=20
    ):
        """
        Return recent general-purpose records.
        """

        try:
            count = max(
                1,
                int(count)
            )
        except Exception:
            count = 20

        return self.records[
            -count:
        ]

    # ==================================================
    # ARTIFACTS
    # ==================================================

    def add_artifact(
        self,
        path
    ):
        """
        Register a file or other generated artifact.
        """

        path = str(
            path or ""
        ).strip()

        if (
            path
            and
            path not in self.artifacts
        ):
            self.artifacts.append(
                path
            )

    # ==================================================

    def has_artifact(
        self,
        path
    ):
        path = str(
            path or ""
        ).strip()

        return (
            path in self.artifacts
        )

    # ==================================================
    # VARIABLES
    # ==================================================

    def remember(
        self,
        key,
        value
    ):
        """
        Store a task variable.

        This allows information discovered during one step
        to survive into later steps.
        """

        key = str(
            key or ""
        ).strip()

        if not key:
            return

        self.variables[
            key
        ] = value

    # ==================================================

    def get_variable(
        self,
        key,
        default=None
    ):
        return self.variables.get(
            str(key),
            default
        )

    # ==================================================
    # ACTION TRACKING
    # ==================================================

    def set_action(
        self,
        action
    ):
        """
        Store the most recently attempted action.
        """

        if isinstance(
            action,
            dict
        ):
            self.last_action = dict(
                action
            )
        else:
            self.last_action = action

    # ==================================================

    def set_result(
        self,
        result
    ):
        """
        Store the result of the most recently attempted
        action.
        """

        if isinstance(
            result,
            dict
        ):
            self.last_result = dict(
                result
            )
        else:
            self.last_result = result

    # ==================================================

    def set_action_result(
        self,
        action,
        result
    ):
        """
        Convenience method used after an action executes.
        """

        self.set_action(
            action
        )

        self.set_result(
            result
        )

    # ==================================================
    # FAILURE
    # ==================================================

    def fail(
        self,
        message
    ):
        """
        Mark the current task as failed while preserving
        the error history.
        """

        self.status = "failed"

        self.errors.append(
            str(message)
        )

        if len(
            self.errors
        ) > 20:

            del self.errors[:-20]

    # ==================================================

    def clear_errors(
        self
    ):
        self.errors.clear()

    # ==================================================
    # COMPLETE
    # ==================================================

    def complete(
        self
    ):
        """
        Mark the current autonomous task as completed.
        """

        self.status = "completed"

        self.completed_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

    # ==================================================
    # CANCEL
    # ==================================================

    def cancel(
        self,
        reason="Task cancelled."
    ):
        """
        Explicitly stop the current task without treating
        the cancellation as an execution error.
        """

        self.status = "cancelled"

        if reason:
            self.errors.append(
                str(reason)
            )

    # ==================================================
    # RUNNING
    # ==================================================

    def is_running(
        self
    ):
        return (
            self.status == "running"
        )

    # ==================================================

    def is_complete(
        self
    ):
        return (
            self.status == "completed"
        )

    # ==================================================

    def is_failed(
        self
    ):
        return (
            self.status == "failed"
        )

    # ==================================================
    # STEP
    # ==================================================

    def set_step(
        self,
        step
    ):
        """
        Safely update the autonomous execution step.
        """

        try:
            self.step = max(
                0,
                int(step)
            )
        except Exception:
            return

    # ==================================================

    def increment_step(
        self
    ):
        self.step += 1

        return self.step

    # ==================================================
    # SNAPSHOT
    # ==================================================

    def snapshot(
        self
    ):
        """
        Return a serializable representation of the complete
        current task state.

        This is consumed by AgentMemory and supplied back to
        the local reasoning model.
        """

        return {
            "goal":
                self.goal,

            "status":
                self.status,

            "step":
                self.step,

            "max_steps":
                self.max_steps,

            "current_stage":
                self.current_stage,

            "current_stage_name":
                self.currentStage(),

            "stages":
                list(
                    self.stages
                ),

            "history":
                self.history[-12:],

            "records":
                self.records[-20:],

            "artifacts":
                list(
                    self.artifacts
                ),

            "variables":
                dict(
                    self.variables
                ),

            "errors":
                self.errors[-5:],

            "last_action":
                self.last_action,

            "last_result":
                self.last_result,

            "started_at":
                self.started_at,

            "completed_at":
                self.completed_at,
        }

    # ==================================================
    # DEBUG REPRESENTATION
    # ==================================================

    def __repr__(
        self
    ):
        return (
            "<AgentState "
            f"status={self.status!r} "
            f"step={self.step} "
            f"stage={self.current_stage} "
            f"goal={self.goal!r}>"
        )