from __future__ import annotations

import math
import time
from typing import Any, Iterable


class ProactiveOpportunityRanker:

    """
    Ranks proactive triggers/opportunities by usefulness.

    Ranking considers:
        - confidence
        - priority
        - goal relevance
        - urgency
        - freshness

    This class does not execute or approve an opportunity.
    """

    def __init__(
        self,
        *,
        confidence_weight: float = 0.30,
        priority_weight: float = 0.25,
        goal_weight: float = 0.20,
        urgency_weight: float = 0.15,
        freshness_weight: float = 0.10,
    ):

        self.confidence_weight = confidence_weight
        self.priority_weight = priority_weight
        self.goal_weight = goal_weight
        self.urgency_weight = urgency_weight
        self.freshness_weight = freshness_weight

    def rank(
        self,
        items: Iterable[Any],
        *,
        active_goal_id: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:

        ranked = []

        for item in items:

            data = self._normalize(
                item
            )

            if not data:
                continue

            confidence = self._clamp(
                data.get(
                    "confidence",
                    0.0
                )
            )

            priority = (
                self._clamp(
                    float(
                        data.get(
                            "priority",
                            0,
                        )
                        or
                        0
                    )
                    /
                    100.0
                )
            )

            goal_relevance = (
                1.0
                if (
                    active_goal_id
                    and
                    str(
                        data.get(
                            "goal_id",
                            ""
                        )
                        or
                        ""
                    )
                    ==
                    str(
                        active_goal_id
                    )
                )
                else
                0.0
            )

            urgency = self._urgency(
                data
            )

            freshness = self._freshness(
                data
            )

            score = (
                self.confidence_weight
                *
                confidence
                +
                self.priority_weight
                *
                priority
                +
                self.goal_weight
                *
                goal_relevance
                +
                self.urgency_weight
                *
                urgency
                +
                self.freshness_weight
                *
                freshness
            )

            ranked.append(
                {
                    "opportunity":
                        data,

                    "score":
                        round(
                            score,
                            6
                        ),

                    "signals":
                        {
                            "confidence":
                                confidence,

                            "priority":
                                priority,

                            "goal_relevance":
                                goal_relevance,

                            "urgency":
                                urgency,

                            "freshness":
                                freshness,
                        },
                }
            )

        ranked.sort(
            key=lambda item:
                item["score"],
            reverse=True,
        )

        return ranked[
            :max(
                0,
                int(
                    limit
                ),
            )
        ]

    @staticmethod
    def _urgency(
        item: dict[str, Any],
    ) -> float:

        metadata = item.get(
            "metadata",
            {}
        )

        if not isinstance(
            metadata,
            dict,
        ):
            return 0.0

        remaining = metadata.get(
            "seconds_remaining"
        )

        if remaining is None:
            return 0.0

        try:
            remaining = float(
                remaining
            )
        except Exception:
            return 0.0

        if remaining <= 0:
            return 1.0

        return math.exp(
            -
            remaining
            /
            86400.0
        )

    @staticmethod
    def _freshness(
        item: dict[str, Any],
    ) -> float:

        try:
            created = float(
                item.get(
                    "created_at",
                    0.0
                )
                or
                0.0
            )
        except Exception:
            return 0.0

        if created <= 0:
            return 0.0

        age = max(
            0.0,
            time.time()
            -
            created,
        )

        return math.exp(
            -
            age
            /
            3600.0
        )

    @staticmethod
    def _normalize(
        item: Any,
    ) -> dict[str, Any]:

        if isinstance(
            item,
            dict
        ):
            return dict(
                item
            )

        if hasattr(
            item,
            "to_dict"
        ):

            try:

                value = item.to_dict()

                if isinstance(
                    value,
                    dict
                ):
                    return value

            except Exception:
                pass

        return {}

    @staticmethod
    def _clamp(
        value: float,
    ) -> float:

        return max(
            0.0,
            min(
                1.0,
                float(
                    value
                ),
            ),
        )


def rank_proactive_opportunities(
    items,
    *,
    active_goal_id: str = "",
    limit: int = 10,
):
    return ProactiveOpportunityRanker().rank(
        items,
        active_goal_id=active_goal_id,
        limit=limit,
    )