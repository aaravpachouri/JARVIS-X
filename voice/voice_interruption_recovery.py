from __future__ import annotations

import time
from typing import Any, Optional


class VoiceInterruptionRecovery:

    """
    Coordinates interruption, cancellation acknowledgement, and
    safe voice resumption after a computer task stops.

    This module is intentionally independent of the actual
    VoiceController and ComputerAgent implementations.

    It provides a deterministic handshake:

        interrupt requested
              ↓
        cancel computer task
              ↓
        cancel TTS
              ↓
        acknowledge stale generation
              ↓
        return to listening/idle
    """

    def __init__(
        self,
        synchronizer,
        tts_sync=None,
        *,
        computer_interrupt_callback=None,
    ):

        self.sync = synchronizer

        self.tts_sync = (
            tts_sync
        )

        self.computer_interrupt_callback = (
            computer_interrupt_callback
        )

        self.requested = False

        self.acknowledged = False

        self.reason = ""

        self.requested_at: Optional[
            float
        ] = None

        self.acknowledged_at: Optional[
            float
        ] = None

    ############################################################
    # REQUEST
    ############################################################

    def request(
        self,
        reason: str = "Interrupted by user.",
    ) -> dict[str, Any]:

        self.requested = True

        self.acknowledged = False

        self.reason = str(
            reason
            or
            "Interrupted by user."
        )

        self.requested_at = (
            time.monotonic()
        )

        ########################################################
        # Mark the current synchronized generation stale first.
        ########################################################

        state = (
            self.sync.request_interrupt(
                self.reason
            )
        )

        ########################################################
        # Cancel speech immediately.
        ########################################################

        if self.tts_sync is not None:

            try:

                self.tts_sync.cancel(
                    self.reason
                )

            except Exception:
                pass

        ########################################################
        # Then notify the actual computer runtime.
        ########################################################

        if callable(
            self.computer_interrupt_callback
        ):

            try:

                self.computer_interrupt_callback(
                    self.reason
                )

            except TypeError:

                self.computer_interrupt_callback()

        return {
            "requested":
                True,

            "state":
                state,

            "reason":
                self.reason,
        }

    ############################################################
    # ACKNOWLEDGE
    ############################################################

    def acknowledge(
        self,
    ) -> dict[str, Any]:

        self.sync.acknowledge_interrupt()

        self.requested = False

        self.acknowledged = True

        self.acknowledged_at = (
            time.monotonic()
        )

        return self.snapshot()

    ############################################################
    # SAFE RESUME
    ############################################################

    def can_resume_voice(
        self,
    ) -> bool:

        state = (
            self.sync.snapshot()
        )

        return bool(
            not self.requested
            and
            not state.get(
                "interrupt_requested",
                False,
            )
            and
            state.get(
                "active_task_id",
                0,
            )
            ==
            0
        )

    def resume(
        self,
    ) -> dict[str, Any]:

        if not self.can_resume_voice():

            return {
                "resumed":
                    False,

                "reason":
                    (
                        "Voice cannot safely resume while "
                        "the previous task generation is active."
                    ),
            }

        self.sync.clear_interrupt()

        self.sync.set_listening()

        return {
            "resumed":
                True,

            "state":
                self.sync.snapshot(),
        }

    ############################################################
    # STALE RESULT GATE
    ############################################################

    def accept_task_result(
        self,
        task_id: int,
    ) -> bool:

        ########################################################
        # An interrupted/stale generation must never be accepted.
        ########################################################

        if self.sync.is_interrupt_requested():

            return False

        return self.sync.is_current_task(
            task_id
        )

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "requested":
                self.requested,

            "acknowledged":
                self.acknowledged,

            "reason":
                self.reason,

            "requested_at":
                self.requested_at,

            "acknowledged_at":
                self.acknowledged_at,

            "synchronizer":
                self.sync.snapshot(),
        }