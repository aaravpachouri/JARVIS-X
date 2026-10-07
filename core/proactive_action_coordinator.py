from __future__ import annotations

from typing import Any, Optional

from core.proactive_opportunity_engine import ProactiveOpportunityEngine
from core.proactive_trigger_context import ProactiveTriggerContext
from core.proactive_opportunity_ranker import ProactiveOpportunityRanker
from core.proactive_approval_gate import ProactiveApprovalGate


class ProactiveActionCoordinator:
    """
    Unified Phase 8.10 proactive runtime facade.

    It:
        1. gathers proactive triggers
        2. creates/ranks opportunities
        3. applies the approval gate
        4. returns an actionable suggestion contract

    It does not execute the final computer action itself.
    """

    def __init__(
        self,
        *,
        opportunity_engine: Optional[
            ProactiveOpportunityEngine
        ] = None,
        trigger_context: Optional[
            ProactiveTriggerContext
        ] = None,
        ranker: Optional[
            ProactiveOpportunityRanker
        ] = None,
        approval_gate: Optional[
            ProactiveApprovalGate
        ] = None,
    ):
        self.engine = (
            opportunity_engine
            or
            ProactiveOpportunityEngine()
        )

        self.triggers = (
            trigger_context
            or
            ProactiveTriggerContext()
        )

        self.ranker = (
            ranker
            or
            ProactiveOpportunityRanker()
        )

        self.gate = (
            approval_gate
            or
            ProactiveApprovalGate()
        )

    def refresh(
        self,
        *,
        goal_context=None,
        memory_context=None,
        runtime_context=None,
    ) -> dict[str, Any]:

        self.triggers.update_from_context(
            goal_context=goal_context,
            workflow_context=runtime_context,
            runtime_context=runtime_context,
        )

        opportunities = self.engine.detect(
            goal_context=goal_context,
            memory_context=memory_context,
            runtime_context=runtime_context,
        )

        active_goal = {}
        if isinstance(
            goal_context,
            dict,
        ):
            active_goal = (
                goal_context.get(
                    "active_goal",
                    {}
                )
                or
                {}
            )

        goal_id = str(
            active_goal.get(
                "goal_id",
                ""
            )
            or
            ""
        )

        ranked = self.ranker.rank(
            opportunities,
            active_goal_id=goal_id,
            limit=10,
        )

        return {
            "triggers": [
                item.to_dict()
                for item
                in self.triggers.active(20)
            ],
            "opportunities": ranked,
        }

    def evaluate(
        self,
        opportunity,
        *,
        action_type: str = "",
        user_approved: bool = False,
        explicit_automation: bool = False,
    ) -> dict[str, Any]:

        return self.gate.evaluate(
            opportunity,
            action_type=action_type,
            user_approved=user_approved,
            explicit_automation=explicit_automation,
        )

    def accept(
        self,
        opportunity_id: str,
        *,
        action_type: str = "",
        user_approved: bool = False,
        explicit_automation: bool = False,
    ) -> dict[str, Any]:

        if not self.engine.accept(
            opportunity_id
        ):
            return {
                "accepted": False,
                "reason": "Opportunity not found.",
            }

        pending = {
            item.opportunity_id:
                item
            for item
            in self.engine.pending(50)
        }

        opportunity = pending.get(
            opportunity_id
        )

        if opportunity is None:
            return {
                "accepted": False,
                "reason": "Opportunity is no longer pending.",
            }

        policy = self.gate.evaluate(
            opportunity,
            action_type=action_type,
            user_approved=user_approved,
            explicit_automation=explicit_automation,
        )

        return {
            "accepted": True,
            "approved": policy.get(
                "allowed",
                False,
            ),
            "policy": policy,
            "opportunity": opportunity.to_dict(),
        }

    def dismiss(
        self,
        opportunity_id: str,
    ) -> bool:
        return self.engine.dismiss(
            opportunity_id
        )