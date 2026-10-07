from __future__ import annotations

from automation.computer_goal import ComputerGoalUnderstanding
from automation.performance import PerformanceTracker

from backend.intent_decomposer import (
    DecomposedIntent,
    IntentDecomposer,
)
from backend.goal_decomposer import GoalDecomposer
from backend.subgoal_dependencies import (
    SubgoalDependencyResolver,
)
from backend.subgoal_decision import (
    SubgoalDecisionEngine,
)
from backend.ambiguity_handler import (
    AmbiguityHandler,
)
from backend.long_horizon import (
    LongHorizonReasoner,
)
from backend.constraint_planner import (
    ConstraintPlanner,
)
from backend.plan_refiner import (
    PlanRefiner,
)


def main():

    print("=" * 70)
    print("JARVIS X - PHASE 5.9 VALIDATION")
    print("=" * 70)

    ############################################################
    # 1. INTENT REPRESENTATION
    ############################################################

    request = (
        "Find my chemistry PDF, summarize it, and save the "
        "summary in my Chemistry folder."
    )

    decomposer = IntentDecomposer()

    intent = decomposer.decompose(
        request
    )

    assert intent.primary_goal
    assert intent.request

    print("[PASS] Intent representation")

    ############################################################
    # 2. SUBGOAL CREATION
    ############################################################

    first = decomposer.add_subgoal(
        intent,
        "Find the chemistry PDF.",
        goal_type="computer",
        priority=1,
    )

    second = decomposer.add_subgoal(
        intent,
        "Read and summarize the PDF.",
        goal_type="reasoning",
        priority=2,
        dependencies=[
            first.subgoal_id,
        ],
    )

    third = decomposer.add_subgoal(
        intent,
        "Save the summary in the Chemistry folder.",
        goal_type="computer",
        priority=3,
        dependencies=[
            second.subgoal_id,
        ],
    )

    decomposer.validate_dependencies(
        intent
    )

    assert len(
        intent.subgoals
    ) == 3

    print("[PASS] Goal → subgoals")

    ############################################################
    # 3. DEPENDENCY RESOLUTION
    ############################################################

    resolver = (
        SubgoalDependencyResolver()
    )

    ready = resolver.get_ready(
        intent,
        completed=set(),
    )

    assert len(
        ready
    ) == 1

    assert (
        ready[0].subgoal_id
        ==
        first.subgoal_id
    )

    completed = {
        first.subgoal_id,
    }

    ready = resolver.get_ready(
        intent,
        completed=completed,
    )

    assert (
        ready[0].subgoal_id
        ==
        second.subgoal_id
    )

    print("[PASS] Dependency resolution")

    ############################################################
    # 4. DECISION MAKING
    ############################################################

    decision = (
        SubgoalDecisionEngine().decide(
            intent,
            ready,
        )
    )

    assert decision.selected is not None
    assert (
        decision.selected.subgoal_id
        ==
        second.subgoal_id
    )

    print("[PASS] Subgoal decision making")

    ############################################################
    # 5. AMBIGUITY HANDLING
    ############################################################

    ambiguity = (
        AmbiguityHandler().analyze(
            "Open the file."
        )
    )

    assert ambiguity.ambiguous is True
    assert ambiguity.clarification_question

    clear = (
        AmbiguityHandler().analyze(
            "Open Calculator."
        )
    )

    assert clear.ambiguous is False

    print("[PASS] Ambiguity handling")

    ############################################################
    # 6. LONG-HORIZON STATE
    ############################################################

    horizon = LongHorizonReasoner()

    state = horizon.start(
        intent
    )

    horizon.activate(
        state,
        first,
    )

    horizon.complete(
        state,
        intent,
        first,
        result="Chemistry PDF located.",
    )

    assert (
        first.subgoal_id
        in
        state.completed_subgoals
    )

    assert state.progress > 0

    print("[PASS] Long-horizon reasoning state")

    ############################################################
    # 7. CONSTRAINT PLANNING
    ############################################################

    intent.global_constraints = [
        "Do not delete files.",
        "Verify the final result.",
    ]

    constraints = (
        ConstraintPlanner()
    )

    constraints.load_intent(
        intent
    )

    allowed = constraints.check(
        "rename the chemistry PDF",
    )

    assert allowed.allowed is True

    blocked = constraints.check(
        "delete the chemistry PDF",
    )

    assert blocked.allowed is False

    print("[PASS] Constraint planning")

    ############################################################
    # 8. DYNAMIC PLAN REFINEMENT
    ############################################################

    refiner = PlanRefiner()

    refinement = refiner.refine(
        intent,
        {
            "reason":
                "New information discovered.",
            "updates": {
                third.subgoal_id: {
                    "description":
                        "Save the summary as a text file "
                        "in the Chemistry folder.",
                    "priority": 3,
                }
            },
        },
    )

    assert refinement.changed is True
    assert (
        third.subgoal_id
        in
        refinement.updated_subgoals
    )
    updated = next(
        item
        for item in intent.subgoals
        if item.subgoal_id
        == third.subgoal_id
    )

    assert (
        "text file"
        in
        updated.description
    )

    print("[PASS] Dynamic plan refinement")

    ############################################################
    # 9. REASONING CONTEXT
    ############################################################

    context = horizon.build_context(
        state,
        intent,
    )

    assert context["primary_goal"]
    assert "remaining_subgoals" in context

    print("[PASS] Long-horizon reasoning context")

    ############################################################
    # FINAL
    ############################################################

    print()

    print("=" * 70)

    print(
        "PHASE 5.9 VALIDATION PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":

    main()