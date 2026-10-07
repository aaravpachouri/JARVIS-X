from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class UIElement:
    element_type: str = ""
    text: str = ""
    role: str = ""
    state: str = ""
    confidence: float = 0.0
    bounds: Optional[dict[str, int]] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_type": self.element_type,
            "text": self.text,
            "role": self.role,
            "state": self.state,
            "confidence": float(self.confidence),
            "bounds": self.bounds,
            "metadata": dict(self.metadata),
        }


class UIIntelligence:
    """
    Modular semantic UI-state layer.

    It analyzes already-produced vision/OCR information and exposes
    compact state for ComputerUseAgent. It does not perform actions.
    """

    def __init__(self):
        self.last_state: dict[str, Any] = {}

    def build_state(
        self,
        vision_result: Any = None,
        ocr_text: str = "",
        foreground: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:

        data = self._normalize(
            vision_result
        )

        visible_text = self._extract_text(
            data
        )

        visible_text.extend(
            self._split_text(
                ocr_text
            )
        )

        visible_text = self._dedupe_text(
            visible_text
        )

        elements = self._extract_elements(
            data
        )

        joined = " ".join(
            visible_text
        )

        state = {
            "foreground":
                dict(
                    foreground
                    or
                    {}
                ),

            "visible_text":
                visible_text,

            "elements":
                elements,

            "dialogs":
                self._detect_dialogs(
                    elements,
                    joined,
                ),

            "loading":
                self._contains(
                    joined,
                    (
                        "loading",
                        "please wait",
                        "starting",
                        "initializing",
                        "connecting",
                    ),
                ),

            "login_required":
                self._contains(
                    joined,
                    (
                        "sign in",
                        "log in",
                        "login",
                        "password",
                        "email address",
                    ),
                ),

            "error_visible":
                self._contains(
                    joined,
                    (
                        "error",
                        "failed",
                        "failure",
                        "not responding",
                        "something went wrong",
                        "access denied",
                    ),
                ),

            "confirmation_visible":
                self._contains(
                    joined,
                    (
                        "are you sure",
                        "confirm",
                        "confirmation",
                        "save changes",
                    ),
                ),

            "confidence":
                self._confidence(
                    visible_text,
                    elements,
                ),
        }

        self.last_state = state

        return state

    def compact_context(
        self,
        state: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:

        state = (
            state
            if isinstance(state, dict)
            else self.last_state
        )

        return {
            "foreground":
                dict(
                    state.get(
                        "foreground",
                        {}
                    )
                    or
                    {}
                ),

            "visible_text":
                list(
                    state.get(
                        "visible_text",
                        []
                    )[:40]
                ),

            "elements":
                [
                    {
                        "type":
                            item.get(
                                "element_type",
                                ""
                            ),

                        "role":
                            item.get(
                                "role",
                                ""
                            ),

                        "text":
                            item.get(
                                "text",
                                ""
                            ),

                        "state":
                            item.get(
                                "state",
                                ""
                            ),

                        "bounds":
                            item.get(
                                "bounds"
                            ),

                        "confidence":
                            item.get(
                                "confidence",
                                0.0
                            ),
                    }
                    for item in state.get(
                        "elements",
                        []
                    )[:30]
                ],

            "dialogs":
                list(
                    state.get(
                        "dialogs",
                        []
                    )[:10]
                ),

            "loading":
                bool(
                    state.get(
                        "loading",
                        False
                    )
                ),

            "login_required":
                bool(
                    state.get(
                        "login_required",
                        False
                    )
                ),

            "error_visible":
                bool(
                    state.get(
                        "error_visible",
                        False
                    )
                ),

            "confirmation_visible":
                bool(
                    state.get(
                        "confirmation_visible",
                        False
                    )
                ),

            "confidence":
                float(
                    state.get(
                        "confidence",
                        0.0
                    )
                    or
                    0.0
                ),
        }

    @staticmethod
    def _normalize(
        value: Any
    ) -> Any:

        if isinstance(
            value,
            dict
        ):
            return value

        if isinstance(
            value,
            str
        ):

            raw = value.strip()

            if not raw:
                return {}

            try:
                parsed = json.loads(
                    raw
                )

                if isinstance(
                    parsed,
                    dict
                ):
                    return parsed

            except Exception:
                pass

            return {
                "text":
                    raw
            }

        return {}

    def _extract_text(
        self,
        data: Any
    ) -> list[str]:

        result: list[str] = []

        def walk(
            value
        ):

            if isinstance(
                value,
                dict
            ):

                for key, child in value.items():

                    key_lower = str(
                        key
                    ).lower()

                    if key_lower in {
                        "text",
                        "label",
                        "title",
                        "name",
                        "content",
                        "visible_text",
                    }:

                        if isinstance(
                            child,
                            str
                        ):

                            result.extend(
                                self._split_text(
                                    child
                                )
                            )

                        elif isinstance(
                            child,
                            list
                        ):

                            for item in child:

                                if isinstance(
                                    item,
                                    str
                                ):

                                    result.extend(
                                        self._split_text(
                                            item
                                        )
                                    )

                    if isinstance(
                        child,
                        (dict, list)
                    ):

                        walk(
                            child
                        )

            elif isinstance(
                value,
                list
            ):

                for item in value:
                    walk(
                        item
                    )

        walk(
            data
        )

        return result

    def _extract_elements(
        self,
        data: Any
    ) -> list[dict[str, Any]]:

        result: list[dict[str, Any]] = []

        def walk(
            value
        ):

            if isinstance(
                value,
                dict
            ):

                element_type = str(
                    value.get(
                        "type",
                        value.get(
                            "element_type",
                            ""
                        )
                    )
                    or
                    ""
                )

                role = str(
                    value.get(
                        "role",
                        ""
                    )
                    or
                    ""
                )

                text = str(
                    value.get(
                        "text",
                        value.get(
                            "label",
                            value.get(
                                "name",
                                ""
                            )
                        )
                    )
                    or
                    ""
                )

                bounds = self._bounds(
                    value.get(
                        "bounds",
                        value.get(
                            "bbox"
                        )
                    )
                )

                if (
                    element_type
                    or
                    role
                    or
                    text
                    or
                    bounds
                ):

                    result.append(
                        UIElement(
                            element_type=element_type,
                            text=text,
                            role=role,
                            state=str(
                                value.get(
                                    "state",
                                    ""
                                )
                                or
                                ""
                            ),
                            confidence=self._float(
                                value.get(
                                    "confidence",
                                    0.0
                                )
                            ),
                            bounds=bounds,
                        ).to_dict()
                    )

                for child in value.values():

                    if isinstance(
                        child,
                        (dict, list)
                    ):
                        walk(
                            child
                        )

            elif isinstance(
                value,
                list
            ):

                for item in value:
                    walk(
                        item
                    )

        walk(
            data
        )

        seen = set()
        unique = []

        for item in result:

            key = (
                item.get(
                    "element_type",
                    ""
                ),
                item.get(
                    "role",
                    ""
                ),
                item.get(
                    "text",
                    ""
                ),
                str(
                    item.get(
                        "bounds"
                    )
                ),
            )

            if key not in seen:

                seen.add(
                    key
                )

                unique.append(
                    item
                )

        return unique

    @staticmethod
    def _detect_dialogs(
        elements,
        text,
    ) -> list[dict[str, Any]]:

        dialogs = []

        for item in elements:

            role = str(
                item.get(
                    "role",
                    ""
                )
            ).lower()

            kind = str(
                item.get(
                    "element_type",
                    ""
                )
            ).lower()

            label = str(
                item.get(
                    "text",
                    ""
                )
            )

            if (
                "dialog" in role
                or
                "dialog" in kind
            ):

                dialogs.append(
                    item
                )

        if (
            not dialogs
            and
            UIIntelligence._contains(
                text,
                (
                    "are you sure",
                    "save changes",
                    "do you want to",
                    "allow this app",
                ),
            )
        ):

            dialogs.append(
                {
                    "element_type":
                        "dialog",

                    "text":
                        "Possible confirmation dialog",

                    "confidence":
                        0.60,
                }
            )

        return dialogs[:10]

    @staticmethod
    def _contains(
        text: str,
        terms,
    ) -> bool:

        lower = str(
            text or ""
        ).lower()

        return any(
            term in lower
            for term in terms
        )

    @staticmethod
    def _split_text(
        text: str
    ) -> list[str]:

        return [
            line.strip()
            for line in str(
                text or ""
            ).splitlines()
            if line.strip()
        ]

    @staticmethod
    def _dedupe_text(
        items
    ) -> list[str]:

        seen = set()
        result = []

        for item in items:

            normalized = re.sub(
                r"\s+",
                " ",
                str(
                    item or ""
                ).strip()
            )

            if not normalized:
                continue

            key = normalized.lower()

            if key in seen:
                continue

            seen.add(
                key
            )

            result.append(
                normalized
            )

        return result

    @staticmethod
    def _bounds(
        value
    ) -> Optional[dict[str, int]]:

        if isinstance(
            value,
            dict
        ):

            try:

                return {
                    "x":
                        int(
                            value.get(
                                "x",
                                0
                            )
                        ),

                    "y":
                        int(
                            value.get(
                                "y",
                                0
                            )
                        ),

                    "width":
                        int(
                            value.get(
                                "width",
                                0
                            )
                        ),

                    "height":
                        int(
                            value.get(
                                "height",
                                0
                            )
                        ),
                }

            except Exception:
                return None

        if isinstance(
            value,
            (list, tuple)
        ) and len(value) == 4:

            try:

                return {
                    "x":
                        int(value[0]),

                    "y":
                        int(value[1]),

                    "width":
                        int(value[2]),

                    "height":
                        int(value[3]),
                }

            except Exception:
                return None

        return None

    @staticmethod
    def _float(
        value
    ) -> float:

        try:
            return float(
                value or 0.0
            )
        except Exception:
            return 0.0

    @staticmethod
    def _confidence(
        visible_text,
        elements,
    ) -> float:

        if not visible_text and not elements:
            return 0.0

        evidence = 0.0

        if visible_text:
            evidence += 0.5

        if elements:
            evidence += 0.5

        return min(
            1.0,
            evidence
        )


def analyze_ui(
    vision_result=None,
    ocr_text="",
    foreground=None,
) -> dict[str, Any]:

    return UIIntelligence().build_state(
        vision_result,
        ocr_text,
        foreground,
    )