from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional


@dataclass
class LocalToolResult:
    handled: bool = False
    answer: str = ""
    tool: str = ""
    confidence: float = 0.0
    metadata: Optional[dict[str, Any]] = None


class LocalTool:
    name = "local_tool"

    def can_handle(self, request: str) -> bool:
        return False

    def execute(self, request: str) -> LocalToolResult:
        return LocalToolResult(handled=False, tool=self.name)


class FunctionTool(LocalTool):
    def __init__(
        self,
        name: str,
        can_handle: Callable[[str], bool],
        execute: Callable[[str], LocalToolResult],
    ):
        self.name = str(name or "local_tool").strip()
        self._can_handle = can_handle
        self._execute = execute

    def can_handle(self, request: str) -> bool:
        try:
            return bool(self._can_handle(str(request or "")))
        except Exception as exc:
            print(f"[LocalTools] {self.name}.can_handle error:", exc)
            return False

    def execute(self, request: str) -> LocalToolResult:
        try:
            result = self._execute(str(request or ""))
            if isinstance(result, LocalToolResult):
                if not result.tool:
                    result.tool = self.name
                return result
            return LocalToolResult(
                handled=True,
                answer=str(result or "").strip(),
                tool=self.name,
            )
        except Exception as exc:
            print(f"[LocalTools] {self.name}.execute error:", exc)
            return LocalToolResult(
                handled=False,
                tool=self.name,
                metadata={"error": str(exc)},
            )


class LocalToolRegistry:
    """
    Fast deterministic capability registry for JARVIS.

    It does not call Qwen, Gemini, or the Computer Agent.
    It only determines whether a local tool can solve a request.
    """

    def __init__(
        self,
        tools: Optional[Iterable[LocalTool]] = None,
    ):
        self._tools: list[LocalTool] = []
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, tool: LocalTool) -> LocalTool:
        if not isinstance(tool, LocalTool):
            raise TypeError(
                "LocalToolRegistry accepts LocalTool instances only."
            )

        self._tools = [
            existing
            for existing in self._tools
            if existing.name != tool.name
        ]

        self._tools.append(tool)

        print(
            "[LocalTools] Registered:",
            tool.name,
        )

        return tool

    def unregister(self, name: str) -> bool:
        name = str(name or "").strip()
        before = len(self._tools)

        self._tools = [
            tool
            for tool in self._tools
            if tool.name != name
        ]

        return len(self._tools) != before

    def tools(self) -> list[LocalTool]:
        return list(self._tools)

    def find(self, request: str) -> Optional[LocalTool]:
        request = str(request or "").strip()

        if not request:
            return None

        for tool in self._tools:
            if tool.can_handle(request):
                return tool

        return None

    def execute(self, request: str) -> LocalToolResult:
        request = str(request or "").strip()

        if not request:
            return LocalToolResult()

        tool = self.find(request)

        if tool is None:
            return LocalToolResult(handled=False)

        result = tool.execute(request)

        if not isinstance(result, LocalToolResult):
            result = LocalToolResult(
                handled=True,
                answer=str(result or "").strip(),
                tool=tool.name,
            )

        if not result.tool:
            result.tool = tool.name

        return result

    def has(self, name: str) -> bool:
        name = str(name or "").strip()
        return any(tool.name == name for tool in self._tools)

    def clear(self) -> None:
        self._tools.clear()

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        names = [tool.name for tool in self._tools]
        return f"<LocalToolRegistry tools={names!r}>"