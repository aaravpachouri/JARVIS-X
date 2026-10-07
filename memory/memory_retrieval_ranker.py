from __future__ import annotations

import math
import time
from typing import Any, Iterable, Optional


class MemoryRetrievalRanker:

    """
    Scores persistent/context memories for a reasoning query.

    Ranking signals:
        - textual relevance
        - memory importance
        - recency
        - access frequency
        - category match

    This is a retrieval/ranking layer only. It does not create,
    delete, or persist memories.
    """

    def __init__(
        self,
        *,
        recency_half_life_days: float = 30.0,
        importance_weight: float = 0.25,
        recency_weight: float = 0.20,
        access_weight: float = 0.10,
        relevance_weight: float = 0.45,
    ):

        self.recency_half_life_days = max(
            0.1,
            float(
                recency_half_life_days
            ),
        )

        self.importance_weight = float(
            importance_weight
        )

        self.recency_weight = float(
            recency_weight
        )

        self.access_weight = float(
            access_weight
        )

        self.relevance_weight = float(
            relevance_weight
        )

    ############################################################
    # RANK
    ############################################################

    def rank(
        self,
        query: str,
        memories: Iterable[
            Any
        ],
        *,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:

        query = str(
            query
            or
            ""
        ).strip().lower()

        if not query:
            return []

        category_filter = str(
            category
            or
            ""
        ).strip().lower()

        ranked = []

        for memory in memories:

            item = self._normalize_memory(
                memory
            )

            if not item:
                continue

            if (
                category_filter
                and
                str(
                    item.get(
                        "category",
                        ""
                    )
                ).lower()
                !=
                category_filter
            ):
                continue

            relevance = self._text_relevance(
                query,
                item,
            )

            if relevance <= 0:
                continue

            importance = self._clamp(
                item.get(
                    "importance",
                    0.5
                ),
            )

            recency = self._recency_score(
                item.get(
                    "updated_at",
                    0.0
                ),
            )

            access = self._access_score(
                item.get(
                    "access_count",
                    0
                ),
            )

            category_score = (
                1.0
                if (
                    category_filter
                    and
                    str(
                        item.get(
                            "category",
                            ""
                        )
                    ).lower()
                    ==
                    category_filter
                )
                else
                0.0
            )

            score = (
                (
                    self.relevance_weight
                    *
                    relevance
                )
                +
                (
                    self.importance_weight
                    *
                    importance
                )
                +
                (
                    self.recency_weight
                    *
                    recency
                )
                +
                (
                    self.access_weight
                    *
                    access
                )
                +
                (
                    0.10
                    *
                    category_score
                )
            )

            ranked.append(
                {
                    "memory":
                        item,

                    "score":
                        round(
                            score,
                            6
                        ),

                    "signals":
                        {
                            "relevance":
                                round(
                                    relevance,
                                    6
                                ),

                            "importance":
                                round(
                                    importance,
                                    6
                                ),

                            "recency":
                                round(
                                    recency,
                                    6
                                ),

                            "access":
                                round(
                                    access,
                                    6
                                ),
                        },
                }
            )

        ranked.sort(
            key=lambda item: (
                item["score"],
                item[
                    "memory"
                ].get(
                    "importance",
                    0.0
                ),
            ),
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

    ############################################################
    # TEXT RELEVANCE
    ############################################################

    @staticmethod
    def _text_relevance(
        query: str,
        item: dict[str, Any],
    ) -> float:

        key = str(
            item.get(
                "key",
                ""
            )
            or
            ""
        ).lower()

        value = str(
            item.get(
                "value",
                ""
            )
            or
            ""
        ).lower()

        category = str(
            item.get(
                "category",
                ""
            )
            or
            ""
        ).lower()

        source = str(
            item.get(
                "source",
                ""
            )
            or
            ""
        ).lower()

        query_tokens = {
            token
            for token
            in query.split()
            if token
        }

        if not query_tokens:
            return 0.0

        fields = {
            "key":
                key,

            "value":
                value,

            "category":
                category,

            "source":
                source,
        }

        score = 0.0

        for token in query_tokens:

            if token in key:
                score += 1.0

            elif token in value:
                score += 0.8

            elif token in category:
                score += 0.5

            elif token in source:
                score += 0.3

        token_score = (
            score
            /
            len(
                query_tokens
            )
        )

        if query in key:
            token_score += 0.35

        elif query in value:
            token_score += 0.20

        return min(
            1.0,
            token_score,
        )

    ############################################################
    # RECENCY
    ############################################################

    def _recency_score(
        self,
        updated_at: Any,
    ) -> float:

        try:

            timestamp = float(
                updated_at
                or
                0.0
            )

        except Exception:

            return 0.0

        if timestamp <= 0:

            return 0.0

        age_seconds = max(
            0.0,
            time.time()
            -
            timestamp,
        )

        age_days = (
            age_seconds
            /
            86400.0
        )

        return math.exp(
            -
            (
                age_days
                /
                self.recency_half_life_days
            )
        )

    ############################################################
    # ACCESS SCORE
    ############################################################

    @staticmethod
    def _access_score(
        access_count: Any,
    ) -> float:

        try:

            count = max(
                0,
                int(
                    access_count
                    or
                    0
                ),
            )

        except Exception:

            count = 0

        ########################################################
        # Log scaling prevents heavily-used memories from
        # overwhelming relevance.
        ########################################################

        return min(
            1.0,
            math.log1p(
                count
            )
            /
            math.log(
                11.0
            ),
        )

    ############################################################
    # HELPERS
    ############################################################

    @staticmethod
    def _normalize_memory(
        memory: Any,
    ) -> dict[str, Any]:

        if isinstance(
            memory,
            dict
        ):

            return dict(
                memory
            )

        if hasattr(
            memory,
            "to_dict"
        ):

            try:

                value = memory.to_dict()

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
        value: Any,
    ) -> float:

        try:

            return max(
                0.0,
                min(
                    1.0,
                    float(
                        value
                        or
                        0.0
                    ),
                ),
            )

        except Exception:

            return 0.0


def rank_memories(
    query: str,
    memories,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:

    return MemoryRetrievalRanker().rank(
        query,
        memories,
        limit=limit,
    )