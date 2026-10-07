from __future__ import annotations

from automation.computer_goal import ComputerGoalUnderstanding
from automation.computer_planner import ComputerPlanner
from automation.computer_observation import (
    ComputerObservationBuilder,
)
from automation.computer_action_selector import (
    ActionCandidate,
    ComputerActionSelector,
)
from automation.computer_context import (
    ComputerContextBuilder,
)
from automation.computer_recovery import (
    ComputerRecoveryAdvisor,
    ComputerRecoveryDecision,
)
from automation.multi_app_task import (
    MultiApplicationTask,
)
from automation.performance import (
    PerformanceTracker,
)


def main():

    print("=" * 70)
    print("JARVIS X - PHASE 4.10 VALIDATION")
    print("=" * 70)

    ############################################################
    # 1. GOAL UNDERSTANDING
    ############################################################

    request = (
        "Find my chemistry PDF and move it to the Chemistry folder."
    )

    goal = ComputerGoalUnderstanding().understand(
        request
    )

    assert goal.goal
    assert goal.success_criteria
    assert goal.constraints

    print("[PASS] Goal understanding")

    ############################################################
    # 2. MULTI-STAGE PLAN
    ############################################################

    planner = ComputerPlanner()

    plan = planner.create_plan(
        goal.goal
    )

    assert len(
        plan.stages
    ) >= 2

    assert plan.current()

    print("[PASS] Multi-stage computer planning")

    ############################################################
    # 3. STRUCTURED OBSERVATION
    ############################################################

    observation = (
        ComputerObservationBuilder().build(
            ocr=[
                {
                    "text": "Chemistry",
                    "confidence": 0.98,
                    "x": 500,
                    "y": 300,
                }
            ],
            active_window="File Explorer",
            screen_size=(
                1920,
                1080,
            ),
        )
    )

    assert observation.active_window
    assert observation.elements

    print("[PASS] Structured visual observation")

    ############################################################
    # 4. ACTION SELECTION
    ############################################################

    candidates = [
        ActionCandidate(
            tool="LEFT_CLICK",
            parameters={
                "x": 500,
                "y": 300,
            },
            reason="Click detected Chemistry folder.",
            confidence=0.96,
            risk=0.10,
            expected_outcome="Chemistry folder opens.",
        ),
        ActionCandidate(
            tool="TYPE_TEXT",
            parameters={
                "text": "Chemistry",
            },
            reason="Search for Chemistry.",
            confidence=0.72,
            risk=0.20,
            expected_outcome="Chemistry appears.",
        ),
    ]

    selection = (
        ComputerActionSelector().select(
            candidates,
            observation=observation.to_dict(),
        )
    )

    assert selection.selected is not None

    assert (
        selection.selected.tool
        ==
        "LEFT_CLICK"
    )

    print("[PASS] Action selection")

    ############################################################
    # 5. CONTEXT BUILDING
    ############################################################

    class MockState:

        status = "running"

        step = 1

        last_action = None

        last_result = None

        variables = {}

        errors = []

        def __init__(
            self,
            goal_text,
            stages,
        ):

            self.goal = goal_text

            self.stages = stages

        def currentStage(
            self,
        ):

            return self.stages[0]

        def recent_history(
            self,
            count=8,
        ):

            return []

        def recent_records(
            self,
            count=10,
        ):

            return []

    mock_state = MockState(
        goal.goal,
        plan.stages,
    )

    context = (
        ComputerContextBuilder().build(
            mock_state,
            observation=observation.to_dict(),
            recovery={},
        )
    )

    assert context["goal"]

    assert context["observation"]

    print("[PASS] Context/state awareness")

    ############################################################
    # 6. RECOVERY
    ############################################################

    recovery = (
        ComputerRecoveryAdvisor().advise(
            recovery={
                "blocked_tools": [
                    "LEFT_CLICK",
                ],
                "failed_signatures": [],
            },
            last_action={
                "tool": "LEFT_CLICK",
                "parameters": {
                    "x": 500,
                    "y": 300,
                },
            },
            observation={
                "uncertainty": [],
            },
        )
    )

    assert (
        recovery.action
        ==
        ComputerRecoveryDecision.ALTERNATIVE
    )

    print("[PASS] Recovery strategy selection")

    ############################################################
    # 7. MULTI-APPLICATION TASK
    ############################################################

    multi = MultiApplicationTask(
        goal=(
            "Find chemistry notes and save them "
            "to a document."
        )
    )

    multi.add_application(
        "File Explorer",
        "Locate the notes.",
    )

    multi.add_application(
        "Word",
        "Create and save the document.",
    )

    assert len(
        multi.applications
    ) == 2

    assert multi.switch_to(
        "Word"
    )

    multi.complete_application(
        "File Explorer",
        "Notes located.",
    )

    multi.complete_application(
        "Word",
        "Document saved.",
    )

    multi.complete_task()

    assert multi.completed is True

    print("[PASS] Multi-application task state")

    ############################################################
    # 8. PERFORMANCE TRACKING
    ############################################################

    tracker = PerformanceTracker()

    with tracker.measure(
        "phase4_validation"
    ):

        _ = sum(
            range(1000)
        )

    summary = tracker.summary()

    assert (
        "phase4_validation"
        in
        summary
    )

    print("[PASS] Performance tracking")

    ############################################################
    # FINAL
    ############################################################

    print()

    print("=" * 70)

    print(
        "PHASE 4.10 VALIDATION PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":

    main()