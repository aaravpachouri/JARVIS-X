from backend.task_orchestrator import (
    FunctionTaskExecutor,
    StepStatus,
    TaskOrchestrator,
    TaskStatus,
)


def test_interrupt_before_executor_returns_cancelled_result_and_cleans_state():
    orchestrator = TaskOrchestrator()
    calls = []

    executor = FunctionTaskExecutor(
        name="TEST",
        execute=lambda step, context: calls.append(step.step_id),
    )
    orchestrator.register_executor(executor)

    task = orchestrator.create_task("Run a test step")
    step = orchestrator.add_step(
        task.task_id,
        description="Perform test action",
        executor="TEST",
    )

    # Simulate the race where interruption is requested after the
    # task/step preflight checks but before the executor is invoked.
    orchestrator.interrupt.request("Cancelled just before execution.")

    result = orchestrator.execute_step(task.task_id, step.step_id)

    assert result.success is False
    assert result.metadata["cancelled"] is True
    assert result.error == "Cancelled just before execution."
    assert calls == []
    assert task.status == TaskStatus.CANCELLED
    assert task.cancelled is True
    assert task.current_step_id is None
    assert step.status == StepStatus.CANCELLED
    assert task.task_id in orchestrator.cancelled_task_ids
    assert orchestrator.active_task_id is None
