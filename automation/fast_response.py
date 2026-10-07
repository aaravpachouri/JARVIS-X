from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


############################################################
# FAST RESPONSE
############################################################

@dataclass
class FastResponse:

    handled: bool = False

    answer: str = ""

    category: str = ""

    confidence: float = 0.0


############################################################
# FAST LOCAL RESPONDER
############################################################

class FastResponseEngine:

    """
    Handles extremely simple conversational requests without
    invoking the general local language model.

    This is intentionally small and deterministic.

    Complex requests continue to the normal local brain.
    """

    def __init__(self):

        self.responses = {
            "how are you": (
                "I'm operating normally and ready to help."
            ),

            "how are u": (
                "I'm operating normally and ready to help."
            ),

            "hello": (
                "Hello. What can I do for you?"
            ),

            "hi": (
                "Hello. What can I do for you?"
            ),

            "hey": (
                "Hello. What can I do for you?"
            ),

            "thanks": (
                "You're welcome."
            ),

            "thank you": (
                "You're welcome."
            ),

            "what are you doing": (
                "I'm ready and waiting for your next command."
            ),
        }

    ########################################################
    # HANDLE
    ########################################################

    def handle(
        self,
        request: str,
    ) -> FastResponse:

        request = self._normalize(
            request
        )

        if not request:

            return FastResponse()

        ####################################################
        # Exact conversational matches
        ####################################################

        answer = self.responses.get(
            request
        )

        if answer:

            return FastResponse(
                handled=True,
                answer=answer,
                category="conversation",
                confidence=0.99,
            )

        ####################################################
        # Very short conversational variants
        ####################################################

        if self._matches(
            request,
            (
                r"how\s+(?:are|r)\s+you",
                r"how\s+(?:are|r)\s+u",
            ),
        ):

            return FastResponse(
                handled=True,
                answer=(
                    "I'm operating normally "
                    "and ready to help."
                ),
                category="conversation",
                confidence=0.98,
            )

        return FastResponse()

    ########################################################
    # NORMALIZE
    ########################################################

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        text = str(
            text or ""
        ).strip().lower()

        text = re.sub(
            r"[^\w\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    ########################################################
    # REGEX MATCH
    ########################################################

    @staticmethod
    def _matches(
        text: str,
        patterns: tuple[str, ...],
    ) -> bool:

        return any(
            re.fullmatch(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern
            in patterns
        )