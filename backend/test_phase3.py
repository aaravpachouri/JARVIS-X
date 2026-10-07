from __future__ import annotations

from backend.task_orchestrator import (
    FunctionTaskExecutor,
    StepResult,
    StepStatus,
    TaskOrchestrator,
)
from backend.task_verifier import (
    FunctionVerifier,
)


def main():

    print("=" * 70)
    print("JARVIS X - PHASE 3.10 VALIDATION")
    print("=" * 70)

    orchestrator = TaskOrchestrator()

    ############################################################
    # 1. BASIC TASK + DEPENDENCY TEST
    ############################################################

    task = orchestrator.create_task(
        "Phase 3 validation"
    )

    step1 = task.add_step(
        "Generate test result",
        executor="TEST",
    )

    step2 = task.add_step(
        "Use previous result",
        executor="TEST",
        dependencies=[step1.step_id],
    )

    assert step2 not in task.ready_steps(), (
        "Dependency gate failed."
    )

    print("[PASS] Dependency gating")

    ############################################################
    # 2. EXECUTOR TEST
    ############################################################

    def test_handler(
        step,
        context,
    ):

        return StepResult(
            success=True,
            result="OK",
            executor="TEST",
            metadata={
                "verified": True,
            },
        )

    orchestrator.register_executor(
        FunctionTaskExecutor(
            name="TEST",
            execute=test_handler,
        )
    )

    orchestrator.start_task(
        task.task_id
    )

    result1 = orchestrator.execute_step(
        task.task_id,
        step1.step_id,
    )

    assert result1.success is True
    assert step1.status == StepStatus.COMPLETED

    print("[PASS] Executor dispatch + verification")

    ############################################################
    # 3. DEPENDENCY UNLOCK TEST
    ############################################################

    ready = task.ready_steps()

    assert step2 in ready

    print("[PASS] Completed step unlocks dependent step")

    ############################################################
    # 4. SECOND STEP
    ############################################################

    result2 = orchestrator.execute_step(
        task.task_id,
        step2.step_id,
    )

    assert result2.success is True
    assert step2.status == StepStatus.COMPLETED

    print("[PASS] Multi-step execution")

    ############################################################
    # 5. INTERRUPT TEST
    ############################################################

    interrupted = orchestrator.interrupt_task(
        task.task_id,
        "Validation interrupt",
    )

    assert interrupted is True
    assert task.is_cancelled() is True

    print("[PASS] Central interruption")

    ############################################################
    # 6. SNAPSHOT TEST
    ############################################################

    snapshot = orchestrator.task_snapshot(
        task.task_id
    )

    assert snapshot is not None
    assert "registered_executors" in snapshot
    assert "registered_verifiers" in snapshot
    assert "recovery" in snapshot
    assert "interrupt_requested" in snapshot

    print("[PASS] Task snapshot integrity")

    ############################################################
    # SUMMARY
    ############################################################

    print()
    print("=" * 70)
    print("PHASE 3.10 VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()