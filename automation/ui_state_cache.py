from __future__ import annotations

import time
from copy import deepcopy
from typing import Any, Optional


class UIStateCache:
    """
    Small, task-local cache for semantic UI state.

    Purpose:
        - reuse recent UI intelligence
        - avoid repeatedly processing unchanged UI state
        - provide freshness checks
        - preserve a compact history for short-lived recovery

    This cache never performs computer actions and never decides
    whether a task is complete.
    """

    DEFAULT_TTL = 2.0
    MAX_HISTORY = 8

    def __init__(
        self,
        ttl: float = DEFAULT_TTL,
        max_history: int = MAX_HISTORY,
    ):

        self.ttl = max(
            0.1,
            float(
                ttl
            ),
        )

        self.max_history = max(
            1,
            int(
                max_history
            ),
        )

        self._state: Optional[
            dict[str, Any]
        ] = None

        self._signature = ""

        self._timestamp = 0.0

        self._history: list[
            dict[str, Any]
        ] = []

    ############################################################
    # STORE
    ############################################################

    def store(
        self,
        state: dict[str, Any],
        signature: str = "",
    ):

        if not isinstance(
            state,
            dict,
        ):

            return

        snapshot = deepcopy(
            state
        )

        now = time.monotonic()

        self._state = snapshot

        self._signature = str(
            signature
            or
            ""
        )

        self._timestamp = now

        self._history.append(
            {
                "timestamp":
                    now,

                "signature":
                    self._signature,

                "state":
                    deepcopy(
                        snapshot
                    ),
            }
        )

        if len(
            self._history
        ) > self.max_history:

            del self._history[
                :-
                self.max_history
            ]

    ############################################################
    # READ
    ############################################################

    def get(
        self,
        max_age: Optional[float] = None,
    ) -> Optional[dict[str, Any]]:

        if self._state is None:
            return None

        age = self.age()

        allowed_age = (
            self.ttl
            if max_age is None
            else
            max(
                0.0,
                float(
                    max_age
                ),
            )
        )

        if age > allowed_age:
            return None

        return deepcopy(
            self._state
        )

    ############################################################
    # FRESHNESS
    ############################################################

    def is_fresh(
        self,
        max_age: Optional[float] = None,
    ) -> bool:

        if self._state is None:
            return False

        allowed_age = (
            self.ttl
            if max_age is None
            else
            max(
                0.0,
                float(
                    max_age
                ),
            )
        )

        return (
            self.age()
            <=
            allowed_age
        )

    def age(
        self,
    ) -> float:

        if self._state is None:
            return float(
                "inf"
            )

        return max(
            0.0,
            time.monotonic()
            -
            self._timestamp,
        )

    ############################################################
    # SIGNATURE
    ############################################################

    def signature(
        self,
    ) -> str:

        return self._signature

    def matches(
        self,
        signature: str,
    ) -> bool:

        return (
            bool(
                self._state
            )
            and
            str(
                signature
                or
                ""
            )
            ==
            self._signature
        )

    ############################################################
    # HISTORY
    ############################################################

    def history(
        self,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:

        items = self._history

        if limit is not None:

            count = max(
                0,
                int(
                    limit
                ),
            )

            if count:
                items = items[
                    -count:
                ]

            else:
                items = []

        return deepcopy(
            items
        )

    ############################################################
    # INVALIDATION
    ############################################################

    def invalidate(
        self,
    ):

        self._state = None

        self._signature = ""

        self._timestamp = 0.0

    def clear(
        self,
    ):

        self.invalidate()

        self._history.clear()

    ############################################################
    # COMPACT CONTEXT
    ############################################################

    def compact(
        self,
    ) -> dict[str, Any]:

        state = self.get()

        if state is None:

            return {
                "available":
                    False,

                "age":
                    None,

                "signature":
                    self._signature,

                "state":
                    None,
            }

        return {
            "available":
                True,

            "age":
                self.age(),

            "signature":
                self._signature,

            "state":
                state,
        }


def cache_ui_state(
    cache: UIStateCache,
    state: dict[str, Any],
    signature: str = "",
):

    cache.store(
        state,
        signature=signature,
    )