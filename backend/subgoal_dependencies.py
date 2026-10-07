from __future__ import annotations

from typing import Any

from backend.intent_decomposer import (
    DecomposedIntent,
    SubGoal,
)


class SubgoalDependencyResolver:

    """
    Resolves dependencies between semantic subgoals.

    It does not execute subgoals.
    It only determines which objectives are currently available.
    """

    ########################################################
    # READY SUBGOALS
    ########################################################

    def get_ready(
        self,
        intent: DecomposedIntent,
        completed: set[str] | None = None,
    ) -> list[SubGoal]:

        completed = set(
            completed or set()
        )

        ready = []

        for subgoal in intent.subgoals:

            if (
                subgoal.subgoal_id
                in
                completed
            ):
                continue

            dependencies_met = all(
                dependency
                in
                completed

                for dependency
                in
                subgoal.dependencies
            )

            if dependencies_met:

                ready.append(
                    subgoal
                )

        ####################################################
        # Highest priority first.
        ####################################################

        ready.sort(
            key=lambda item:
                item.priority
        )

        return ready

    ########################################################
    # BLOCKED SUBGOALS
    ########################################################

    def get_blocked(
        self,
        intent: DecomposedIntent,
        completed: set[str] | None = None,
    ) -> list[SubGoal]:

        completed = set(
            completed or set()
        )

        blocked = []

        for subgoal in intent.subgoals:

            if (
                subgoal.subgoal_id
                in
                completed
            ):
                continue

            if any(
                dependency
                not in
                completed

                for dependency
                in
                subgoal.dependencies
            ):

                blocked.append(
                    subgoal
                )

        return blocked

    ########################################################
    # NEXT SUBGOAL
    ########################################################

    def next(
        self,
        intent: DecomposedIntent,
        completed: set[str] | None = None,
    ) -> SubGoal | None:

        ready = self.get_ready(
            intent,
            completed,
        )

        if not ready:
            return None

        return ready[0]

    ########################################################
    # DEPENDENCY STATUS
    ########################################################

    def status(
        self,
        intent: DecomposedIntent,
        completed: set[str] | None = None,
    ) -> dict[str, Any]:

        completed = set(
            completed or set()
        )

        ready = self.get_ready(
            intent,
            completed,
        )

        blocked = self.get_blocked(
            intent,
            completed,
        )

        return {
            "completed": list(
                completed
            ),

            "ready": [
                subgoal.subgoal_id
                for subgoal in ready
            ],

            "blocked": [
                subgoal.subgoal_id
                for subgoal in blocked
            ],

            "remaining": [
                subgoal.subgoal_id
                for subgoal in intent.subgoals
                if subgoal.subgoal_id
                not in
                completed
            ],
        }

    ########################################################
    # VALIDATION
    ########################################################

    def validate(
        self,
        intent: DecomposedIntent,
    ) -> None:

        known_ids = {
            subgoal.subgoal_id
            for subgoal in intent.subgoals
        }

        for subgoal in intent.subgoals:

            if (
                subgoal.subgoal_id
                in
                subgoal.dependencies
            ):

                raise ValueError(
                    "A subgoal cannot depend on itself."
                )

            for dependency in (
                subgoal.dependencies
            ):

                if dependency not in known_ids:

                    raise ValueError(
                        "Unknown subgoal dependency: "
                        f"{dependency}"
                    )

        ####################################################
        # Cycle detection
        ####################################################

        for subgoal in intent.subgoals:

            if self._has_cycle(
                subgoal.subgoal_id,
                intent,
                set(),
                set(),
            ):

                raise ValueError(
                    "Circular subgoal dependency detected."
                )

    ########################################################
    # CYCLE DETECTION
    ########################################################

    def _has_cycle(
        self,
        subgoal_id: str,
        intent: DecomposedIntent,
        visiting: set[str],
        visited: set[str],
    ) -> bool:

        if subgoal_id in visiting:

            return True

        if subgoal_id in visited:

            return False

        subgoal = next(
            (
                item
                for item in intent.subgoals
                if item.subgoal_id
                == subgoal_id
            ),
            None,
        )

        if subgoal is None:

            return False

        visiting.add(
            subgoal_id
        )

        for dependency in (
            subgoal.dependencies
        ):

            if self._has_cycle(
                dependency,
                intent,
                visiting,
                visited,
            ):

                return True

        visiting.remove(
            subgoal_id
        )

        visited.add(
            subgoal_id
        )

        return False