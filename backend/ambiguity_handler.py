from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


############################################################
# AMBIGUITY RESULT
############################################################

@dataclass
class AmbiguityResult:

    ambiguous: bool = False

    clarification_question: str = ""

    missing_information: list[str] = field(
        default_factory=list
    )

    confidence: float = 1.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# AMBIGUITY HANDLER
############################################################

class AmbiguityHandler:

    """
    Detects whether a request lacks information required for
    safe and meaningful execution.

    This component does NOT execute anything and does not invent
    missing information.
    """

    def analyze(
        self,
        request: str,
        context: Optional[
            dict[str, Any]
        ] = None,
    ) -> AmbiguityResult:

        request = str(
            request or ""
        ).strip()

        context = dict(
            context or {}
        )

        if not request:

            return AmbiguityResult(
                ambiguous=True,
                clarification_question=(
                    "What would you like me to do?"
                ),
                missing_information=[
                    "user_request"
                ],
                confidence=1.0,
            )

        ####################################################
        # Explicit context can tell us what information is
        # already available.
        ####################################################

        available = set(
            context.get(
                "available_information",
                [],
            )
            or []
        )

        missing = []

        lower = request.lower()

        ####################################################
        # Common unresolved references.
        ####################################################

        vague_references = (
            "it",
            "that",
            "this",
            "them",
            "him",
            "her",
            "there",
            "the file",
            "the folder",
            "the document",
            "the app",
        )

        if any(
            reference in lower
            for reference in vague_references
        ):

            if "reference_context" not in available:

                missing.append(
                    "reference_target"
                )

        ####################################################
        # Common underspecified computer actions.
        ####################################################

        if (
            "open" in lower
            and
            not any(
                token in lower
                for token in (
                    "chrome",
                    "browser",
                    "calculator",
                    "notepad",
                    "word",
                    "explorer",
                    "file",
                    "folder",
                    ".exe",
                    ".pdf",
                )
            )
        ):

            missing.append(
                "target_to_open"
            )

        if (
            (
                "send" in lower
                or
                "share" in lower
            )
            and
            not any(
                token in lower
                for token in (
                    "to ",
                    "email",
                    "whatsapp",
                    "telegram",
                )
            )
        ):

            missing.append(
                "recipient"
            )

        if (
            "move" in lower
            and
            "to" not in lower
        ):

            missing.append(
                "destination"
            )

        if (
            "rename" in lower
            and
            not any(
                token in lower
                for token in (
                    "as ",
                    "to ",
                )
            )
        ):

            missing.append(
                "new_name"
            )

        ####################################################
        # Deduplicate.
        ####################################################

        missing = list(
            dict.fromkeys(
                missing
            )
        )

        if not missing:

            return AmbiguityResult(
                ambiguous=False,
                confidence=0.95,
                metadata={
                    "request": request,
                },
            )

        question = (
            self._build_question(
                missing
            )
        )

        return AmbiguityResult(
            ambiguous=True,
            clarification_question=question,
            missing_information=missing,
            confidence=0.90,
            metadata={
                "request": request,
            },
        )

    ########################################################
    # CLARIFICATION
    ########################################################

    @staticmethod
    def _build_question(
        missing: list[str],
    ) -> str:

        questions = {
            "reference_target":
                "What are you referring to?",

            "target_to_open":
                "Which app, file, or folder should I open?",

            "recipient":
                "Who should I send or share it with?",

            "destination":
                "Where should I move it?",

            "new_name":
                "What should I rename it to?",

            "user_request":
                "What would you like me to do?",
        }

        if len(
            missing
        ) == 1:

            return questions.get(
                missing[0],
                "Could you clarify that?"
            )

        return (
            "Could you clarify "
            +
            " and ".join(
                questions.get(
                    item,
                    item,
                )
                for item in missing
            )
        )

    ########################################################
    # SAFE DECISION
    ########################################################

    def requires_clarification(
        self,
        result: AmbiguityResult,
    ) -> bool:

        return bool(
            result.ambiguous
        )