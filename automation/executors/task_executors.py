from __future__ import annotations

from typing import Any, Callable, Optional

from backend.task_orchestrator import (
    TaskExecutor,
    TaskStep,
    StepResult,
)


############################################################
# GENERIC CALLABLE EXECUTOR
############################################################

class CallableExecutor(TaskExecutor):

    """
    Generic adapter for any callable capability.

    This keeps TaskOrchestrator independent from the concrete
    implementation behind the executor.
    """

    def __init__(
        self,
        name: str,
        handler: Callable[
            [TaskStep, dict[str, Any]],
            Any,
        ],
        can_execute: Optional[
            Callable[[TaskStep], bool]
        ] = None,
    ):

        self.name = str(
            name or "executor"
        ).strip()

        self.handler = handler

        self._can_execute = can_execute

    def can_execute(
        self,
        step: TaskStep,
    ) -> bool:

        if self._can_execute is None:

            return (
                step.executor
                ==
                self.name
            )

        try:

            return bool(
                self._can_execute(
                    step
                )
            )

        except Exception as exc:

            print(
                f"[Executor:{self.name}] "
                f"can_execute error:",
                exc,
            )

            return False

    def execute(
        self,
        step: TaskStep,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> StepResult:

        try:

            result = self.handler(
                step,
                dict(
                    context or {}
                ),
            )

            ####################################################
            # Already normalized result.
            ####################################################

            if isinstance(
                result,
                StepResult,
            ):

                if not result.executor:

                    result.executor = (
                        self.name
                    )

                return result

            ####################################################
            # Normal Python return value.
            ####################################################

            return StepResult(
                success=True,
                result=result,
                executor=self.name,
            )

        except Exception as exc:

            return StepResult(
                success=False,
                error=str(
                    exc
                ),
                executor=self.name,
            )


############################################################
# LOCAL TOOL EXECUTOR
############################################################

class LocalToolExecutor(
    CallableExecutor
):

    """
    Executor category for deterministic local capabilities.

    The actual LocalToolRegistry is injected from outside.

    This prevents the orchestrator from knowing about individual
    tools such as computation, datetime, units, etc.
    """

    name = "LOCAL_TOOL"

    def __init__(
        self,
        tool_registry,
    ):

        self.tool_registry = (
            tool_registry
        )

        super().__init__(
            name=self.name,
            handler=self._handle,
            can_execute=self._can_execute,
        )

    def _can_execute(
        self,
        step: TaskStep,
    ) -> bool:

        if step.executor:

            return (
                step.executor
                ==
                self.name
            )

        return False

    def _handle(
        self,
        step: TaskStep,
        context: dict[str, Any],
    ):

        request = str(
            step.description
            or ""
        ).strip()

        if not request:

            return StepResult(
                success=False,
                error=(
                    "Local-tool step has no description."
                ),
                executor=self.name,
            )

        result = (
            self.tool_registry.execute(
                request
            )
        )

        if not result.handled:

            return StepResult(
                success=False,
                error=(
                    "No registered local capability "
                    "could handle this step."
                ),
                executor=self.name,
                metadata={
                    "request": request,
                },
            )

        return StepResult(
            success=True,
            result=result.answer,
            executor=self.name,
            verification=(
                "Local capability returned a handled result."
            ),
            metadata={
                "tool": result.tool,
                "confidence": result.confidence,
                "tool_metadata":
                    result.metadata,
            },
        )


############################################################
# LOCAL BRAIN EXECUTOR
############################################################

class LocalBrainExecutor(
    CallableExecutor
):

    """
    Executor category for general local intelligence.

    The actual AIBrain instance is injected.

    This means the orchestrator does not know how the brain
    internally works.
    """

    name = "LOCAL_BRAIN"

    def __init__(
        self,
        brain,
    ):

        self.brain = brain

        super().__init__(
            name=self.name,
            handler=self._handle,
            can_execute=self._can_execute,
        )

    def _can_execute(
        self,
        step: TaskStep,
    ) -> bool:

        if step.executor:

            return (
                step.executor
                ==
                self.name
            )

        return False

    def _handle(
        self,
        step: TaskStep,
        context: dict[str, Any],
    ):

        request = str(
            step.description
            or ""
        ).strip()

        if not request:

            return StepResult(
                success=False,
                error=(
                    "Local-brain step has no description."
                ),
                executor=self.name,
            )

        ####################################################
        # AIBrain is expected to expose think().
        ####################################################

        response = self.brain.think(
            request
        )

        if response is None:

            return StepResult(
                success=False,
                error=(
                    "Local brain returned no response."
                ),
                executor=self.name,
            )

        success = bool(
            getattr(
                response,
                "success",
                True,
            )
        )

        answer = str(
            getattr(
                response,
                "answer",
                "",
            )
            or ""
        ).strip()

        mode = getattr(
            response,
            "mode",
            "CHAT",
        )

        ####################################################
        # If the brain determines that this actually needs
        # physical computer interaction, the orchestrator
        # should not pretend it was completed as a chat step.
        ####################################################

        if str(
            mode
        ).upper() == "COMPUTER":

            return StepResult(
                success=False,
                result="",
                error=(
                    "Local brain routed this step "
                    "to COMPUTER."
                ),
                executor=self.name,
                metadata={
                    "mode": "COMPUTER",
                    "computer_goal":
                        getattr(
                            response,
                            "computer_goal",
                            request,
                        ),
                },
            )

        if not success:

            return StepResult(
                success=False,
                result=answer,
                error=str(
                    getattr(
                        response,
                        "error",
                        "Local brain failed.",
                    )
                    or
                    "Local brain failed."
                ),
                executor=self.name,
            )

        return StepResult(
            success=True,
            result=answer,
            executor=self.name,
            verification=(
                "Local brain returned a successful response."
            ),
            metadata={
                "mode": mode,
                "reasoning":
                    getattr(
                        response,
                        "reasoning",
                        "",
                    ),
            },
        )


############################################################
# COMPUTER AGENT EXECUTOR
############################################################

class ComputerAgentExecutor(
    CallableExecutor
):

    """
    Executor category for physical computer interaction.

    The concrete ComputerAgent implementation is injected.

    We deliberately do NOT assume whether its public method is
    execute(), run(), start(), execute_goal(), or something else.

    A caller provides an adapter function that matches the actual
    ComputerAgent implementation.
    """

    name = "COMPUTER_AGENT"

    def __init__(
        self,
        handler: Callable[
            [TaskStep, dict[str, Any]],
            Any,
        ],
    ):

        super().__init__(
            name=self.name,
            handler=handler,
            can_execute=self._can_execute,
        )

    def _can_execute(
        self,
        step: TaskStep,
    ) -> bool:

        if step.executor:

            return (
                step.executor
                ==
                self.name
            )

        return False


############################################################
# EXECUTOR DISPATCHER
############################################################

class ExecutorDispatcher:

    """
    Universal executor dispatcher.

    The dispatcher contains no application-specific workflows.

    It simply maps executor names to executor implementations.
    """

    def __init__(self):

        self.executors: dict[
            str,
            TaskExecutor,
        ] = {}

    ########################################################
    # REGISTER
    ########################################################

    def register(
        self,
        executor: TaskExecutor,
    ) -> TaskExecutor:

        if not isinstance(
            executor,
            TaskExecutor,
        ):

            raise TypeError(
                "ExecutorDispatcher requires "
                "TaskExecutor instances."
            )

        self.executors[
            executor.name
        ] = executor

        print(
            "[Dispatcher] "
            f"Registered executor: "
            f"{executor.name}"
        )

        return executor

    ########################################################
    # UNREGISTER
    ########################################################

    def unregister(
        self,
        name: str,
    ) -> bool:

        name = str(
            name or ""
        ).strip()

        if name not in self.executors:

            return False

        del self.executors[
            name
        ]

        return True

    ########################################################
    # LOOKUP
    ########################################################

    def get(
        self,
        name: str,
    ) -> Optional[
        TaskExecutor
    ]:

        return self.executors.get(
            str(
                name or ""
            ).strip()
        )

    ########################################################
    # FIND
    ########################################################

    def find(
        self,
        step: TaskStep,
    ) -> Optional[
        TaskExecutor
    ]:

        ####################################################
        # Explicit executor takes priority.
        ####################################################

        if step.executor:

            executor = self.get(
                step.executor
            )

            if (
                executor is not None
                and
                executor.can_execute(
                    step
                )
            ):

                return executor

            return None

        ####################################################
        # Otherwise let registered executors determine
        # whether they can handle the step.
        ####################################################

        for executor in (
            self.executors.values()
        ):

            if executor.can_execute(
                step
            ):

                return executor

        return None

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

        executor = self.find(
            step
        )

        if executor is None:

            return StepResult(
                success=False,
                error=(
                    "No registered executor can "
                    f"handle step: {step.description}"
                ),
            )

        return executor.execute(
            step,
            context=context,
        )

    ########################################################
    # LIST
    ########################################################

    def names(
        self,
    ) -> list[str]:

        return list(
            self.executors.keys()
        )

    ########################################################
    # REPRESENTATION
    ########################################################

    def __repr__(
        self,
    ):

        return (
            "<ExecutorDispatcher "
            f"executors={self.names()!r}>"
        )