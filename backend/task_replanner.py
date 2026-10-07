from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ReplanResult:
    success: bool = False
    reason: str = ""
    step_specs: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskReplanner:
    """
    Generic dynamic replanning contract.

    The replanner does not execute anything. It receives the current
    task state plus recovery context and returns replacement/new step
    specifications.

    A planner function can later be backed by the local JARVIS brain,
    a dedicated planner model, or another deterministic strategy.
    """

    def __init__(
        self,
        planner: Optional[Callable[[dict[str, Any]], Any]] = None,
    ):
        self.planner = planner

    def set_planner(
        self,
        planner: Callable[[dict[str, Any]], Any],
    ) -> None:
        self.planner = planner

    def clear_planner(self) -> None:
        self.planner = None

    def replan(
        self,
        context: dict[str, Any],
    ) -> ReplanResult:

        if self.planner is None:
            return ReplanResult(
                success=False,
                reason="No replanning strategy is registered.",
            )

        try:
            raw = self.planner(dict(context))
        except Exception as exc:
            return ReplanResult(
                success=False,
                reason=str(exc),
                metadata={"exception": str(exc)},
            )

        if isinstance(raw, ReplanResult):
            return raw

        if isinstance(raw, dict):
            specs = raw.get("steps", [])
            if not isinstance(specs, list):
                specs = []

            return ReplanResult(
                success=bool(raw.get("success", bool(specs))),
                reason=str(raw.get("reason", "")),
                step_specs=[
                    spec for spec in specs
                    if isinstance(spec, dict)
                ],
                metadata=dict(raw.get("metadata", {})),
            )

        if isinstance(raw, list):
            return ReplanResult(
                success=bool(raw),
                reason="Replacement plan generated.",
                step_specs=[
                    spec for spec in raw
                    if isinstance(spec, dict)
                ],
            )

        return ReplanResult(
            success=False,
            reason="Planner returned an unsupported plan format.",
        )