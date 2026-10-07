from __future__ import annotations

import threading


class TaskInterruptController:

    """
    Central cooperative interruption state for JARVIS.

    It does not force-kill threads. It exposes a thread-safe
    cancellation signal that the orchestrator and executors
    can observe.
    """

    def __init__(self):

        self._event = threading.Event()

        self.reason = ""

    def request(
        self,
        reason: str = "Task interrupted by user.",
    ) -> None:

        self.reason = str(
            reason or
            "Task interrupted by user."
        ).strip()

        self._event.set()

    def is_requested(
        self,
    ) -> bool:

        return self._event.is_set()

    def clear(
        self,
    ) -> None:

        self.reason = ""

        self._event.clear()

    def check(
        self,
    ) -> None:

        if self.is_requested():

            raise InterruptedError(
                self.reason
                or
                "Task interrupted by user."
            )

    def __repr__(
        self,
    ):

        return (
            "<TaskInterruptController "
            f"requested={self.is_requested()}>"
        )