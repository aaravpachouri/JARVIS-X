from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable, Optional


############################################################
# OBSERVATION CACHE
############################################################

@dataclass
class CachedObservation:

    data: Any = None

    created_at: float = 0.0


class ObservationCache:

    """
    Very short-lived observation cache.

    Purpose:
        Avoid duplicate screenshot/OCR work during the same
        reasoning window.

    Safety:
        The cache expires quickly and can be invalidated
        immediately after an action.
    """

    def __init__(
        self,
        ttl_seconds: float = 0.35,
    ):

        self.ttl_seconds = max(
            0.0,
            float(
                ttl_seconds
            ),
        )

        self._cached = (
            CachedObservation()
        )

    ########################################################
    # GET OR CAPTURE
    ########################################################

    def get(
        self,
        capture: Callable[[], Any],
    ) -> Any:

        if (
            self._cached.data is not None
            and
            self._is_fresh()
        ):

            return self._cached.data

        data = capture()

        self._cached = CachedObservation(
            data=data,
            created_at=monotonic(),
        )

        return data

    ########################################################
    # FRESHNESS
    ########################################################

    def is_fresh(
        self,
    ) -> bool:

        return (
            self._cached.data is not None
            and
            self._is_fresh()
        )

    def _is_fresh(
        self,
    ) -> bool:

        age = (
            monotonic()
            -
            self._cached.created_at
        )

        return age <= self.ttl_seconds

    ########################################################
    # INVALIDATE
    ########################################################

    def invalidate(
        self,
    ) -> None:

        self._cached = (
            CachedObservation()
        )

    ########################################################
    # CLEAR
    ########################################################

    def clear(
        self,
    ) -> None:

        self.invalidate()

    ########################################################
    # AGE
    ########################################################

    def age(
        self,
    ) -> Optional[float]:

        if self._cached.data is None:

            return None

        return (
            monotonic()
            -
            self._cached.created_at
        )

    ########################################################
    # REPRESENTATION
    ########################################################

    def __repr__(
        self,
    ):

        return (
            "<ObservationCache "
            f"fresh={self.is_fresh()} "
            f"age={self.age()}>"
        )