from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


############################################################
# COMPUTER TASK STATUS
############################################################

class ComputerTaskStatus:

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


############################################################
# UNIVERSAL COMPUTER TASK CONTRACT
############################################################

@dataclass
class ComputerTaskContract:

    """
    Universal contract between JARVIS orchestration and the
    physical computer-use layer.

    This describes WHAT must be achieved.

    It does not describe HOW to achieve it.
    """

    task_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    goal: str = ""

    success_criteria: list[str] = field(
        default_factory=list
    )

    constraints: list[str] = field(
        default_factory=list
    )

    context: dict[str, Any] = field(
        default_factory=dict
    )

    requested_result: str = ""

    status: str = (
        ComputerTaskStatus.CREATED
    )

    created_at: str = field(
        default_factory=lambda:
            datetime.now().isoformat(
                timespec="seconds"
            )
    )

    started_at: Optional[str] = None

    completed_at: Optional[str] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    ########################################################
    # VALIDATION
    ########################################################

    def validate(
        self,
    ) -> None:

        if not str(
            self.goal or ""
        ).strip():

            raise ValueError(
                "Computer task goal cannot be empty."
            )

        self.goal = str(
            self.goal
        ).strip()

        self.success_criteria = [
            str(item).strip()
            for item in self.success_criteria
            if str(item).strip()
        ]

        self.constraints = [
            str(item).strip()
            for item in self.constraints
            if str(item).strip()
        ]

        self.requested_result = str(
            self.requested_result or ""
        ).strip()

    ########################################################
    # LIFECYCLE
    ########################################################

    def start(
        self,
    ) -> None:

        self.validate()

        self.status = (
            ComputerTaskStatus.RUNNING
        )

        self.started_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

    def complete(
        self,
        result: Any = None,
    ) -> None:

        self.status = (
            ComputerTaskStatus.COMPLETED
        )

        self.completed_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        self.metadata[
            "result"
        ] = result

    def fail(
        self,
        reason: str,
    ) -> None:

        self.status = (
            ComputerTaskStatus.FAILED
        )

        self.completed_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        self.metadata[
            "failure_reason"
        ] = str(
            reason or ""
        )

    def cancel(
        self,
        reason: str = "Task cancelled.",
    ) -> None:

        self.status = (
            ComputerTaskStatus.CANCELLED
        )

        self.completed_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        self.metadata[
            "cancel_reason"
        ] = str(
            reason or ""
        )

    ########################################################
    # SERIALIZATION
    ########################################################

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return asdict(
            self
        )


############################################################
# FACTORY
############################################################

def create_computer_task(
    goal: str,
    success_criteria: Optional[
        list[str]
    ] = None,
    constraints: Optional[
        list[str]
    ] = None,
    context: Optional[
        dict[str, Any]
    ] = None,
    requested_result: str = "",
    metadata: Optional[
        dict[str, Any]
    ] = None,
) -> ComputerTaskContract:

    task = ComputerTaskContract(
        goal=str(
            goal or ""
        ).strip(),

        success_criteria=list(
            success_criteria or []
        ),

        constraints=list(
            constraints or []
        ),

        context=dict(
            context or {}
        ),

        requested_result=str(
            requested_result or ""
        ).strip(),

        metadata=dict(
            metadata or {}
        ),
    )

    task.validate()

    return task