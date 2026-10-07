from __future__ import annotations

from typing import Any, Optional

from automation.ui_intelligence import UIIntelligence
from automation.ui_element_targeting import UIElementTargeting
from automation.ui_observation_bridge import UIObservationBridge
from automation.ui_state_cache import UIStateCache
from automation.ui_state_trust import UIStateTrust, UIStateTrustGate


class UIContextProvider:
    """
    Unified UI context facade for JARVIS X.

    This module keeps the growing UI subsystem behind one interface.

    Components:
        UIIntelligence
            semantic interpretation

        UIObservationBridge
            observation capture + analysis

        UIStateCache
            short-lived state reuse

        UIStateTrust
            freshness / confidence / stale-state protection

        UIElementTargeting
            semantic interaction target resolution

    This class does not perform mouse or keyboard actions.
    """

    def __init__(
        self,
        observer,
        ui_intelligence: Optional[UIIntelligence] = None,
        cache: Optional[UIStateCache] = None,
        trust: Optional[UIStateTrust] = None,
        targeting: Optional[UIElementTargeting] = None,
    ):

        self.ui = (
            ui_intelligence
            or
            UIIntelligence()
        )

        self.cache = (
            cache
            or
            UIStateCache()
        )

        self.trust = (
            trust
            or
            UIStateTrust()
        )

        self.targeting = (
            targeting
            or
            UIElementTargeting(
                self.ui
            )
        )

        self.bridge = (
            UIObservationBridge(
                observer,
                self.ui,
            )
        )

        # Keep the bridge's cache aligned with the provider cache.
        self.bridge.cache = self.cache

        self.trust_gate = (
            UIStateTrustGate(
                self.cache,
                self.trust,
            )
        )

        self.last_context: dict[str, Any] = {}

    ############################################################
    # OBSERVE
    ############################################################

    def observe(
        self,
        vision_result: Any = None,
        ocr_text: str = "",
        foreground: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:

        result = self.bridge.observe(
            vision_result=vision_result,
            ocr_text=ocr_text,
            foreground=foreground,
        )

        state = result.get(
            "state",
            {},
        )

        trust_result = (
            self.trust.evaluate(
                state,
                age=self.cache.age(),
            )
        )

        context = {
            "state":
                state,

            "compact":
                self.ui.compact_context(
                    state
                ),

            "cache":
                self.cache.compact(),

            "trust":
                trust_result,

            "state_change":
                result.get(
                    "state_change",
                    self.bridge.compare_state_change(
                        state
                    )
                    if hasattr(
                        self.bridge,
                        "compare_state_change",
                    )
                    else {},
                ),

            "screenshot":
                result.get(
                    "screenshot"
                ),
        }

        self.last_context = context

        return context

    ############################################################
    # CURRENT CONTEXT
    ############################################################

    def current(
        self,
        max_age: Optional[float] = None,
    ) -> dict[str, Any]:

        state = self.cache.get(
            max_age=max_age
        )

        if state is None:

            return {
                "available":
                    False,

                "state":
                    None,

                "compact":
                    {},

                "trust":
                    self.trust_gate.evaluate_cached(
                        max_age=max_age
                    ),

                "cache":
                    self.cache.compact(),
            }

        return {
            "available":
                True,

            "state":
                state,

            "compact":
                self.ui.compact_context(
                    state
                ),

            "trust":
                self.trust.evaluate(
                    state,
                    age=self.cache.age(),
                ),

            "cache":
                self.cache.compact(),
        }

    ############################################################
    # TARGET RESOLUTION
    ############################################################

    def resolve_target(
        self,
        target: str,
        action: str = "click",
        state: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:

        if state is None:

            state = self.cache.get()

        result = self.targeting.resolve(
            target,
            action=action,
            state=state,
        )

        trusted = self.trust.evaluate(
            state,
            age=self.cache.age(),
        )

        result[
            "ui_trusted"
        ] = trusted.get(
            "trusted",
            False,
        )

        ########################################################
        # Never declare a target safe when the underlying UI state
        # is stale or untrusted.
        ########################################################

        if not trusted.get(
            "trusted",
            False,
        ):

            result[
                "safe"
            ] = False

            result[
                "reason"
            ] = (
                "UI target resolution blocked because "
                "the current UI state is not trusted: "
                +
                str(
                    trusted.get(
                        "reason",
                        "",
                    )
                )
            )

            return result

        result[
            "safe"
        ] = (
            self.targeting.is_safe_target(
                result
            )
        )

        return result

    ############################################################
    # STATE ACCESS
    ############################################################

    def get_state(
        self,
        max_age: Optional[float] = None,
    ):

        return self.cache.get(
            max_age=max_age
        )

    def is_trusted(
        self,
    ) -> bool:

        return bool(
            self.trust_gate.evaluate_cached().get(
                "trusted",
                False,
            )
        )

    def should_refresh(
        self,
    ) -> bool:

        return bool(
            self.trust_gate.should_refresh()
        )

    ############################################################
    # CACHE CONTROL
    ############################################################

    def invalidate(
        self,
    ):

        self.cache.invalidate()

    def clear(
        self,
    ):

        self.cache.clear()

    ############################################################
    # COMPACT MODEL CONTEXT
    ############################################################

    def compact_context(
        self,
    ) -> dict[str, Any]:

        current = self.current()

        return {
            "available":
                current.get(
                    "available",
                    False,
                ),

            "ui":
                current.get(
                    "compact",
                    {},
                ),

            "trust":
                current.get(
                    "trust",
                    {},
                ),

            "cache":
                {
                    "age":
                        current.get(
                            "cache",
                            {}
                        ).get(
                            "age"
                        ),

                    "signature":
                        current.get(
                            "cache",
                            {}
                        ).get(
                            "signature",
                            "",
                        ),
                },
        }

    ############################################################
    # CLEANUP
    ############################################################

    def cleanup(
        self,
        screenshot=None,
    ):

        self.bridge.cleanup(
            screenshot
        )