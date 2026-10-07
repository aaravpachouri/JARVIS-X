from __future__ import annotations

import re
from typing import Any, Optional


class GoalDetection:

    """
    Detects an explicit or implicit user goal from a command.

    This layer does not execute tasks and does not create a goal itself.
    It produces a structured candidate that GoalContext can accept.

    It distinguishes:
        - explicit goal statements
        - task-oriented commands
        - informational/chat requests
        - continuation of an existing goal
    """

    GOAL_VERBS = {
        "make",
        "create",
        "build",
        "finish",
        "complete",
        "solve",
        "find",
        "fix",
        "install",
        "set",
        "configure",
        "prepare",
        "write",
        "design",
        "organize",
        "move",
        "copy",
        "open",
        "download",
        "research",
        "study",
        "learn",
        "plan",
        "prepare",
        "submit",
        "deploy",
    }

    CONTINUATION_PHRASES = (
        "make it simpler",
        "simplify it",
        "make it shorter",
        "make it longer",
        "explain that",
        "explain this",
        "give me an example",
        "show me another",
        "do the same",
        "continue",
        "next",
        "then",
        "now",
        "also",
        "instead",
        "change it",
        "modify it",
        "fix that",
        "fix this",
    )

    EXPLICIT_GOAL_PATTERNS = (
        r"\bmy goal is to\s+(.+)$",
        r"\bi want to\s+(.+)$",
        r"\bi need to\s+(.+)$",
        r"\bhelp me\s+(.+)$",
        r"\bi'm trying to\s+(.+)$",
        r"\bi am trying to\s+(.+)$",
        r"\bi need help\s+to\s+(.+)$",
    )

    def detect(
        self,
        command: str,
        *,
        existing_goal: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:

        text = str(
            command
            or
            ""
        ).strip()

        lower = text.lower()

        if not text:

            return {
                "goal_detected":
                    False,

                "goal_type":
                    "none",

                "confidence":
                    0.0,

                "title":
                    "",

                "description":
                    "",

                "continuation":
                    False,

                "reason":
                    "Empty command.",
            }

        ########################################################
        # Existing-goal continuation
        ########################################################

        continuation = (
            existing_goal is not None
            and
            self._is_continuation(
                lower
            )
        )

        if continuation:

            title = str(
                existing_goal.get(
                    "title",
                    "",
                )
                or
                ""
            ).strip()

            return {
                "goal_detected":
                    bool(title),

                "goal_type":
                    "continuation",

                "confidence":
                    0.95,

                "title":
                    title,

                "description":
                    text,

                "continuation":
                    True,

                "reason":
                    "Command appears to continue the active goal.",
            }

        ########################################################
        # Explicit goal statements
        ########################################################

        for pattern in self.EXPLICIT_GOAL_PATTERNS:

            match = re.search(
                pattern,
                lower,
                flags=re.IGNORECASE,
            )

            if match:

                description = (
                    match.group(1)
                    .strip()
                )

                return {
                    "goal_detected":
                        True,

                    "goal_type":
                        "explicit",

                    "confidence":
                        0.96,

                    "title":
                        self._title_from_text(
                            description
                        ),

                    "description":
                        description,

                    "continuation":
                        False,

                    "reason":
                        "Explicit user goal statement detected.",
                }

        ########################################################
        # Imperative/task detection
        ########################################################

        first_token = (
            lower.split(
                maxsplit=1
            )[0]
            if lower
            else
            ""
        )

        if first_token in self.GOAL_VERBS:

            return {
                "goal_detected":
                    True,

                "goal_type":
                    "task",

                "confidence":
                    0.82,

                "title":
                    self._title_from_text(
                        text
                    ),

                "description":
                    text,

                "continuation":
                    False,

                "reason":
                    "Imperative/task-oriented command detected.",
            }

        ########################################################
        # Task language anywhere in the command.
        ########################################################

        task_verb_found = any(
            re.search(
                rf"\b{re.escape(verb)}\b",
                lower,
            )
            for verb in self.GOAL_VERBS
        )

        if task_verb_found:

            return {
                "goal_detected":
                    True,

                "goal_type":
                    "task",

                "confidence":
                    0.68,

                "title":
                    self._title_from_text(
                        text
                    ),

                "description":
                    text,

                "continuation":
                    False,

                "reason":
                    "Task-oriented language detected.",
            }

        ########################################################
        # Informational/chat request
        ########################################################

        return {
            "goal_detected":
                False,

            "goal_type":
                "informational",

            "confidence":
                0.40,

            "title":
                "",

            "description":
                text,

            "continuation":
                False,

            "reason":
                "No actionable goal was confidently detected.",
        }

    @staticmethod
    def _is_continuation(
        text: str,
    ) -> bool:

        if any(
            text.startswith(
                phrase
            )
            for phrase in GoalDetection.CONTINUATION_PHRASES
        ):

            return True

        continuation_prefixes = (
            "make ",
            "change ",
            "modify ",
            "add ",
            "remove ",
            "replace ",
            "shorten ",
            "simplify ",
            "continue ",
            "now ",
            "then ",
        )

        return any(
            text.startswith(
                prefix
            )
            for prefix in continuation_prefixes
        )

    @staticmethod
    def _title_from_text(
        text: str,
    ) -> str:

        clean = re.sub(
            r"^\s*(please|can you|could you)\s+",
            "",
            str(
                text
                or
                ""
            ).strip(),
            flags=re.IGNORECASE,
        )

        if not clean:

            return "Untitled goal"

        words = clean.split()

        if len(
            words
        ) > 10:

            clean = " ".join(
                words[:10]
            ) + "..."

        return clean[:120]