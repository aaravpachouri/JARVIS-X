from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


############################################################
# RUNTIME STATE
############################################################

@dataclass
class RuntimeState:

    """
    Single runtime-facing view of the current JARVIS task.

    The TaskOrchestrator remains the source of truth for task
    execution. This object provides a stable state representation
    for AIController, UI, voice, logging, and later integrations.
    """

    execution_id: int = 0

    task_id: Optional[str] = None

    goal: str = ""

    status: str = "IDLE"

    current_step_id: Optional[str] = None

    current_step: str = ""

    completed_steps: int = 0

    total_steps: int = 0

    progress: float = 0.0

    result: Any = None

    error: str = ""

    cancelled: bool = False

    interrupt_requested: bool = False

    interrupt_reason: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    updated_at: str = field(
        default_factory=lambda:
            datetime.now().isoformat(
                timespec="seconds"
            )
    )


############################################################
# RUNTIME STATE SYNCHRONIZER
############################################################

class RuntimeStateSynchronizer:

    """
    Converts TaskOrchestrator snapshots into a compact,
    runtime-safe RuntimeState.

    The synchronizer never changes task state.
    """

    def __init__(self):

        self.state = RuntimeState()

    ########################################################
    # SYNC
    ########################################################

    def sync(
        self,
        snapshot: Optional[
            dict[str, Any]
        ],
        execution_id: int = 0,
    ) -> RuntimeState:

        if not snapshot:

            self.state = RuntimeState(
                execution_id=int(
                    execution_id
                ),
                updated_at=self._now(),
            )

            return self.state

        steps = snapshot.get(
            "steps",
            [],
        )

        if not isinstance(
            steps,
            list,
        ):

            steps = []

        completed = []

        current_step = None

        for step in steps:

            if not isinstance(
                step,
                dict,
            ):

                continue

            status = str(
                step.get(
                    "status",
                    "",
                )
                or ""
            ).upper()

            if status == "COMPLETED":

                completed.append(
                    step
                )

            if (
                step.get(
                    "step_id"
                )
                ==
                snapshot.get(
                    "current_step_id"
                )
            ):

                current_step = step

        total = len(
            steps
        )

        progress = (
            len(completed)
            /
            total
            if total
            else 0.0
        )

        recovery = snapshot.get(
            "recovery",
            {}
        )

        if not isinstance(
            recovery,
            dict,
        ):

            recovery = {}

        interrupt_requested = bool(
            snapshot.get(
                "interrupt_requested",
                False,
            )
        )

        interrupt_reason = str(
            snapshot.get(
                "interrupt_reason",
                "",
            )
            or ""
        )

        self.state = RuntimeState(
            execution_id=int(
                execution_id
            ),

            task_id=snapshot.get(
                "task_id"
            ),

            goal=str(
                snapshot.get(
                    "goal",
                    "",
                )
                or ""
            ),

            status=str(
                snapshot.get(
                    "status",
                    "IDLE",
                )
                or "IDLE"
            ),

            current_step_id=snapshot.get(
                "current_step_id"
            ),

            current_step=str(
                (
                    current_step or {}
                ).get(
                    "description",
                    "",
                )
                or ""
            ),

            completed_steps=len(
                completed
            ),

            total_steps=total,

            progress=round(
                progress,
                3,
            ),

            result=snapshot.get(
                "result"
            ),

            error=str(
                snapshot.get(
                    "error",
                    "",
                )
                or ""
            ),

            cancelled=bool(
                snapshot.get(
                    "cancelled",
                    False,
                )
            ),

            interrupt_requested=(
                interrupt_requested
            ),

            interrupt_reason=(
                interrupt_reason
            ),

            metadata={
                "registered_executors":
                    list(
                        snapshot.get(
                            "registered_executors",
                            [],
                        )
                        or []
                    ),

                "registered_verifiers":
                    list(
                        snapshot.get(
                            "registered_verifiers",
                            [],
                        )
                        or []
                    ),

                "recovery":
                    dict(
                        recovery
                    ),

                "replanning_available":
                    bool(
                        snapshot.get(
                            "replanning_available",
                            False,
                        )
                    ),
            },

            updated_at=self._now(),
        )

        return self.state

    ########################################################
    # CLEAR
    ########################################################

    def clear(
        self,
        execution_id: int = 0,
    ) -> RuntimeState:

        self.state = RuntimeState(
            execution_id=int(
                execution_id
            ),
            updated_at=self._now(),
        )

        return self.state

    ########################################################
    # SNAPSHOT
    ########################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "execution_id":
                self.state.execution_id,

            "task_id":
                self.state.task_id,

            "goal":
                self.state.goal,

            "status":
                self.state.status,

            "current_step_id":
                self.state.current_step_id,

            "current_step":
                self.state.current_step,

            "completed_steps":
                self.state.completed_steps,

            "total_steps":
                self.state.total_steps,

            "progress":
                self.state.progress,

            "result":
                self.state.result,

            "error":
                self.state.error,

            "cancelled":
                self.state.cancelled,

            "interrupt_requested":
                self.state.interrupt_requested,

            "interrupt_reason":
                self.state.interrupt_reason,

            "metadata":
                dict(
                    self.state.metadata
                ),

            "updated_at":
                self.state.updated_at,
        }

    ########################################################
    # CONTEXT
    ########################################################

    def reasoning_context(
        self,
    ) -> dict[str, Any]:

        return {
            "task_id":
                self.state.task_id,

            "goal":
                self.state.goal,

            "status":
                self.state.status,

            "current_step":
                self.state.current_step,

            "progress":
                self.state.progress,

            "completed_steps":
                self.state.completed_steps,

            "total_steps":
                self.state.total_steps,

            "error":
                self.state.error,

            "cancelled":
                self.state.cancelled,

            "interrupt_requested":
                self.state.interrupt_requested,

            "recovery":
                dict(
                    self.state.metadata.get(
                        "recovery",
                        {}
                    )
                    or {}
                ),
        }

    ########################################################
    # TIME
    ########################################################

    @staticmethod
    def _now() -> str:

        return datetime.now().isoformat(
            timespec="seconds"
        )


############################################################
# STATUS HELPERS
############################################################

def is_active(
    state: RuntimeState,
) -> bool:

    return state.status in {
        "CREATED",
        "PLANNING",
        "READY",
        "RUNNING",
        "PAUSED",
    }


def is_terminal(
    state: RuntimeState,
) -> bool:

    return state.status in {
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    }