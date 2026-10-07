from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional


@dataclass
class GoalStep:

    step_id: str

    title: str

    description: str = ""

    order: int = 0

    status: str = "PENDING"

    dependencies: list[str] = field(
        default_factory=list
    )

    application: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "step_id":
                self.step_id,

            "title":
                self.title,

            "description":
                self.description,

            "order":
                self.order,

            "status":
                self.status,

            "dependencies":
                list(
                    self.dependencies
                ),

            "application":
                self.application,

            "metadata":
                dict(
                    self.metadata
                ),
        }


class GoalDecomposer:

    """
    Converts an identified goal into an ordered set of candidate
    steps.

    It is deliberately planner-friendly:
        - decomposition is explicit
        - dependencies are represented
        - applications can be attached
        - a custom planner can replace the heuristic fallback

    It does not execute any step.
    """

    def __init__(
        self,
        planner: Optional[
            Callable[..., Any]
        ] = None,
    ):

        self.planner = planner

    ############################################################
    # DECOMPOSE
    ############################################################

    def decompose(
        self,
        goal: str,
        *,
        context: Optional[dict[str, Any]] = None,
    ) -> list[GoalStep]:

        goal_text = str(
            goal
            or
            ""
        ).strip()

        if not goal_text:

            return []

        ########################################################
        # Prefer injected planner when available.
        ########################################################

        if self.planner is not None:

            try:

                planned = self.planner(
                    goal_text,
                    context or {},
                )

                normalized = (
                    self._normalize_steps(
                        planned
                    )
                )

                if normalized:

                    return normalized

            except Exception as exc:

                print(
                    "[GoalDecomposer] "
                    f"Planner fallback: {exc}"
                )

        ########################################################
        # Heuristic decomposition for common workflow patterns.
        ########################################################

        return self._heuristic(
            goal_text
        )

    ############################################################
    # HEURISTIC PLANNER
    ############################################################

    def _heuristic(
        self,
        goal: str,
    ) -> list[GoalStep]:

        lower = goal.lower()

        steps: list[
            GoalStep
        ] = []

        def add(
            title,
            description="",
            application="",
            dependencies=None,
        ):

            steps.append(
                GoalStep(
                    step_id=str(
                        uuid.uuid4()
                    ),

                    title=str(
                        title
                    ),

                    description=str(
                        description
                        or
                        ""
                    ),

                    order=len(
                        steps
                    ),

                    application=str(
                        application
                        or
                        ""
                    ),

                    dependencies=list(
                        dependencies
                        or
                        []
                    ),
                )
            )

        ########################################################
        # Multi-app / computer workflow patterns.
        ########################################################

        if any(
            phrase in lower
            for phrase in (
                "download",
                "find online",
                "get from website",
            )
        ):

            add(
                "Open the relevant website",
                "Navigate to the source required for the goal.",
                "browser",
            )

            add(
                "Find the required resource",
                "Locate the requested file, page, or resource.",
                "browser",
                dependencies=[
                    steps[-1].step_id
                ],
            )

            add(
                "Download or capture the resource",
                "Obtain the resource required by the goal.",
                "browser",
                dependencies=[
                    steps[-1].step_id
                ],
            )

            add(
                "Verify the resource",
                "Confirm that the expected resource exists.",
                "filesystem",
                dependencies=[
                    steps[-1].step_id
                ],
            )

        elif any(
            phrase in lower
            for phrase in (
                "create a document",
                "make a document",
                "write a document",
                "prepare a report",
            )
        ):

            add(
                "Open the document application",
                "Open the appropriate document editor.",
                "document",
            )

            add(
                "Create the document",
                "Create the requested document content.",
                "document",
                dependencies=[
                    steps[-1].step_id
                ],
            )

            add(
                "Save the document",
                "Save the completed document.",
                "document",
                dependencies=[
                    steps[-1].step_id
                ],
            )

            add(
                "Verify the document",
                "Confirm that the document was saved correctly.",
                "filesystem",
                dependencies=[
                    steps[-1].step_id
                ],
            )

        elif any(
            phrase in lower
            for phrase in (
                "move",
                "copy",
                "rename",
                "organize",
            )
        ):

            add(
                "Find the source item",
                "Locate the requested file or folder.",
                "filesystem",
            )

            add(
                "Perform the filesystem operation",
                "Apply the requested move, copy, rename, or organization.",
                "filesystem",
                dependencies=[
                    steps[-1].step_id
                ],
            )

            add(
                "Verify the result",
                "Confirm that the requested filesystem change occurred.",
                "filesystem",
                dependencies=[
                    steps[-1].step_id
                ],
            )

        else:

            ####################################################
            # Generic goal decomposition.
            ####################################################

            add(
                "Understand the goal",
                goal,
            )

            add(
                "Execute the required work",
                "Perform the actions needed to accomplish the goal.",
                dependencies=[
                    steps[-1].step_id
                ],
            )

            add(
                "Verify the result",
                "Confirm that the goal was actually accomplished.",
                dependencies=[
                    steps[-1].step_id
                ],
            )

        return steps

    ############################################################
    # NORMALIZATION
    ############################################################

    @staticmethod
    def _normalize_steps(
        planned: Any,
    ) -> list[GoalStep]:

        if not isinstance(
            planned,
            Iterable,
        ) or isinstance(
            planned,
            (str, bytes, dict),
        ):

            return []

        steps = []

        for index, item in enumerate(
            planned
        ):

            if isinstance(
                item,
                GoalStep,
            ):

                steps.append(
                    item
                )

                continue

            if not isinstance(
                item,
                dict,
            ):

                continue

            title = str(
                item.get(
                    "title",
                    item.get(
                        "name",
                        ""
                    )
                )
                or
                ""
            ).strip()

            if not title:
                continue

            steps.append(
                GoalStep(
                    step_id=str(
                        item.get(
                            "step_id",
                            uuid.uuid4()
                        )
                    ),

                    title=title,

                    description=str(
                        item.get(
                            "description",
                            ""
                        )
                        or
                        ""
                    ),

                    order=int(
                        item.get(
                            "order",
                            index,
                        )
                    ),

                    status=str(
                        item.get(
                            "status",
                            "PENDING",
                        )
                        or
                        "PENDING"
                    ),

                    dependencies=list(
                        item.get(
                            "dependencies",
                            []
                        )
                        or
                        []
                    ),

                    application=str(
                        item.get(
                            "application",
                            ""
                        )
                        or
                        ""
                    ),

                    metadata=dict(
                        item.get(
                            "metadata",
                            {}
                        )
                        or
                        {}
                    ),
                )
            )

        steps.sort(
            key=lambda item:
                item.order
        )

        return steps