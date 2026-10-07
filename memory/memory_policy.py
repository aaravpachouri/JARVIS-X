from __future__ import annotations

import re
from typing import Any, Optional


class MemoryPolicy:

    """
    Controls what JARVIS should and should not persist.

    This is a policy layer, not a storage layer.

    The policy intentionally favors explicit user requests and
    stable/useful information over transient conversation details.
    """

    DEFAULT_IMPORTANCE = 0.5

    def __init__(
        self,
        *,
        minimum_importance: float = 0.35,
    ):

        self.minimum_importance = max(
            0.0,
            min(
                1.0,
                float(
                    minimum_importance
                ),
            ),
        )

        self.forbidden_patterns = [
            r"\bpassword\b",
            r"\bpasscode\b",
            r"\botp\b",
            r"\bone[- ]time password\b",
            r"\bapi key\b",
            r"\bsecret key\b",
            r"\bprivate key\b",
            r"\bcredit card\b",
            r"\bcard number\b",
            r"\bcvv\b",
        ]

        self.transient_patterns = [
            r"\bright now\b",
            r"\bfor a second\b",
            r"\btemporarily\b",
            r"\bjust this once\b",
            r"\bcurrently\b",
        ]

    ############################################################
    # EVALUATE
    ############################################################

    def evaluate(
        self,
        *,
        category: str,
        key: str,
        value: Any,
        explicit: bool = False,
        importance: Optional[float] = None,
        source_text: str = "",
    ) -> dict[str, Any]:

        category = str(
            category
            or
            "general"
        ).strip().lower()

        key = str(
            key
            or
            ""
        ).strip()

        value_text = str(
            value
            or
            ""
        )

        combined = (
            f"{key} {value_text} {source_text}"
        ).lower()

        ########################################################
        # Sensitive information should never be auto-persisted.
        ########################################################

        for pattern in self.forbidden_patterns:

            if re.search(
                pattern,
                combined,
                flags=re.IGNORECASE,
            ):

                return {
                    "allowed":
                        False,

                    "importance":
                        0.0,

                    "reason":
                        "Sensitive credential/payment information should not be persisted.",
                }

        ########################################################
        # Explicit memory requests receive priority.
        ########################################################

        if explicit:

            final_importance = (
                self._importance(
                    importance
                    if importance is not None
                    else
                    0.75
                )
            )

            return {
                "allowed":
                    True,

                "importance":
                    final_importance,

                "reason":
                    "User explicitly requested that this information be remembered.",
            }

        ########################################################
        # Reject highly transient information.
        ########################################################

        for pattern in self.transient_patterns:

            if re.search(
                pattern,
                combined,
                flags=re.IGNORECASE,
            ):

                return {
                    "allowed":
                        False,

                    "importance":
                        0.0,

                    "reason":
                        "Information appears transient and is not an explicit memory request.",
                }

        ########################################################
        # Categories that are usually durable.
        ########################################################

        durable_categories = {
            "preference",
            "profile",
            "workflow",
            "project",
            "setting",
            "important",
        }

        if category in durable_categories:

            final_importance = (
                self._importance(
                    importance
                    if importance is not None
                    else
                    0.65
                )
            )

            return {
                "allowed":
                    final_importance
                    >=
                    self.minimum_importance,

                "importance":
                    final_importance,

                "reason":
                    "Category represents potentially durable context.",
            }

        ########################################################
        # General memory: require a meaningful importance value.
        ########################################################

        final_importance = (
            self._importance(
                importance
                if importance is not None
                else
                self.DEFAULT_IMPORTANCE
            )
        )

        return {
            "allowed":
                final_importance
                >=
                self.minimum_importance,

            "importance":
                final_importance,

            "reason":
                "General memory passes the configured importance threshold.",
        }

    ############################################################
    # EXPLICIT REMEMBER DETECTION
    ############################################################

    @staticmethod
    def is_explicit_remember_request(
        text: str,
    ) -> bool:

        value = str(
            text
            or
            ""
        ).strip().lower()

        patterns = (
            r"\bremember\b",
            r"\bkeep this in mind\b",
            r"\bsave this\b",
            r"\bstore this\b",
            r"\bdon't forget\b",
            r"\bdo not forget\b",
        )

        return any(
            re.search(
                pattern,
                value,
            )
            for pattern in patterns
        )

    ############################################################
    # IMPORTANCE
    ############################################################

    @staticmethod
    def _importance(
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