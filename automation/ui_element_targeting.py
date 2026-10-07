from __future__ import annotations

import re
from typing import Any


class UIElementTargeting:

    """
    Semantic UI target resolver.

    Converts UIIntelligence output into candidate interaction targets.

    This class does NOT click, type, move the mouse, or press keys.
    It only identifies where an interaction should occur.
    """

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(
        self,
        ui_intelligence=None,
    ):

        self.ui = (
            ui_intelligence
        )

    ############################################################
    # FIND TEXT
    ############################################################

    def find_text(
        self,
        text: str,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        query = str(
            text or ""
        ).strip()

        if not query:
            return self._not_found(
                "Empty UI text query."
            )

        state = (
            state
            if isinstance(
                state,
                dict,
            )
            else
            getattr(
                self.ui,
                "last_state",
                {},
            )
        )

        elements = state.get(
            "elements",
            [],
        )

        if not isinstance(
            elements,
            list,
        ):

            elements = []

        candidates = []

        query_normalized = (
            self._normalize_text(
                query
            )
        )

        for element in elements:

            if not isinstance(
                element,
                dict,
            ):
                continue

            label = str(
                element.get(
                    "text",
                    "",
                )
                or
                ""
            ).strip()

            if not label:
                continue

            normalized_label = (
                self._normalize_text(
                    label
                )
            )

            score = (
                self._match_score(
                    query_normalized,
                    normalized_label,
                )
            )

            if score <= 0:
                continue

            candidates.append(
                {
                    "element":
                        element,

                    "score":
                        score,

                    "text":
                        label,

                    "bounds":
                        element.get(
                            "bounds"
                        ),
                }
            )

        candidates.sort(
            key=lambda item: item[
                "score"
            ],
            reverse=True,
        )

        if not candidates:

            ####################################################
            # Fallback to visible_text when no structured
            # elements were returned.
            ####################################################

            visible_text = state.get(
                "visible_text",
                [],
            )

            if isinstance(
                visible_text,
                list,
            ):

                for item in visible_text:

                    label = str(
                        item or ""
                    ).strip()

                    score = (
                        self._match_score(
                            query_normalized,
                            self._normalize_text(
                                label
                            ),
                        )
                    )

                    if score > 0:

                        candidates.append(
                            {
                                "element":
                                    {
                                        "text":
                                            label
                                    },

                                "score":
                                    score,

                                "text":
                                    label,

                                "bounds":
                                    None,
                            }
                        )

        if not candidates:

            return self._not_found(
                f"UI text not found: {query}"
            )

        best = candidates[0]

        return {
            "found":
                True,

            "query":
                query,

            "target":
                best,

            "candidates":
                candidates[:8],

            "ambiguous":
                self._is_ambiguous(
                    candidates
                ),
        }

    ############################################################
    # FIND ROLE
    ############################################################

    def find_role(
        self,
        role: str,
        text: str = "",
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        requested_role = (
            str(
                role or ""
            ).strip().lower()
        )

        if not requested_role:
            return self._not_found(
                "Empty UI role."
            )

        state = (
            state
            if isinstance(
                state,
                dict,
            )
            else
            getattr(
                self.ui,
                "last_state",
                {},
            )
        )

        elements = state.get(
            "elements",
            [],
        )

        if not isinstance(
            elements,
            list,
        ):

            elements = []

        text_query = (
            self._normalize_text(
                text
            )
            if text
            else ""
        )

        candidates = []

        for element in elements:

            if not isinstance(
                element,
                dict,
            ):
                continue

            element_role = str(
                element.get(
                    "role",
                    "",
                )
                or
                ""
            ).strip().lower()

            element_type = str(
                element.get(
                    "element_type",
                    "",
                )
                or
                ""
            ).strip().lower()

            label = str(
                element.get(
                    "text",
                    "",
                )
                or
                ""
            )

            role_match = (
                requested_role
                in
                element_role
                or
                requested_role
                in
                element_type
            )

            if not role_match:
                continue

            score = 70.0

            if text_query:

                score += (
                    self._match_score(
                        text_query,
                        self._normalize_text(
                            label
                        ),
                    )
                    * 0.30
                )

            confidence = (
                float(
                    element.get(
                        "confidence",
                        0.0,
                    )
                    or
                    0.0
                )
            )

            score += (
                confidence
                * 10.0
            )

            candidates.append(
                {
                    "element":
                        element,

                    "score":
                        score,

                    "text":
                        label,

                    "bounds":
                        element.get(
                            "bounds"
                        ),
                }
            )

        candidates.sort(
            key=lambda item: item[
                "score"
            ],
            reverse=True,
        )

        if not candidates:

            return self._not_found(
                (
                    "UI role not found: "
                    f"{requested_role}"
                )
            )

        return {
            "found":
                True,

            "role":
                requested_role,

            "query":
                text,

            "target":
                candidates[0],

            "candidates":
                candidates[:8],

            "ambiguous":
                self._is_ambiguous(
                    candidates
                ),
        }

    ############################################################
    # INTERACTION TARGET
    ############################################################

    def resolve(
        self,
        target: str,
        action: str = "click",
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        """
        Resolve natural-language interaction targets.

        Examples:
            Search
            Download button
            address bar
            email field
        """

        target_text = str(
            target or ""
        ).strip()

        normalized_action = str(
            action or "click"
        ).strip().lower()

        if not target_text:

            return self._not_found(
                "Empty interaction target."
            )

        ########################################################
        # Semantic role hints.
        ########################################################

        role = None

        if any(
            word in target_text.lower()
            for word in (
                "button",
                "btn",
            )
        ):

            role = "button"

        elif any(
            word in target_text.lower()
            for word in (
                "field",
                "input",
                "textbox",
                "text box",
            )
        ):

            role = "textbox"

        elif any(
            word in target_text.lower()
            for word in (
                "link",
            )
        ):

            role = "link"

        ########################################################
        # Strip generic role words before text matching.
        ########################################################

        clean_text = re.sub(
            r"\b(button|btn|field|input|textbox|text box|link)\b",
            "",
            target_text,
            flags=re.IGNORECASE,
        ).strip()

        if role:

            result = self.find_role(
                role,
                text=clean_text,
                state=state,
            )

            if result.get(
                "found"
            ):

                result[
                    "action"
                ] = normalized_action

                return result

        ########################################################
        # Generic text targeting.
        ########################################################

        result = self.find_text(
            clean_text
            or
            target_text,
            state=state,
        )

        result[
            "action"
        ] = normalized_action

        return result

    ############################################################
    # SAFETY
    ############################################################

    @staticmethod
    def is_safe_target(
        result: dict[str, Any],
    ) -> bool:

        if not isinstance(
            result,
            dict,
        ):

            return False

        if not result.get(
            "found",
            False,
        ):

            return False

        if result.get(
            "ambiguous",
            False,
        ):

            return False

        target = result.get(
            "target",
            {},
        )

        if not isinstance(
            target,
            dict,
        ):

            return False

        bounds = target.get(
            "bounds"
        )

        return bool(
            bounds
        )

    ############################################################
    # HELPERS
    ############################################################

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            str(
                text or ""
            ).strip().lower(),
        )

    @staticmethod
    def _match_score(
        query: str,
        label: str,
    ) -> float:

        if not query or not label:
            return 0.0

        ########################################################
        # Exact
        ########################################################

        if query == label:
            return 100.0

        ########################################################
        # Exact phrase contained in label
        ########################################################

        if query in label:
            return 90.0

        ########################################################
        # Label contained in query
        ########################################################

        if label in query:
            return 80.0

        ########################################################
        # Token overlap
        ########################################################

        query_tokens = set(
            query.split()
        )

        label_tokens = set(
            label.split()
        )

        if not query_tokens or not label_tokens:
            return 0.0

        overlap = (
            len(
                query_tokens
                &
                label_tokens
            )
            /
            len(
                query_tokens
            )
        )

        return (
            overlap
            *
            70.0
        )

    @staticmethod
    def _is_ambiguous(
        candidates,
    ) -> bool:

        if len(
            candidates
        ) < 2:

            return False

        first = float(
            candidates[0].get(
                "score",
                0.0,
            )
            or
            0.0
        )

        second = float(
            candidates[1].get(
                "score",
                0.0,
            )
            or
            0.0
        )

        return (
            first > 0
            and
            second > 0
            and
            (
                first
                -
                second
            )
            < 8.0
        )

    @staticmethod
    def _not_found(
        reason: str,
    ) -> dict[str, Any]:

        return {
            "found":
                False,

            "target":
                None,

            "candidates":
                [],

            "ambiguous":
                False,

            "reason":
                reason,
        }


def resolve_ui_target(
    target: str,
    state: dict[str, Any],
    action: str = "click",
) -> dict[str, Any]:

    resolver = UIElementTargeting()

    return resolver.resolve(
        target,
        action=action,
        state=state,
    )