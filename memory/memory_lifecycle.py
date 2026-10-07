from __future__ import annotations

import math
import time
from typing import Any, Iterable, Optional


class MemoryLifecycleManager:

    """
    Applies lifecycle rules to memories.

    Responsibilities:
        - calculate effective memory strength over time
        - identify stale/low-value memories
        - boost durable/high-importance memories
        - provide cleanup candidates
        - optionally prune through the supplied persistent store

    This layer does not decide what to remember initially; it only
    manages the lifecycle of memories that already exist.
    """

    def __init__(
        self,
        *,
        half_life_days: float = 90.0,
        minimum_strength: float = 0.12,
    ):

        self.half_life_days = max(
            1.0,
            float(
                half_life_days
            ),
        )

        self.minimum_strength = max(
            0.0,
            min(
                1.0,
                float(
                    minimum_strength
                ),
            ),
        )

    ############################################################
    # STRENGTH
    ############################################################

    def effective_strength(
        self,
        memory: dict[str, Any],
        now: Optional[float] = None,
    ) -> float:

        now = (
            time.time()
            if now is None
            else
            float(
                now
            )
        )

        importance = self._clamp(
            memory.get(
                "importance",
                0.5,
            )
        )

        updated_at = self._timestamp(
            memory.get(
                "updated_at",
                0.0,
            )
        )

        last_accessed = self._timestamp(
            memory.get(
                "last_accessed_at",
                0.0,
            )
        )

        reference = max(
            updated_at,
            last_accessed,
        )

        if reference <= 0:

            return importance

        age_days = max(
            0.0,
            (
                now
                -
                reference
            )
            /
            86400.0,
        )

        decay = math.exp(
            -
            (
                age_days
                /
                self.half_life_days
            )
        )

        access_count = max(
            0,
            int(
                memory.get(
                    "access_count",
                    0,
                )
                or
                0
            ),
        )

        access_boost = min(
            0.20,
            math.log1p(
                access_count
            )
            /
            20.0,
        )

        return self._clamp(
            (
                importance
                *
                decay
            )
            +
            access_boost,
        )

    ############################################################
    # CLASSIFY
    ############################################################

    def classify(
        self,
        memory: dict[str, Any],
    ) -> dict[str, Any]:

        strength = self.effective_strength(
            memory
        )

        if strength < self.minimum_strength:

            status = "STALE"

        elif strength < 0.35:

            status = "WEAK"

        elif strength < 0.70:

            status = "ACTIVE"

        else:

            status = "STRONG"

        return {
            "status":
                status,

            "strength":
                strength,

            "memory":
                dict(
                    memory
                ),
        }

    ############################################################
    # CLEANUP CANDIDATES
    ############################################################

    def cleanup_candidates(
        self,
        memories: Iterable[
            dict[str, Any]
        ],
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:

        candidates = []

        for memory in memories:

            if not isinstance(
                memory,
                dict,
            ):
                continue

            classification = self.classify(
                memory
            )

            if classification[
                "status"
            ] == "STALE":

                candidates.append(
                    classification
                )

        candidates.sort(
            key=lambda item:
                item[
                    "strength"
                ]
        )

        return candidates[
            :max(
                0,
                int(
                    limit
                ),
            )
        ]

    ############################################################
    # PRUNE
    ############################################################

    def prune_store(
        self,
        store,
        *,
        limit: int = 50,
    ) -> dict[str, Any]:

        if store is None:

            return {
                "pruned":
                    0,

                "reason":
                    "No persistent memory store supplied.",
            }

        snapshot = store.snapshot(
            limit=max(
                100,
                limit * 4,
            )
        )

        candidates = (
            self.cleanup_candidates(
                snapshot.get(
                    "items",
                    [],
                ),
                limit=limit,
            )
        )

        pruned = 0

        for item in candidates:

            category = item[
                "memory"
            ].get(
                "category",
                "",
            )

            key = item[
                "memory"
            ].get(
                "key",
                "",
            )

            try:

                if store.delete(
                    category,
                    key,
                ):

                    pruned += 1

            except Exception:
                pass

        return {
            "pruned":
                pruned,

            "candidates":
                len(
                    candidates
                ),

            "reason":
                "Stale memories were evaluated for removal.",
        }

    ############################################################
    # HELPERS
    ############################################################

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

    @staticmethod
    def _timestamp(
        value: Any,
    ) -> float:

        try:

            return float(
                value
                or
                0.0
            )

        except Exception:

            return 0.0