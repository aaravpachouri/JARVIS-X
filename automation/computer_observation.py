from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


############################################################
# VISUAL ELEMENT
############################################################

@dataclass
class VisualElement:

    element_type: str = ""

    label: str = ""

    x: Optional[float] = None

    y: Optional[float] = None

    left: Optional[float] = None

    top: Optional[float] = None

    right: Optional[float] = None

    bottom: Optional[float] = None

    confidence: float = 0.0

    properties: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# COMPUTER OBSERVATION
############################################################

@dataclass
class ComputerObservation:

    elements: list[VisualElement] = field(
        default_factory=list
    )

    ocr: list[dict[str, Any]] = field(
        default_factory=list
    )

    active_window: str = ""

    screen_width: int = 0

    screen_height: int = 0

    state_summary: str = ""

    uncertainty: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    ########################################################
    # ELEMENTS
    ########################################################

    def add_element(
        self,
        element: VisualElement,
    ) -> None:

        if not isinstance(
            element,
            VisualElement,
        ):

            raise TypeError(
                "Expected VisualElement."
            )

        self.elements.append(
            element
        )

    ########################################################
    # OCR
    ########################################################

    def add_ocr(
        self,
        item: dict[str, Any],
    ) -> None:

        if isinstance(
            item,
            dict,
        ):

            self.ocr.append(
                dict(item)
            )

    ########################################################
    # UNCERTAINTY
    ########################################################

    def add_uncertainty(
        self,
        message: str,
    ) -> None:

        message = str(
            message or ""
        ).strip()

        if (
            message
            and
            message not in self.uncertainty
        ):

            self.uncertainty.append(
                message
            )

    ########################################################
    # SERIALIZATION
    ########################################################

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "active_window":
                self.active_window,

            "screen": {
                "width":
                    self.screen_width,
                "height":
                    self.screen_height,
            },

            "state_summary":
                self.state_summary,

            "elements": [
                {
                    "type":
                        element.element_type,

                    "label":
                        element.label,

                    "x":
                        element.x,

                    "y":
                        element.y,

                    "left":
                        element.left,

                    "top":
                        element.top,

                    "right":
                        element.right,

                    "bottom":
                        element.bottom,

                    "confidence":
                        element.confidence,

                    "properties":
                        dict(
                            element.properties
                        ),
                }

                for element in self.elements
            ],

            "ocr":
                list(self.ocr),

            "uncertainty":
                list(self.uncertainty),

            "metadata":
                dict(self.metadata),
        }


############################################################
# OBSERVATION BUILDER
############################################################

class ComputerObservationBuilder:

    """
    Converts the existing screenshot/OCR output into a structured
    observation object.

    It does not perform computer actions.
    """

    def build(
        self,
        ocr: Optional[
            list[dict[str, Any]]
        ] = None,
        active_window: str = "",
        screen_size: Optional[
            tuple[int, int]
        ] = None,
    ) -> ComputerObservation:

        width = 0

        height = 0

        if screen_size:

            try:

                width = int(
                    screen_size[0]
                )

                height = int(
                    screen_size[1]
                )

            except (
                TypeError,
                ValueError,
            ):

                width = 0

                height = 0

        observation = (
            ComputerObservation(
                active_window=str(
                    active_window or ""
                ).strip(),

                screen_width=width,

                screen_height=height,
            )
        )

        ####################################################
        # Preserve existing OCR data.
        ####################################################

        for item in (
            ocr or []
        ):

            observation.add_ocr(
                item
            )

            if not isinstance(
                item,
                dict,
            ):

                continue

            text = str(
                item.get(
                    "text",
                    "",
                )
            ).strip()

            if not text:

                continue

            element = VisualElement(
                element_type="TEXT",
                label=text,
                x=item.get("x"),
                y=item.get("y"),
                left=item.get("left"),
                top=item.get("top"),
                right=item.get("right"),
                bottom=item.get("bottom"),
                confidence=float(
                    item.get(
                        "confidence",
                        0.0,
                    )
                    or
                    0.0
                ),
            )

            observation.add_element(
                element
            )

        ####################################################
        # Basic uncertainty handling.
        ####################################################

        if not observation.elements:

            observation.add_uncertainty(
                "No reliable OCR/UI text was detected."
            )

        if not observation.active_window:

            observation.add_uncertainty(
                "Active window is unknown."
            )

        observation.state_summary = (
            self._build_summary(
                observation
            )
        )

        return observation

    @staticmethod
    def _build_summary(
        observation: ComputerObservation,
    ) -> str:

        parts = []

        if observation.active_window:

            parts.append(
                "Active window: "
                + observation.active_window
            )

        if observation.elements:

            parts.append(
                f"Detected {len(observation.elements)} "
                "visible text element(s)."
            )

        if observation.uncertainty:

            parts.append(
                "Uncertainty: "
                + " ".join(
                    observation.uncertainty
                )
            )

        return " ".join(
            parts
        ).strip()


############################################################
# REASONING CONTEXT
############################################################

def build_visual_reasoning_context(
    observation: ComputerObservation,
) -> dict[str, Any]:

    return {
        "active_window":
            observation.active_window,

        "screen_width":
            observation.screen_width,

        "screen_height":
            observation.screen_height,

        "state_summary":
            observation.state_summary,

        "visible_elements":
            [
                {
                    "type":
                        element.element_type,

                    "label":
                        element.label,

                    "x":
                        element.x,

                    "y":
                        element.y,

                    "bounds": {
                        "left":
                            element.left,

                        "top":
                            element.top,

                        "right":
                            element.right,

                        "bottom":
                            element.bottom,
                    },

                    "confidence":
                        element.confidence,
                }

                for element
                in observation.elements
            ],

        "uncertainty":
            list(
                observation.uncertainty
            ),
    }