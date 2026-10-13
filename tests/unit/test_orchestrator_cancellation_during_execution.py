from backend.task_orchestrator import (
    FunctionTaskExecutor,
    StepResult,
    StepStatus,
    TaskOrchestrator,
    TaskStatus,
)


def test_cancellation_during_executor_is_not_overwritten_by_failure():
    orchestrator = TaskOrchestrator()
    task = orchestrator.create_task("Run cancellable work")
    calls = []

    def execute_and_cancel(step, context):
        calls.append(step.step_id)
        assert orchestrator.interrupt_task(
            task.task_id,
            reason="Cancelled while executor was running.",
        )
        # A running operation may still return an error after cancellation.
        return StepResult(
            success=False,
            error="Underlying operation was interrupted.",
            executor="TEST",
        )

    orchestrator.register_executor(
        FunctionTaskExecutor(
            name="TEST",
            execute=execute_and_cancel,
        )
    )
    step = orchestrator.add_step(
        task.task_id,
        description="Perform cancellable action",
        executor="TEST",
    )

    result = orchestrator.execute_step(task.task_id, step.step_id)

    assert calls == [step.step_id]
    assert result.success is False
    assert result.metadata["cancelled"] is True
    assert result.error == "Cancelled while executor was running."
    assert task.status == TaskStatus.CANCELLED
    assert task.cancelled is True
    assert task.current_step_id is None
    assert step.status == StepStatus.CANCELLED
    assert step.error == "Cancelled while executor was running."
