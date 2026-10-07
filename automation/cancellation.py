from __future__ import annotations

import threading
from typing import Optional


############################################################
# CANCELLATION TOKEN
############################################################

class CancellationToken:

    """
    Thread-safe cooperative cancellation signal.

    It does not force-kill threads.

    Long-running components should periodically call:
        is_cancelled()
        raise_if_cancelled()
    """

    def __init__(self):

        self._event = threading.Event()

        self._reason = ""

    ########################################################
    # REQUEST
    ########################################################

    def cancel(
        self,
        reason: str = "Task interrupted by user.",
    ) -> None:

        self._reason = str(
            reason or
            "Task interrupted by user."
        ).strip()

        self._event.set()

    ########################################################
    # STATE
    ########################################################

    def is_cancelled(
        self,
    ) -> bool:

        return self._event.is_set()

    ########################################################
    # REASON
    ########################################################

    @property
    def reason(
        self,
    ) -> str:

        return self._reason

    ########################################################
    # CHECK
    ########################################################

    def raise_if_cancelled(
        self,
    ) -> None:

        if self.is_cancelled():

            raise InterruptedError(
                self.reason
                or
                "Task interrupted by user."
            )

    ########################################################
    # RESET
    ########################################################

    def reset(
        self,
    ) -> None:

        self._reason = ""

        self._event.clear()

    ########################################################
    # EVENT
    ########################################################

    @property
    def event(
        self,
    ) -> threading.Event:

        return self._event

    ########################################################
    # REPRESENTATION
    ########################################################

    def __repr__(
        self,
    ):

        return (
            "<CancellationToken "
            f"cancelled={self.is_cancelled()}>"
        )


############################################################
# CANCELLATION CONTEXT
############################################################

class CancellationContext:

    """
    Shared cancellation context passed through task execution.

    This avoids passing several independent cancellation flags
    through the system.
    """

    def __init__(
        self,
        token: Optional[
            CancellationToken
        ] = None,
    ):

        self.token = (
            token
            if token is not None
            else CancellationToken()
        )

    def cancel(
        self,
        reason: str = "Task interrupted by user.",
    ) -> None:

        self.token.cancel(
            reason
        )

    def reset(
        self,
    ) -> None:

        self.token.reset()

    def is_cancelled(
        self,
    ) -> bool:

        return self.token.is_cancelled()

    def check(
        self,
    ) -> None:

        self.token.raise_if_cancelled()