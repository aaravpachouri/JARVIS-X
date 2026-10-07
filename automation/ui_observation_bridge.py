from __future__ import annotations

from typing import Any, Optional
from automation.ui_state_cache import UIStateCache


class UIObservationBridge:
    """
    Thin bridge between AgentObserver and UIIntelligence.

    It captures observations and converts supplied vision/OCR/
    foreground data into semantic UI state without adding UI
    logic to ComputerUseAgent.
    """

    def __init__(
        self,
        observer,
        ui_intelligence,
    ):
        self.observer = observer
        self.ui = ui_intelligence

        self.cache = UIStateCache()
        self.last_observation = None

    @staticmethod
    def _state_signature(
        state
    ) -> str:

        if not isinstance(
            state,
            dict,
        ):
            return ""

        return repr(
            (
                state.get(
                    "foreground",
                    {},
                ),
                tuple(
                    state.get(
                        "visible_text",
                        [],
                    )[:20]
                ),
                tuple(
                    (
                        item.get(
                            "text",
                            "",
                        ),
                        item.get(
                            "role",
                            "",
                        ),
                        str(
                            item.get(
                                "bounds",
                                "",
                            )
                        ),
                    )
                    for item in state.get(
                        "elements",
                        []
                    )[:20]
                    if isinstance(
                        item,
                        dict,
                    )
                ),
                bool(
                    state.get(
                        "loading",
                        False,
                    )
                ),
                bool(
                    state.get(
                        "error_visible",
                        False,
                    )
                ),
            )
        )

    def capture(self):
        capture_temp = getattr(
            self.observer,
            "capture_to_temp",
            None,
        )

        if callable(capture_temp):
            screenshot = capture_temp()
        else:
            capture = getattr(
                self.observer,
                "capture",
                None,
            )

            if not callable(capture):
                raise RuntimeError(
                    "AgentObserver has no capture method."
                )

            screenshot = capture()

        self.last_observation = screenshot
        return screenshot

    def analyze(
        self,
        vision_result: Any = None,
        ocr_text: str = "",
        foreground: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:

        state = self.ui.build_state(
            vision_result=vision_result,
            ocr_text=ocr_text,
            foreground=foreground,
        )

        state_change = (
            self.compare_state_change(
                state
            )
        )

        self.cache.store(
            state,
            signature=(
                state_change.get(
                    "current_signature",
                    self._state_signature(
                        state
                    ),
                )
            ),
        )

        return {
            "screenshot": self.last_observation,

            "state": state,

            "compact":
                self.ui.compact_context(
                    state
                ),

            "cached":
                self.cache.compact(),

            "state_change":
                state_change,
        }

    def compare_state_change(
        self,
        state,
    ) -> dict:

        """
        Compare a newly analyzed UI state against the cached state.
        """

        current_signature = (
            self._state_signature(
                state
            )
        )

        previous_signature = (
            self.cache.signature()
        )

        if not previous_signature:

            return {
                "changed":
                    False,

                "previous_signature":
                    "",

                "current_signature":
                    current_signature,

                "reason":
                    "No previous UI state exists.",
            }

        changed = (
            current_signature
            !=
            previous_signature
        )

        return {
            "changed":
                changed,

            "previous_signature":
                previous_signature,

            "current_signature":
                current_signature,

            "reason":
                (
                    "UI state signature changed."
                    if changed
                    else
                    "UI state is unchanged."
                ),
        }

    def has_state_changed(
        self,
        state,
    ) -> bool:

        return bool(
            self.compare_state_change(
                state
            ).get(
                "changed",
                False,
            )
        )

    def get_cached_state(
        self,
        max_age=None,
    ):

        return self.cache.get(
            max_age=max_age
        )

    def cached_context(
        self,
    ):

        return self.cache.compact()

    def invalidate_cache(
        self,
    ):

        self.cache.invalidate()

    def observe(
        self,
        vision_result: Any = None,
        ocr_text: str = "",
        foreground: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:

        screenshot = self.capture()

        result = self.analyze(
            vision_result=vision_result,
            ocr_text=ocr_text,
            foreground=foreground,
        )

        result["screenshot"] = screenshot
        return result

    def cleanup(
        self,
        screenshot=None,
    ):

        target = (
            screenshot
            or
            self.last_observation
        )

        if not target:
            return

        delete_temp = getattr(
            self.observer,
            "delete_temp",
            None,
        )

        if callable(delete_temp):
            try:
                delete_temp(target)
            except Exception:
                pass

        if target == self.last_observation:
            self.last_observation = None