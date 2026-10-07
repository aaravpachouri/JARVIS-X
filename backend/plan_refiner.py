from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.intent_decomposer import (
    DecomposedIntent,
    SubGoal,
)


############################################################
# REFINEMENT RESULT
############################################################

@dataclass
class PlanRefinement:

    changed: bool = False

    reason: str = ""

    added_subgoals: list[
        SubGoal
    ] = field(
        default_factory=list
    )

    removed_subgoals: list[str] = field(
        default_factory=list
    )

    updated_subgoals: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# PLAN REFINER
############################################################

class PlanRefiner:

    """
    Refines an existing semantic plan when new information,
    failures, discoveries, or changed conditions appear.

    It does not execute anything.
    """

    def refine(
        self,
        intent: DecomposedIntent,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> PlanRefinement:

        context = dict(
            context or {}
        )

        result = PlanRefinement()

        ####################################################
        # New information supplied by the reasoning layer.
        ####################################################

        new_subgoals = context.get(
            "new_subgoals",
            [],
        )

        if isinstance(
            new_subgoals,
            list,
        ):

            for item in new_subgoals:

                if isinstance(
                    item,
                    SubGoal,
                ):

                    intent.subgoals.append(
                        item
                    )

                    result.added_subgoals.append(
                        item
                    )

                    result.changed = True

        ####################################################
        # Remove obsolete subgoals.
        ####################################################

        remove_ids = set(
            str(item)
            for item in (
                context.get(
                    "remove_subgoals",
                    [],
                )
                or []
            )
        )

        if remove_ids:

            retained = []

            for subgoal in intent.subgoals:

                if (
                    subgoal.subgoal_id
                    in
                    remove_ids
                ):

                    result.removed_subgoals.append(
                        subgoal.subgoal_id
                    )

                    result.changed = True

                else:

                    retained.append(
                        subgoal
                    )

            intent.subgoals = retained

        ####################################################
        # Update descriptions / constraints.
        ####################################################

        updates = context.get(
            "updates",
            {},
        )

        if isinstance(
            updates,
            dict,
        ):

            for subgoal_id, update in (
                updates.items()
            ):

                if not isinstance(
                    update,
                    dict,
                ):

                    continue

                subgoal = next(
                    (
                        item
                        for item
                        in intent.subgoals
                        if item.subgoal_id
                        ==
                        str(
                            subgoal_id
                        )
                    ),
                    None,
                )

                if subgoal is None:

                    continue

                changed = False

                if "description" in update:

                    description = str(
                        update["description"]
                        or ""
                    ).strip()

                    if description:

                        subgoal.description = (
                            description
                        )

                        changed = True

                if "goal_type" in update:

                    goal_type = str(
                        update["goal_type"]
                        or ""
                    ).strip()

                    if goal_type:

                        subgoal.goal_type = (
                            goal_type
                        )

                        changed = True

                if "priority" in update:

                    try:

                        subgoal.priority = int(
                            update["priority"]
                        )

                        changed = True

                    except (
                        TypeError,
                        ValueError,
                    ):

                        pass

                if "dependencies" in update:

                    dependencies = list(
                        update["dependencies"]
                        or []
                    )

                    subgoal.dependencies = (
                        dependencies
                    )

                    changed = True

                if "constraints" in update:

                    constraints = list(
                        update["constraints"]
                        or []
                    )

                    subgoal.constraints = (
                        constraints
                    )

                    changed = True

                if changed:

                    result.updated_subgoals.append(
                        subgoal.subgoal_id
                    )

                    result.changed = True

        ####################################################
        # Update global constraints.
        ####################################################

        constraints = context.get(
            "global_constraints",
        )

        if isinstance(
            constraints,
            list,
        ):

            cleaned = [
                str(item).strip()
                for item in constraints
                if str(item).strip()
            ]

            if cleaned:

                intent.global_constraints = (
                    list(
                        dict.fromkeys(
                            cleaned
                        )
                    )
                )

                result.changed = True

        ####################################################
        # Update requested final result.
        ####################################################

        if (
            "requested_result"
            in
            context
        ):

            intent.requested_result = str(
                context.get(
                    "requested_result",
                    "",
                )
                or ""
            ).strip()

            result.changed = True

        ####################################################
        # Reason
        ####################################################

        result.reason = str(
            context.get(
                "reason",
                "Plan refined from updated task information.",
            )
            or
            "Plan refined from updated task information."
        )

        result.metadata[
            "context_source"
        ] = context.get(
            "source",
            "runtime",
        )

        return result

    ########################################################
    # REPLAN FROM FAILURE
    ########################################################

    def refine_from_failure(
        self,
        intent: DecomposedIntent,
        failed_subgoal: SubGoal,
        reason: str,
    ) -> PlanRefinement:

        """
        Lightweight failure refinement.

        The failed objective is retained, but marked with
        recovery metadata so a later reasoning layer can choose
        a different strategy.
        """

        failed_subgoal.metadata[
            "last_failure"
        ] = str(
            reason or ""
        )

        failed_subgoal.metadata[
            "requires_replanning"
        ] = True

        return PlanRefinement(
            changed=True,
            reason=(
                "Failed subgoal marked for "
                "alternative planning."
            ),
            updated_subgoals=[
                failed_subgoal.subgoal_id
            ],
            metadata={
                "failure_replanning":
                    True,
            },
        )

    ########################################################
    # CONTEXT
    ########################################################

    def build_context(
        self,
        intent: DecomposedIntent,
    ) -> dict[str, Any]:

        return {
            "primary_goal":
                intent.primary_goal,

            "subgoals": [
                {
                    "id":
                        subgoal.subgoal_id,

                    "description":
                        subgoal.description,

                    "goal_type":
                        subgoal.goal_type,

                    "priority":
                        subgoal.priority,

                    "dependencies":
                        list(
                            subgoal.dependencies
                        ),

                    "constraints":
                        list(
                            subgoal.constraints
                        ),

                    "metadata":
                        dict(
                            subgoal.metadata
                        ),
                }

                for subgoal
                in intent.subgoals
            ],

            "global_constraints":
                list(
                    intent.global_constraints
                ),

            "requested_result":
                intent.requested_result,
        }