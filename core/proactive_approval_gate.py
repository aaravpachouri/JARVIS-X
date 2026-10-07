from __future__ import annotations

import time
from typing import Any, Optional


class ProactiveApprovalGate:
    """
    Decides whether a proactive opportunity may move from
    suggestion into an actionable request.

    The gate is deliberately conservative:
        - suggestions are allowed freely
        - consequential actions require approval
        - explicit user opt-in can authorize execution
        - expiry and confidence are checked
    """

    CONSEQUENT_ACTIONS = {
        "DELETE",
        "MOVE",
        "COPY",
        "RENAME",
        "SEND",
        "SUBMIT",
        "PURCHASE",
        "POST",
        "PUBLISH",
        "INSTALL",
        "EXECUTE",
        "OPEN",
    }

    def __init__(
        self,
        *,
        minimum_confidence: float = 0.70,
    ):
        self.minimum_confidence = max(
            0.0,
            min(
                1.0,
                float(
                    minimum_confidence
                ),
            ),
        )

    def evaluate(
        self,
        opportunity,
        *,
        action_type: str = "",
        user_approved: bool = False,
        explicit_automation: bool = False,
    ) -> dict[str, Any]:

        data = self._normalize(opportunity)

        if not data:
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": "Opportunity is invalid.",
            }

        confidence = self._clamp(
            data.get(
                "confidence",
                0.0,
            )
        )

        status = str(
            data.get(
                "status",
                "PENDING",
            )
            or
            "PENDING"
        ).upper()

        if status not in {
            "PENDING",
            "ACCEPTED",
        }:
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": f"Opportunity status is {status}.",
            }

        expires_at = data.get(
            "expires_at"
        )

        if expires_at is not None:
            try:
                if time.time() >= float(expires_at):
                    return {
                        "allowed": False,
                        "requires_approval": True,
                        "reason": "Opportunity has expired.",
                    }
            except Exception:
                pass

        if confidence < self.minimum_confidence:
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": "Opportunity confidence is below the execution threshold.",
                "confidence": confidence,
            }

        action = str(
            action_type
            or
            data.get(
                "metadata",
                {}
            ).get(
                "action_type",
                "",
            )
            or
            ""
        ).upper().strip()

        consequential = action in self.CONSEQUENT_ACTIONS

        if consequential and not (
            user_approved
            or
            explicit_automation
        ):
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": "Consequential proactive action requires user approval.",
                "confidence": confidence,
                "action_type": action,
            }

        return {
            "allowed": True,
            "requires_approval": False,
            "reason": (
                "Proactive action is approved by current policy."
            ),
            "confidence": confidence,
            "action_type": action,
        }

    @staticmethod
    def _normalize(item):
        if isinstance(item, dict):
            return dict(item)
        if hasattr(item, "to_dict"):
            try:
                data = item.to_dict()
                return data if isinstance(data, dict) else {}
            except Exception:
                pass
        return {}

    @staticmethod
    def _clamp(value):
        try:
            return max(
                0.0,
                min(
                    1.0,
                    float(value),
                ),
            )
        except Exception:
            return 0.0