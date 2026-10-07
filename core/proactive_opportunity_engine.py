from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ProactiveOpportunity:

    opportunity_id: str

    title: str

    reason: str

    trigger_type: str

    confidence: float = 0.0

    created_at: float = field(
        default_factory=time.time
    )

    expires_at: Optional[float] = None

    goal_id: str = ""

    suggested_action: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    status: str = "PENDING"

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "opportunity_id":
                self.opportunity_id,

            "title":
                self.title,

            "reason":
                self.reason,

            "trigger_type":
                self.trigger_type,

            "confidence":
                self.confidence,

            "created_at":
                self.created_at,

            "expires_at":
                self.expires_at,

            "goal_id":
                self.goal_id,

            "suggested_action":
                self.suggested_action,

            "metadata":
                dict(
                    self.metadata
                ),

            "status":
                self.status,
        }


class ProactiveOpportunityEngine:

    """
    Phase 8.10 foundation: proactive intelligence.

    This module identifies potentially useful next actions from
    existing JARVIS state.

    IMPORTANT:
        It is suggestion-first.
        It does not silently execute actions.

    Inputs may include:
        - active goal
        - goal progress
        - memory/context
        - pending workflow state
        - runtime signals

    A future policy layer can decide whether an opportunity should
    become an actual task or simply be presented to the user.
    """

    def __init__(
        self,
        detector: Optional[
            Callable[..., Any]
        ] = None,
    ):

        self.detector = detector

        self._opportunities: dict[
            str,
            ProactiveOpportunity
        ] = {}

    ############################################################
    # DETECT
    ############################################################

    def detect(
        self,
        *,
        goal_context: Optional[
            dict[str, Any]
        ] = None,
        memory_context: Optional[
            dict[str, Any]
        ] = None,
        runtime_context: Optional[
            dict[str, Any]
        ] = None,
    ) -> list[ProactiveOpportunity]:

        goal_context = dict(
            goal_context
            or
            {}
        )

        memory_context = dict(
            memory_context
            or
            {}
        )

        runtime_context = dict(
            runtime_context
            or
            {}
        )

        ########################################################
        # Custom detector first.
        ########################################################

        if self.detector is not None:

            try:

                result = self.detector(
                    goal_context,
                    memory_context,
                    runtime_context,
                )

                normalized = (
                    self._normalize(
                        result
                    )
                )

                if normalized:

                    self._store(
                        normalized
                    )

                    return normalized

            except Exception as exc:

                print(
                    "[ProactiveOpportunityEngine] "
                    f"Custom detector fallback: {exc}"
                )

        opportunities = []

        active_goal = goal_context.get(
            "active_goal"
        )

        ########################################################
        # Goal-based opportunity.
        #
        # If a goal exists but no current progress/task signal is
        # available, suggest reviewing/continuing it rather than
        # executing anything automatically.
        ########################################################

        if isinstance(
            active_goal,
            dict
        ):

            status = str(
                active_goal.get(
                    "status",
                    ""
                )
                or
                ""
            ).upper()

            progress = float(
                active_goal.get(
                    "progress",
                    0.0
                )
                or
                0.0
            )

            title = str(
                active_goal.get(
                    "title",
                    ""
                )
                or
                ""
            ).strip()

            goal_id = str(
                active_goal.get(
                    "goal_id",
                    ""
                )
                or
                ""
            )

            if (
                title
                and
                status == "ACTIVE"
                and
                progress < 1.0
            ):

                opportunities.append(
                    ProactiveOpportunity(
                        opportunity_id=str(
                            uuid.uuid4()
                        ),

                        title="Continue active goal",

                        reason=(
                            "An active user goal is still "
                            "in progress."
                        ),

                        trigger_type="GOAL_PROGRESS",

                        confidence=0.72,

                        goal_id=goal_id,

                        suggested_action=(
                            f"Continue working on: {title}"
                        ),
                    )
                )

        ########################################################
        # Runtime signal: waiting/stalled workflow.
        ########################################################

        workflow = runtime_context.get(
            "workflow"
        )

        if isinstance(
            workflow,
            dict
        ):

            workflow_status = str(
                workflow.get(
                    "status",
                    ""
                )
                or
                ""
            ).upper()

            if workflow_status in {
                "PAUSED",
                "WAITING",
                "BLOCKED",
            }:

                opportunities.append(
                    ProactiveOpportunity(
                        opportunity_id=str(
                            uuid.uuid4()
                        ),

                        title="Review paused workflow",

                        reason=(
                            "A workflow is waiting or blocked "
                            "and may need attention."
                        ),

                        trigger_type="WORKFLOW_BLOCKED",

                        confidence=0.78,

                        suggested_action=(
                            "Review the workflow state before "
                            "taking another action."
                        ),
                    )
                )

        ########################################################
        # Memory signal: useful context exists, but suggestion
        # remains non-executing.
        ########################################################

        memory_count = int(
            memory_context.get(
                "memory_count",
                0
            )
            or
            0
        )

        if (
            memory_count > 0
            and
            active_goal
        ):

            opportunities.append(
                ProactiveOpportunity(
                    opportunity_id=str(
                        uuid.uuid4()
                    ),

                    title="Use relevant remembered context",

                    reason=(
                        "Relevant saved context is available "
                        "for the active goal."
                    ),

                    trigger_type="MEMORY_RELEVANCE",

                    confidence=0.68,

                    goal_id=str(
                        active_goal.get(
                            "goal_id",
                            ""
                        )
                        or
                        ""
                    ),

                    suggested_action=(
                        "Include the relevant memory context "
                        "before planning the next step."
                    ),
                )
            )

        self._store(
            opportunities
        )

        return opportunities

    ############################################################
    # READ
    ############################################################

    def pending(
        self,
        limit: int = 10,
    ) -> list[ProactiveOpportunity]:

        items = [
            item
            for item
            in self._opportunities.values()
            if item.status == "PENDING"
        ]

        items.sort(
            key=lambda item: (
                item.confidence,
                item.created_at,
            ),
            reverse=True,
        )

        return items[
            :max(
                0,
                int(
                    limit
                ),
            )
        ]

    ############################################################
    # ACCEPT / DISMISS
    ############################################################

    def accept(
        self,
        opportunity_id: str,
    ) -> bool:

        item = self._opportunities.get(
            str(
                opportunity_id
                or
                ""
            ).strip()
        )

        if item is None:
            return False

        item.status = "ACCEPTED"

        return True

    def dismiss(
        self,
        opportunity_id: str,
    ) -> bool:

        item = self._opportunities.get(
            str(
                opportunity_id
                or
                ""
            ).strip()
        )

        if item is None:
            return False

        item.status = "DISMISSED"

        return True

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "opportunities":
                [
                    item.to_dict()
                    for item
                    in self.pending(
                        50
                    )
                ]
        }

    ############################################################
    # HELPERS
    ############################################################

    def _store(
        self,
        items,
    ):

        for item in items:

            if isinstance(
                item,
                ProactiveOpportunity,
            ):

                self._opportunities[
                    item.opportunity_id
                ] = item

    @staticmethod
    def _normalize(
        result,
    ) -> list[ProactiveOpportunity]:

        if not isinstance(
            result,
            (list, tuple),
        ):

            return []

        normalized = []

        for item in result:

            if isinstance(
                item,
                ProactiveOpportunity,
            ):

                normalized.append(
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
                    ""
                )
                or
                ""
            ).strip()

            if not title:
                continue

            normalized.append(
                ProactiveOpportunity(
                    opportunity_id=str(
                        item.get(
                            "opportunity_id",
                            uuid.uuid4()
                        )
                    ),

                    title=title,

                    reason=str(
                        item.get(
                            "reason",
                            ""
                        )
                        or
                        ""
                    ),

                    trigger_type=str(
                        item.get(
                            "trigger_type",
                            "CUSTOM",
                        )
                        or
                        "CUSTOM"
                    ),

                    confidence=max(
                        0.0,
                        min(
                            1.0,
                            float(
                                item.get(
                                    "confidence",
                                    0.0,
                                )
                                or
                                0.0
                            ),
                        ),
                    ),

                    expires_at=item.get(
                        "expires_at"
                    ),

                    goal_id=str(
                        item.get(
                            "goal_id",
                            ""
                        )
                        or
                        ""
                    ),

                    suggested_action=str(
                        item.get(
                            "suggested_action",
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

                    status=str(
                        item.get(
                            "status",
                            "PENDING",
                        )
                        or
                        "PENDING"
                    ),
                )
            )

        return normalized


def detect_proactive_opportunities(
    *,
    goal_context=None,
    memory_context=None,
    runtime_context=None,
):
    return ProactiveOpportunityEngine().detect(
        goal_context=goal_context,
        memory_context=memory_context,
        runtime_context=runtime_context,
    )