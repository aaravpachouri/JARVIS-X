from backend.task_orchestrator import (
    FunctionTaskExecutor,
    StepStatus,
    TaskOrchestrator,
    TaskStatus,
    StepResult,
)


def test_new_task_runs_after_previous_task_is_cancelled():
    orchestrator = TaskOrchestrator()
    executed = []

    def execute(step, context):
        executed.append(step.description)
        return StepResult(
            success=True,
            result="done",
            executor="TEST",
            verification="Test executor completed.",
            metadata={"verified": True},
        )

    orchestrator.register_executor(
        FunctionTaskExecutor(name="TEST", execute=execute)
    )

    first = orchestrator.create_task("First task to cancel")
    first_step = orchestrator.add_step(
        first.task_id,
        description="First action",
        executor="TEST",
    )

    assert orchestrator.interrupt_task(
        first.task_id,
        reason="Cancelled first task.",
    )
    assert first.status == TaskStatus.CANCELLED
    assert first_step.status == StepStatus.CANCELLED

    second = orchestrator.create_task("Second task should run")
    second_step = orchestrator.add_step(
        second.task_id,
        description="Second action",
        executor="TEST",
    )

    assert orchestrator.start_task(second.task_id) is True
    result = orchestrator.execute_step(second.task_id, second_step.step_id)

    assert result.success is True
    assert result.metadata["verified"] is True
    assert second.status == TaskStatus.RUNNING
    assert second_step.status == StepStatus.COMPLETED
    assert second.current_step_id is None
    assert executed == ["Second action"]
