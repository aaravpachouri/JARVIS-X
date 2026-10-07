from __future__ import annotations

import time
from typing import Any, Optional


class UIStateTrust:

    """
    Tracks whether cached UI state is trustworthy enough to reuse.

    This is intentionally separate from UIIntelligence and the
    ComputerUseAgent. It answers one narrow question:

        "Can JARVIS safely rely on this UI observation right now?"

    Trust is reduced when:
        - the observation becomes stale
        - the UI is loading
        - an error/dialog is visible
        - the state is low-confidence
        - the foreground application changes

    It never executes actions.
    """

    DEFAULT_MAX_AGE = 2.0
    DEFAULT_MIN_CONFIDENCE = 0.55

    def __init__(
        self,
        max_age: float = DEFAULT_MAX_AGE,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ):

        self.max_age = max(
            0.1,
            float(
                max_age
            ),
        )

        self.min_confidence = max(
            0.0,
            min(
                1.0,
                float(
                    min_confidence
                ),
            ),
        )

        self._last_foreground = None

    ############################################################
    # TRUST EVALUATION
    ############################################################

    def evaluate(
        self,
        state: Optional[dict[str, Any]],
        age: Optional[float] = None,
    ) -> dict[str, Any]:

        if not isinstance(
            state,
            dict,
        ):

            return {
                "trusted": False,
                "score": 0.0,
                "reason": "No UI state is available.",
            }

        if age is None:
            age = 0.0

        try:
            age = float(
                age
            )
        except Exception:
            age = 999.0

        confidence = self._confidence(
            state
        )

        reasons = []

        ########################################################
        # Freshness
        ########################################################

        if age > self.max_age:

            reasons.append(
                "UI observation is stale."
            )

        ########################################################
        # Confidence
        ########################################################

        if confidence < self.min_confidence:

            reasons.append(
                "UI observation confidence is too low."
            )

        ########################################################
        # Transitional state
        ########################################################

        if state.get(
            "loading",
            False,
        ):

            reasons.append(
                "UI appears to be loading."
            )

        ########################################################
        # Error state
        ########################################################

        if state.get(
            "error_visible",
            False,
        ):

            reasons.append(
                "UI currently shows an error state."
            )

        ########################################################
        # Confirmation / dialog state
        ########################################################

        if state.get(
            "confirmation_visible",
            False,
        ):

            reasons.append(
                "UI contains a confirmation state."
            )

        ########################################################
        # Foreground tracking
        ########################################################

        foreground = state.get(
            "foreground",
            {},
        )

        if not isinstance(
            foreground,
            dict,
        ):

            foreground = {}

        current_foreground = (
            foreground.get(
                "title",
                "",
            ),
            foreground.get(
                "pid",
                0,
            ),
            foreground.get(
                "process_name",
                "",
            ),
        )

        if (
            self._last_foreground is not None
            and
            current_foreground
            !=
            self._last_foreground
        ):

            reasons.append(
                "Foreground application/window changed."
            )

        self._last_foreground = (
            current_foreground
        )

        trusted = (
            not reasons
        )

        if trusted:

            reason = (
                "UI state is fresh and sufficiently reliable."
            )

        else:

            reason = (
                " ".join(
                    reasons
                )
            )

        return {
            "trusted":
                trusted,

            "score":
                self._trust_score(
                    confidence,
                    age,
                    reasons,
                ),

            "confidence":
                confidence,

            "age":
                age,

            "reason":
                reason,

            "refresh_required":
                not trusted,
        }

    ############################################################
    # CURRENT FOREGROUND
    ############################################################

    def foreground_changed(
        self,
        state: Optional[dict[str, Any]],
    ) -> bool:

        if not isinstance(
            state,
            dict,
        ):

            return True

        foreground = state.get(
            "foreground",
            {},
        )

        if not isinstance(
            foreground,
            dict,
        ):

            foreground = {}

        current = (
            foreground.get(
                "title",
                "",
            ),
            foreground.get(
                "pid",
                0,
            ),
            foreground.get(
                "process_name",
                "",
            ),
        )

        changed = (
            self._last_foreground is not None
            and
            current
            !=
            self._last_foreground
        )

        self._last_foreground = current

        return changed

    ############################################################
    # HELPERS
    ############################################################

    @staticmethod
    def _confidence(
        state,
    ) -> float:

        try:
            return max(
                0.0,
                min(
                    1.0,
                    float(
                        state.get(
                            "confidence",
                            0.0,
                        )
                        or
                        0.0
                    ),
                ),
            )
        except Exception:
            return 0.0

    @staticmethod
    def _trust_score(
        confidence,
        age,
        reasons,
    ) -> float:

        freshness = max(
            0.0,
            min(
                1.0,
                1.0
                -
                (
                    float(age)
                    /
                    5.0
                ),
            ),
        )

        penalty = min(
            0.8,
            0.15
            *
            len(
                reasons
            ),
        )

        return max(
            0.0,
            min(
                1.0,
                (
                    0.65
                    *
                    float(
                        confidence
                    )
                )
                +
                (
                    0.35
                    *
                    freshness
                )
                -
                penalty,
            ),
        )


class UIStateTrustGate:

    """
    Convenience wrapper combining UIStateCache freshness with
    UIStateTrust evaluation.
    """

    def __init__(
        self,
        cache,
        trust: Optional[UIStateTrust] = None,
    ):

        self.cache = cache

        self.trust = (
            trust
            or
            UIStateTrust()
        )

    def evaluate_cached(
        self,
        max_age: Optional[float] = None,
    ) -> dict[str, Any]:

        state = self.cache.get(
            max_age=max_age
        )

        age = self.cache.age()

        result = self.trust.evaluate(
            state,
            age=age,
        )

        result[
            "cache_available"
        ] = (
            state is not None
        )

        return result

    def should_refresh(
        self,
    ) -> bool:

        return not self.evaluate_cached().get(
            "trusted",
            False,
        )