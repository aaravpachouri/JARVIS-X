from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from backend.task_verifier import TaskVerificationEngine
from backend.task_recovery import TaskRecoveryCoordinator
from backend.task_replanner import TaskReplanner, ReplanResult
from backend.task_interrupt import TaskInterruptController


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


@dataclass
class StepResult:
    success: bool = False
    result: Any = None
    error: str = ""
    verification: str = ""
    executor: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskStep:

    step_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    description: str = ""
    executor: str = ""
    status: StepStatus = StepStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    error: str = ""
    verification: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda:
            datetime.now().isoformat(timespec="seconds")
    )
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def add_dependency(self, step_id: str):
        step_id = str(step_id or "").strip()
        if not step_id:
            return
        if step_id == self.step_id:
            raise ValueError(
                "A step cannot depend on itself."
            )
        if step_id not in self.dependencies:
            self.dependencies.append(step_id)

    def mark_ready(self):
        self.status = StepStatus.READY

    def mark_running(self):
        self.status = StepStatus.RUNNING
        self.started_at = datetime.now().isoformat(
            timespec="seconds"
        )

    def mark_completed(
        self,
        result: Any = None,
        verification: str = "",
    ):
        self.status = StepStatus.COMPLETED
        self.result = result
        self.verification = str(verification or "")
        self.completed_at = datetime.now().isoformat(
            timespec="seconds"
        )

    def mark_failed(self, error: str):
        self.status = StepStatus.FAILED
        self.error = str(error or "")
        self.completed_at = datetime.now().isoformat(
            timespec="seconds"
        )

    def mark_cancelled(self, reason: str = ""):
        self.status = StepStatus.CANCELLED
        self.error = str(reason or "")
        self.completed_at = datetime.now().isoformat(
            timespec="seconds"
        )

    def is_terminal(self) -> bool:
        return self.status in {
            StepStatus.COMPLETED,
            StepStatus.FAILED,
            StepStatus.SKIPPED,
            StepStatus.CANCELLED,
        }

    def is_successful(self) -> bool:
        return self.status == StepStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class Task:

    task_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    goal: str = ""
    status: TaskStatus = TaskStatus.CREATED
    steps: list[TaskStep] = field(default_factory=list)
    current_step_id: Optional[str] = None
    result: Any = None
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda:
            datetime.now().isoformat(timespec="seconds")
    )
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancelled: bool = False

    def add_step(
        self,
        description: str,
        executor: str = "",
        dependencies: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TaskStep:

        step = TaskStep(
            description=str(description or "").strip(),
            executor=str(executor or "").strip(),
            dependencies=list(dependencies or []),
            metadata=dict(metadata or {}),
        )

        if not step.description:
            raise ValueError(
                "Task step description cannot be empty."
            )

        self.steps.append(step)
        self.status = TaskStatus.READY
        return step

    def get_step(
        self,
        step_id: str,
    ) -> Optional[TaskStep]:

        step_id = str(step_id or "").strip()

        for step in self.steps:
            if step.step_id == step_id:
                return step

        return None

    def ready_steps(self) -> list[TaskStep]:

        completed_ids = {
            step.step_id
            for step in self.steps
            if step.status == StepStatus.COMPLETED
        }

        ready = []

        for step in self.steps:

            if step.status not in {
                StepStatus.PENDING,
                StepStatus.READY,
            }:
                continue

            if all(
                dependency_id in completed_ids
                for dependency_id in step.dependencies
            ):
                step.mark_ready()
                ready.append(step)

        return ready

    def start(self):

        if self.cancelled:
            raise RuntimeError(
                "Cannot start a cancelled task."
            )

        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().isoformat(
            timespec="seconds"
        )

    def complete(self, result: Any = None):
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.current_step_id = None
        self.completed_at = datetime.now().isoformat(
            timespec="seconds"
        )

    def fail(self, error: str):
        self.status = TaskStatus.FAILED
        self.error = str(error or "")
        self.current_step_id = None
        self.completed_at = datetime.now().isoformat(
            timespec="seconds"
        )

    def cancel(self, reason: str = ""):

        self.cancelled = True
        self.status = TaskStatus.CANCELLED
        self.error = str(reason or "")

        for step in self.steps:
            if not step.is_terminal():
                step.mark_cancelled(reason)

        self.current_step_id = None
        self.completed_at = datetime.now().isoformat(
            timespec="seconds"
        )

    def is_complete(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def is_cancelled(self) -> bool:
        return (
            self.status == TaskStatus.CANCELLED
            or self.cancelled
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status.value,
            "steps": [
                step.to_dict() for step in self.steps
            ],
            "current_step_id": self.current_step_id,
            "result": self.result,
            "error": self.error,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "cancelled": self.cancelled,
        }


class TaskExecutor:

    name = "executor"

    def can_execute(self, step: TaskStep) -> bool:
        return False

    def execute(
        self,
        step: TaskStep,
        context: Optional[dict[str, Any]] = None,
    ) -> StepResult:

        return StepResult(
            success=False,
            error=(
                f"Executor '{self.name}' "
                "does not implement execution."
            ),
            executor=self.name,
        )


class FunctionTaskExecutor(TaskExecutor):

    def __init__(
        self,
        name: str,
        execute,
        can_execute=None,
    ):

        self.name = str(name or "executor").strip()
        self._execute = execute
        self._can_execute = can_execute

    def can_execute(self, step: TaskStep) -> bool:

        if self._can_execute is None:
            return step.executor == self.name

        try:
            return bool(self._can_execute(step))
        except Exception as exc:
            print(
                f"[Orchestrator] "
                f"{self.name}.can_execute error:",
                exc,
            )
            return False

    def execute(
        self,
        step: TaskStep,
        context: Optional[dict[str, Any]] = None,
    ) -> StepResult:

        try:
            result = self._execute(
                step,
                dict(context or {}),
            )

            if isinstance(result, StepResult):

                if not result.executor:
                    result.executor = self.name

                return result

            return StepResult(
                success=True,
                result=result,
                executor=self.name,
            )

        except Exception as exc:

            return StepResult(
                success=False,
                error=str(exc),
                executor=self.name,
            )


class TaskOrchestrator:

    def __init__(
        self,
        verifier: Optional[
            TaskVerificationEngine
        ] = None,
    ):

        self.tasks: dict[str, Task] = {}
        self.executors: dict[str, TaskExecutor] = {}
        self.active_task_id: Optional[str] = None
        self.cancelled_task_ids: set[str] = set()

        self.verifier = (
            verifier
            if verifier is not None
            else TaskVerificationEngine()
        )

        self.recovery = TaskRecoveryCoordinator()
        self.replanner = TaskReplanner()

        self.interrupt = TaskInterruptController()

    def register_executor(
        self,
        executor: TaskExecutor,
    ) -> TaskExecutor:

        if not isinstance(
            executor,
            TaskExecutor,
        ):
            raise TypeError(
                "register_executor() requires a TaskExecutor."
            )

        self.executors[executor.name] = executor

        print(
            "[Orchestrator] "
            f"Registered executor: {executor.name}"
        )

        return executor

    def unregister_executor(
        self,
        name: str,
    ) -> bool:

        name = str(name or "").strip()

        if name not in self.executors:
            return False

        del self.executors[name]
        return True

    def get_executor(
        self,
        name: str,
    ) -> Optional[TaskExecutor]:

        return self.executors.get(
            str(name or "").strip()
        )

    def register_verifier(
        self,
        executor_name: str,
        verifier,
    ):

        return self.verifier.register(
            executor_name,
            verifier,
        )

    def create_task(
        self,
        goal: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Task:

        goal = str(goal or "").strip()

        if not goal:
            raise ValueError(
                "Task goal cannot be empty."
            )

        task = Task(
            goal=goal,
            metadata=dict(metadata or {}),
        )

        self.tasks[task.task_id] = task
        self.active_task_id = task.task_id

        return task

    def get_task(
        self,
        task_id: str,
    ) -> Optional[Task]:

        return self.tasks.get(
            str(task_id or "").strip()
        )

    def active_task(self) -> Optional[Task]:

        if not self.active_task_id:
            return None

        return self.get_task(
            self.active_task_id
        )

    def add_step(
        self,
        task_id: str,
        description: str,
        executor: str = "",
        dependencies: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TaskStep:

        task = self.get_task(task_id)

        if task is None:
            raise KeyError(
                f"Unknown task: {task_id}"
            )

        return task.add_step(
            description=description,
            executor=executor,
            dependencies=dependencies,
            metadata=metadata,
        )

    def ready_steps(
        self,
        task_id: Optional[str] = None,
    ) -> list[TaskStep]:

        task = (
            self.get_task(task_id)
            if task_id
            else self.active_task()
        )

        if task is None:
            return []

        return task.ready_steps()

    def execute_step(
        self,
        task_id: str,
        step_id: str,
        context: Optional[dict[str, Any]] = None,
    ) -> StepResult:

        task = self.get_task(task_id)

        if task is None:
            raise KeyError(
                f"Unknown task: {task_id}"
            )

        if task.is_complete():
            return StepResult(
                success=False,
                error="Task is already completed.",
            )

        if task.is_cancelled():
            return StepResult(
                success=False,
                error="Task has been cancelled.",
            )

        step = task.get_step(step_id)

        if step is None:
            raise KeyError(
                f"Unknown step: {step_id}"
            )

        ready = task.ready_steps()

        if step not in ready:
            return StepResult(
                success=False,
                error=(
                    "Step is not ready. Its dependencies "
                    "may not be complete."
                ),
            )

        executor = None

        if step.executor:

            candidate = self.get_executor(
                step.executor
            )

            if (
                candidate is not None
                and
                candidate.can_execute(step)
            ):
                executor = candidate

        else:

            for candidate in self.executors.values():

                if candidate.can_execute(step):
                    executor = candidate
                    break

        if executor is None:

            step.mark_failed(
                "No executor is available for this step."
            )

            return StepResult(
                success=False,
                error=step.error,
            )

        task.status = TaskStatus.RUNNING
        task.current_step_id = step.step_id
        step.mark_running()

        context = dict(
            context or {}
        )

        # The orchestrator owns interruption internally.
        #
        # Do not inject the live TaskInterruptController or its
        # threading.Event into the executor context. Those objects
        # contain thread locks and are not safe to serialize.
        #
        # Executors receive only the caller-provided, serializable
        # task context. Interruption is checked by the orchestrator
        # before execution, and task interruption remains owned by
        # self.interrupt.
        self.interrupt.check()

        result = executor.execute(
            step,
            context=context,
        )

        if not isinstance(result, StepResult):

            result = StepResult(
                success=False,
                error=(
                    "Executor returned an invalid StepResult."
                ),
                executor=executor.name,
            )

        verification = self.verifier.verify(
            step,
            result,
            context=context,
        )

        if verification.verified:

            result.metadata["verified"] = True
            result.metadata[
                "verification_reason"
            ] = verification.reason

            final_verification = (
                verification.reason
                or
                result.verification
                or
                "Verified."
            )

            step.mark_completed(
                result=result.result,
                verification=final_verification,
            )

            result.verification = final_verification
            self.recovery.record_success(step)

        else:

            result.metadata["verified"] = False
            result.metadata[
                "verification_reason"
            ] = verification.reason

            result.success = False

            if not result.error:
                result.error = (
                    verification.reason
                    or
                    "Verification failed."
                )

            result.metadata[
                "recovery"
            ] = self.recovery.record_failure(
                step,
                result,
            )

            step.mark_failed(
                result.error
                or
                "Verification failed."
            )

        task.current_step_id = None

        return result

    def start_task(
        self,
        task_id: Optional[str] = None,
    ) -> bool:

        task = (
            self.get_task(task_id)
            if task_id
            else self.active_task()
        )

        if task is None:
            return False

        self.recovery.reset()
        self.interrupt.clear()
        task.start()
        self.active_task_id = task.task_id
        return True

    def complete_task(
        self,
        task_id: Optional[str] = None,
        result: Any = None,
    ) -> bool:

        task = (
            self.get_task(task_id)
            if task_id
            else self.active_task()
        )

        if task is None:
            return False

        task.complete(result)

        if self.active_task_id == task.task_id:
            self.active_task_id = None

        return True

    def fail_task(
        self,
        task_id: Optional[str] = None,
        error: str = "",
    ) -> bool:

        task = (
            self.get_task(task_id)
            if task_id
            else self.active_task()
        )

        if task is None:
            return False

        task.fail(error)

        if self.active_task_id == task.task_id:
            self.active_task_id = None

        return True

    def interrupt_task(
        self,
        task_id: Optional[str] = None,
        reason: str = "Task interrupted by user.",
    ) -> bool:

        task = (
            self.get_task(task_id)
            if task_id
            else self.active_task()
        )

        if task is None:
            return False

        self.interrupt.request(
            reason
        )

        task.cancel(
            reason
        )

        self.cancelled_task_ids.add(
            task.task_id
        )

        for executor in self.executors.values():

            cancel = getattr(
                executor,
                "cancel",
                None,
            )

            if callable(cancel):

                try:
                    cancel(reason)
                except Exception as exc:

                    print(
                        "[Orchestrator] "
                        "Interrupt warning:",
                        exc,
                    )

        if self.active_task_id == task.task_id:
            self.active_task_id = None

        return True

    def cancel_task(
        self,
        task_id: Optional[str] = None,
        reason: str = "Task cancelled.",
    ) -> bool:

        return self.interrupt_task(
            task_id=task_id,
            reason=reason,
        )

    def set_replanner(self, planner) -> None:
        self.replanner.set_planner(planner)

    def clear_replanner(self) -> None:
        self.replanner.clear_planner()

    def replan_task(
        self,
        task_id: Optional[str] = None,
        reason: str = "Current route failed.",
        failed_step_id: Optional[str] = None,
    ) -> ReplanResult:

        task = self.get_task(task_id) if task_id else self.active_task()
        if task is None:
            return ReplanResult(False, "No active task to replan.")

        failed_step = task.get_step(failed_step_id) if failed_step_id else None

        context = {
            "task": task.to_dict(),
            "goal": task.goal,
            "failed_step": failed_step.to_dict() if failed_step else None,
            "reason": str(reason or "Current route failed."),
            "recovery": self.recovery.context(),
        }

        result = self.replanner.replan(context)
        if not result.success:
            return result

        if failed_step is not None and not failed_step.is_terminal():
            failed_step.status = StepStatus.SKIPPED

        created_ids = []
        for spec in result.step_specs:
            if not isinstance(spec, dict):
                continue
            description = str(spec.get("description", "")).strip()
            if not description:
                continue

            dependencies = list(spec.get("dependencies", []))
            if not dependencies:
                dependencies = [
                    step.step_id
                    for step in task.steps
                    if step.status == StepStatus.COMPLETED
                ]

            step = task.add_step(
                description=description,
                executor=str(spec.get("executor", "")).strip(),
                dependencies=dependencies,
                metadata=dict(spec.get("metadata", {})),
            )
            step.metadata["replanned"] = True
            step.metadata["replan_reason"] = str(reason or "")
            created_ids.append(step.step_id)

        if not created_ids:
            return ReplanResult(
                success=False,
                reason="Replanner produced no usable replacement steps.",
            )

        task.status = TaskStatus.READY
        task.current_step_id = None

        return ReplanResult(
            success=True,
            reason=result.reason or "Task replanned.",
            step_specs=result.step_specs,
            metadata={**result.metadata, "created_step_ids": created_ids},
        )

    def task_snapshot(
        self,
        task_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:

        task = (
            self.get_task(task_id)
            if task_id
            else self.active_task()
        )

        if task is None:
            return None

        snapshot = task.to_dict()

        snapshot[
            "registered_executors"
        ] = list(self.executors.keys())

        snapshot[
            "registered_verifiers"
        ] = self.verifier.names()

        snapshot[
            "recovery"
        ] = self.recovery.context()

        snapshot[
            "replanning_available"
        ] = self.replanner.planner is not None

        snapshot[
            "interrupt_requested"
        ] = self.interrupt.is_requested()

        snapshot[
            "interrupt_reason"
        ] = self.interrupt.reason

        return snapshot

    def __repr__(self):

        return (
            "<TaskOrchestrator "
            f"tasks={len(self.tasks)} "
            f"executors={len(self.executors)} "
            f"verifiers={len(self.verifier.names())} "
            f"active={self.active_task_id!r}>"
        )