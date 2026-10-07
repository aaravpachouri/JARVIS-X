from __future__ import annotations

import json


class AgentRecoveryPlanner:

    """
    JARVIS X
    UNIVERSAL RECOVERY PLANNER

    This component does not execute actions.

    Its job is to remember which routes have failed and to
    provide the reasoning layer with concrete recovery
    constraints so the agent does not keep selecting the same
    ineffective strategy.

    Recovery types:
        - semantic: executor accepted the input, but the expected
          computer state did not appear.
        - executor: the executor itself rejected or failed the action.
        - capability: the requested tool is unavailable/unsupported
          and should be treated as unavailable for the remainder of
          the task.
    """

    TOOL_ALIASES = {
        "CLICK": "LEFT_CLICK",
        "LEFTCLICK": "LEFT_CLICK",
        "RIGHTCLICK": "RIGHT_CLICK",
        "DOUBLECLICK": "DOUBLE_CLICK",
        "TYPE": "TYPE_TEXT",
        "PRESS": "PRESS_KEY",
        "KEY_PRESS": "PRESS_KEY",
        "OPEN_APPLICATION": "OPEN_APP",
        "LAUNCH_APP": "OPEN_APP",
        "LAUNCH_APPLICATION": "OPEN_APP",
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self.failed_signatures: dict[str, int] = {}
        self.failed_tools: dict[str, int] = {}
        self.blocked_tools: set[str] = set()
        self.semantic_failures: list[dict] = []
        self.executor_failures: list[dict] = []
        self.last_failure: dict | None = None

    @classmethod
    def normalize_tool(cls, tool: str) -> str:
        name = str(tool or "").strip().upper()
        return cls.TOOL_ALIASES.get(name, name)

    @staticmethod
    def signature(tool: str, parameters: dict | None) -> str:
        try:
            payload = json.dumps(
                parameters or {},
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
        except Exception:
            payload = str(parameters)
        return f"{str(tool or '').upper().strip()}|{payload}"

    def record_failure(
        self,
        action: dict,
        reason: str = "",
        failure_type: str = "semantic",
    ) -> None:
        if not isinstance(action, dict):
            return

        tool = self.normalize_tool(action.get("tool", ""))
        parameters = action.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}

        sig = self.signature(tool, parameters)

        self.failed_signatures[sig] = (
            self.failed_signatures.get(sig, 0) + 1
        )
        self.failed_tools[tool] = (
            self.failed_tools.get(tool, 0) + 1
        )

        record = {
            "tool": tool,
            "parameters": dict(parameters),
            "signature": sig,
            "reason": str(reason or ""),
            "type": str(failure_type or "semantic").lower(),
        }

        if record["type"] == "capability":
            self.blocked_tools.add(tool)
            self.executor_failures.append(record)
        elif record["type"] == "executor":
            self.executor_failures.append(record)
        else:
            self.semantic_failures.append(record)

        self.last_failure = record

    def record_success(
        self,
        action: dict,
    ) -> None:
        """Record that an action was executed successfully.

        A successful executor call does not clear historical failures.
        The planner intentionally keeps failure knowledge for the task.
        """
        _ = action

    def is_blocked(
        self,
        action: dict,
    ) -> bool:
        if not isinstance(action, dict):
            return True

        tool = self.normalize_tool(action.get("tool", ""))
        parameters = action.get("parameters", {})
        sig = self.signature(tool, parameters)

        if tool in self.blocked_tools:
            return True

        return sig in self.failed_signatures

    def has_failed_signature(
        self,
        action: dict,
    ) -> bool:
        if not isinstance(action, dict):
            return False
        tool = self.normalize_tool(action.get("tool", ""))
        parameters = action.get("parameters", {})
        return (
            self.signature(tool, parameters)
            in self.failed_signatures
        )

    def model_context(self) -> dict:
        recent_semantic = self.semantic_failures[-4:]
        recent_executor = self.executor_failures[-4:]

        return {
            "blocked_tools": sorted(self.blocked_tools),
            "failed_tools": sorted(self.failed_tools.keys())[-10:],
            "failed_signatures": list(self.failed_signatures.keys())[-8:],
            "recent_semantic_failures": recent_semantic,
            "recent_executor_failures": recent_executor,
            "last_failure": self.last_failure,
            "recovery_rule": (
                "Never repeat a blocked tool or failed exact route. "
                "Choose a genuinely different capability or strategy."
            ),
        }

    def classify_executor_failure(self, error: str) -> str:
        text = str(error or "").lower()

        capability_markers = (
            "unsupported computer action",
            "unsupported action",
            "no action supplied",
            "invalid action",
            "policy rejected action",
        )

        if any(marker in text for marker in capability_markers):
            return "capability"

        return "executor"