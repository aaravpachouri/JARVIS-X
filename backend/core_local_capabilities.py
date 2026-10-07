from __future__ import annotations

import ast
import datetime as _datetime
import math
import operator
import re
from typing import Optional

try:
    import psutil
except Exception:
    psutil = None

from backend.local_tool_registry import (
    LocalTool,
    LocalToolRegistry,
    LocalToolResult,
)


############################################################
# TEXT HELPERS
############################################################

def _normalize(
    text: str
) -> str:

    text = str(
        text or ""
    ).strip().lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


############################################################
# SAFE MATH ENGINE
############################################################

class SafeMathEvaluator:

    """
    Restricted arithmetic evaluator.

    Supported:

        numbers
        +  -  *  /  //  %  **
        parentheses
        unary + / -
        sqrt()
        abs()
        round()

    No:

        attribute access
        imports
        function calls other than the explicit safe set
        names other than registered safe functions
    """

    FUNCTIONS = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
    }

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    MAX_ABS_NUMBER = 10 ** 100
    MAX_POWER = 1000

    @classmethod
    def evaluate(
        cls,
        expression: str,
    ):

        expression = str(
            expression or ""
        ).strip()

        if not expression:
            raise ValueError(
                "Empty expression."
            )

        tree = ast.parse(
            expression,
            mode="eval",
        )

        value = cls._eval_node(
            tree.body
        )

        if isinstance(
            value,
            complex,
        ):

            raise ValueError(
                "Complex results are not supported."
            )

        if isinstance(
            value,
            (int, float)
        ):

            if not math.isfinite(
                float(value)
            ):

                raise ValueError(
                    "Result is not finite."
                )

            if abs(value) > cls.MAX_ABS_NUMBER:

                raise ValueError(
                    "Result is outside the safe numeric range."
                )

        return value

    @classmethod
    def _eval_node(
        cls,
        node,
    ):

        if isinstance(
            node,
            ast.Constant,
        ):

            if isinstance(
                node.value,
                bool,
            ):

                raise ValueError(
                    "Boolean values are not arithmetic operands."
                )

            if isinstance(
                node.value,
                (int, float)
            ):

                return node.value

            raise ValueError(
                "Unsupported constant."
            )

        if isinstance(
            node,
            ast.UnaryOp,
        ):

            operation = cls.OPERATORS.get(
                type(node.op)
            )

            if operation is None:

                raise ValueError(
                    "Unsupported unary operator."
                )

            return operation(
                cls._eval_node(
                    node.operand
                )
            )

        if isinstance(
            node,
            ast.BinOp,
        ):

            operation = cls.OPERATORS.get(
                type(node.op)
            )

            if operation is None:

                raise ValueError(
                    "Unsupported operator."
                )

            left = cls._eval_node(
                node.left
            )

            right = cls._eval_node(
                node.right
            )

            if isinstance(
                node.op,
                ast.Pow,
            ):

                if abs(
                    right
                ) > cls.MAX_POWER:

                    raise ValueError(
                        "Exponent is too large."
                    )

            return operation(
                left,
                right,
            )

        if isinstance(
            node,
            ast.Call,
        ):

            if not isinstance(
                node.func,
                ast.Name,
            ):

                raise ValueError(
                    "Unsupported function."
                )

            function = cls.FUNCTIONS.get(
                node.func.id
            )

            if function is None:

                raise ValueError(
                    f"Unsupported function: {node.func.id}"
                )

            if len(
                node.args
            ) == 0:

                raise ValueError(
                    "Function requires an argument."
                )

            if len(
                node.args
            ) > 2:

                raise ValueError(
                    "Too many arguments."
                )

            args = [
                cls._eval_node(
                    argument
                )
                for argument in node.args
            ]

            return function(
                *args
            )

        raise ValueError(
            "Unsupported expression."
        )


def _format_number(
    value,
) -> str:

    if isinstance(
        value,
        int,
    ):

        return f"{value:,}"

    if isinstance(
        value,
        float,
    ):

        if value.is_integer():

            return f"{int(value):,}"

        return f"{value:,.10g}"

    return str(
        value
    )


def _math_expression_from_request(
    request: str,
) -> Optional[str]:

    text = _normalize(
        request
    )

    ########################################################
    # Strip common request wrappers.
    ########################################################

    prefixes = (
        r"^please\s+",
        r"^can you\s+",
        r"^could you\s+",
        r"^calculate\s+",
        r"^compute\s+",
        r"^work out\s+",
        r"^what is\s+",
        r"^what's\s+",
        r"^whats\s+",
        r"^find\s+",
        r"^solve\s+",
    )

    for pattern in prefixes:

        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE,
        )

    ########################################################
    # Spoken arithmetic.
    ########################################################

    replacements = (
        (r"\bmultiplied\s+by\b", "*"),
        (r"\bmultiply\s+by\b", "*"),
        (r"\btimes\b", "*"),
        (r"\binto\b", "*"),
        (r"\bdivided\s+by\b", "/"),
        (r"\bdivide\s+by\b", "/"),
        (r"\bplus\b", "+"),
        (r"\bminus\b", "-"),
        (r"\bmodulo\b", "%"),
        (r"\bmod\b", "%"),
    )

    for pattern, replacement in replacements:

        text = re.sub(
            pattern,
            f" {replacement} ",
            text,
            flags=re.IGNORECASE,
        )

    ########################################################
    # Square root wording.
    ########################################################

    root_match = re.fullmatch(
        r"square\s+root\s+of\s+(.+)",
        text,
        flags=re.IGNORECASE,
    )

    if root_match:

        return (
            "sqrt("
            + root_match.group(1).strip()
            + ")"
        )

    ########################################################
    # Percent of wording.
    ########################################################

    percent_match = re.fullmatch(
        r"(.+?)\s*percent\s+of\s*(.+)",
        text,
        flags=re.IGNORECASE,
    )

    if percent_match:

        left = (
            percent_match.group(1)
            .strip()
        )

        right = (
            percent_match.group(2)
            .strip()
        )

        return (
            f"({left} / 100) * ({right})"
        )

    ########################################################
    # Remove common verbal noise.
    ########################################################

    text = re.sub(
        r"\bplease\b",
        " ",
        text,
    )

    text = re.sub(
        r"\bsir\b",
        " ",
        text,
    )

    text = re.sub(
        r"\bwhat's\b",
        " ",
        text,
    )

    text = re.sub(
        r"\bwhat is\b",
        " ",
        text,
    )

    text = re.sub(
        r"\bcalculate\b",
        " ",
        text,
    )

    text = re.sub(
        r"\bcompute\b",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    ########################################################
    # Only accept expressions composed of arithmetic syntax.
    ########################################################

    if not re.fullmatch(
        r"[0-9+\-*/%().,\s]+",
        text,
    ):

        return None

    text = text.replace(
        ",",
        "",
    )

    return text


############################################################
# COMPUTATION CAPABILITY
############################################################

class ComputationTool(LocalTool):

    name = "computation"

    def can_handle(
        self,
        request: str,
    ) -> bool:

        return (
            _math_expression_from_request(
                request
            )
            is not None
        )

    def execute(
        self,
        request: str,
    ) -> LocalToolResult:

        expression = (
            _math_expression_from_request(
                request
            )
        )

        if expression is None:

            return LocalToolResult(
                handled=False,
                tool=self.name,
            )

        try:

            value = (
                SafeMathEvaluator.evaluate(
                    expression
                )
            )

        except Exception as exc:

            return LocalToolResult(
                handled=False,
                tool=self.name,
                metadata={
                    "error": str(exc),
                },
            )

        answer = (
            f"{_format_number(value)}"
        )

        return LocalToolResult(
            handled=True,
            answer=answer,
            tool=self.name,
            confidence=1.0,
            metadata={
                "expression": expression,
                "value": value,
            },
        )


############################################################
# DATE / TIME CAPABILITY
############################################################

class DateTimeTool(LocalTool):

    name = "datetime"

    TIME_PATTERNS = (
        "what time is it",
        "what is the time",
        "whats the time",
        "what's the time",
        "tell me the time",
        "current time",
        "do you know the time",
    )

    DATE_PATTERNS = (
        "what is today's date",
        "what is todays date",
        "what's today's date",
        "whats today's date",
        "what is the date",
        "tell me the date",
        "tell me today's date",
        "today's date",
        "todays date",
        "what day is it",
    )

    def can_handle(
        self,
        request: str,
    ) -> bool:

        text = _normalize(
            request
        )

        return (
            text in self.TIME_PATTERNS
            or
            text in self.DATE_PATTERNS
        )

    def execute(
        self,
        request: str,
    ) -> LocalToolResult:

        text = _normalize(
            request
        )

        now = _datetime.datetime.now()

        if text in self.TIME_PATTERNS:

            answer = (
                "The current time is "
                f"{now.strftime('%I:%M %p')}."
            )

        elif text in self.DATE_PATTERNS:

            answer = (
                "Today is "
                f"{now.strftime('%A, %d %B %Y')}."
            )

        else:

            return LocalToolResult(
                handled=False,
                tool=self.name,
            )

        return LocalToolResult(
            handled=True,
            answer=answer,
            tool=self.name,
            confidence=1.0,
            metadata={
                "datetime": now.isoformat(),
            },
        )


############################################################
# UNIT CONVERSION CAPABILITY
############################################################

class UnitConversionTool(LocalTool):

    name = "unit_conversion"

    LENGTH = {
        "mm": 0.001,
        "millimeter": 0.001,
        "millimeters": 0.001,
        "cm": 0.01,
        "centimeter": 0.01,
        "centimeters": 0.01,
        "m": 1.0,
        "meter": 1.0,
        "meters": 1.0,
        "km": 1000.0,
        "kilometer": 1000.0,
        "kilometers": 1000.0,
        "in": 0.0254,
        "inch": 0.0254,
        "inches": 0.0254,
        "ft": 0.3048,
        "foot": 0.3048,
        "feet": 0.3048,
        "yd": 0.9144,
        "yard": 0.9144,
        "yards": 0.9144,
        "mi": 1609.344,
        "mile": 1609.344,
        "miles": 1609.344,
    }

    MASS = {
        "mg": 0.000001,
        "milligram": 0.000001,
        "milligrams": 0.000001,
        "g": 0.001,
        "gram": 0.001,
        "grams": 0.001,
        "kg": 1.0,
        "kilogram": 1.0,
        "kilograms": 1.0,
        "lb": 0.45359237,
        "lbs": 0.45359237,
        "pound": 0.45359237,
        "pounds": 0.45359237,
    }

    TIME = {
        "second": 1.0,
        "seconds": 1.0,
        "sec": 1.0,
        "s": 1.0,
        "minute": 60.0,
        "minutes": 60.0,
        "min": 60.0,
        "hour": 3600.0,
        "hours": 3600.0,
        "hr": 3600.0,
        "day": 86400.0,
        "days": 86400.0,
    }

    @classmethod
    def _parse(
        cls,
        request: str,
    ):

        text = _normalize(
            request
        )

        text = re.sub(
            r"^(convert|change)\s+",
            "",
            text,
        )

        match = re.fullmatch(
            r"([0-9]+(?:\.[0-9]+)?)\s+"
            r"([a-z]+)\s+"
            r"(?:to|into|in)\s+"
            r"([a-z]+)",
            text,
            flags=re.IGNORECASE,
        )

        if not match:

            return None

        value = float(
            match.group(1)
        )

        source = match.group(2)

        target = match.group(3)

        for category, units in (
            ("length", cls.LENGTH),
            ("mass", cls.MASS),
            ("time", cls.TIME),
        ):

            if (
                source in units
                and
                target in units
            ):

                return (
                    category,
                    value,
                    source,
                    target,
                    units[source],
                    units[target],
                )

        return None

    def can_handle(
        self,
        request: str,
    ) -> bool:

        return (
            self._parse(
                request
            )
            is not None
        )

    def execute(
        self,
        request: str,
    ) -> LocalToolResult:

        parsed = self._parse(
            request
        )

        if parsed is None:

            return LocalToolResult(
                handled=False,
                tool=self.name,
            )

        category, value, source, target, source_factor, target_factor = parsed

        base_value = (
            value
            *
            source_factor
        )

        result = (
            base_value
            /
            target_factor
        )

        answer = (
            f"{_format_number(value)} {source} "
            f"is approximately "
            f"{_format_number(result)} {target}."
        )

        return LocalToolResult(
            handled=True,
            answer=answer,
            tool=self.name,
            confidence=1.0,
            metadata={
                "category": category,
                "source": source,
                "target": target,
                "value": result,
            },
        )


############################################################
# SYSTEM INFORMATION CAPABILITY
############################################################

class SystemInfoTool(LocalTool):

    name = "system_info"

    CPU_PATTERNS = (
        "how much cpu am i using",
        "what is my cpu usage",
        "cpu usage",
        "cpu utilization",
    )

    RAM_PATTERNS = (
        "how much ram am i using",
        "what is my ram usage",
        "ram usage",
        "memory usage",
        "how much memory am i using",
    )

    DISK_PATTERNS = (
        "disk usage",
        "disk space",
        "how much disk space do i have",
        "how much storage do i have",
    )

    def can_handle(
        self,
        request: str,
    ) -> bool:

        text = _normalize(
            request
        )

        return (
            text in self.CPU_PATTERNS
            or
            text in self.RAM_PATTERNS
            or
            text in self.DISK_PATTERNS
        )

    def execute(
        self,
        request: str,
    ) -> LocalToolResult:

        if psutil is None:

            return LocalToolResult(
                handled=False,
                tool=self.name,
                metadata={
                    "error":
                        "psutil is unavailable.",
                },
            )

        text = _normalize(
            request
        )

        if text in self.CPU_PATTERNS:

            value = psutil.cpu_percent(
                interval=0.15
            )

            answer = (
                f"CPU usage is approximately "
                f"{value:.0f}%."
            )

        elif text in self.RAM_PATTERNS:

            memory = psutil.virtual_memory()

            answer = (
                f"RAM usage is approximately "
                f"{memory.percent:.0f}% "
                f"({memory.used / (1024 ** 3):.1f} GB "
                f"of {memory.total / (1024 ** 3):.1f} GB)."
            )

        elif text in self.DISK_PATTERNS:

            disk = psutil.disk_usage(
                "/"
            )

            answer = (
                f"Disk usage is approximately "
                f"{disk.percent:.0f}%, with "
                f"{disk.free / (1024 ** 3):.1f} GB free."
            )

        else:

            return LocalToolResult(
                handled=False,
                tool=self.name,
            )

        return LocalToolResult(
            handled=True,
            answer=answer,
            tool=self.name,
            confidence=1.0,
        )


############################################################
# TOOL REGISTRATION
############################################################

def register_core_local_tools(
    registry: LocalToolRegistry,
) -> LocalToolRegistry:

    """
    Register the Phase 2 core local capabilities.

    This is deliberately one registration function so AIBrain
    does not contain a growing list of command-specific logic.
    """

    registry.register(
        ComputationTool()
    )

    registry.register(
        DateTimeTool()
    )

    registry.register(
        UnitConversionTool()
    )

    registry.register(
        SystemInfoTool()
    )

    return registry