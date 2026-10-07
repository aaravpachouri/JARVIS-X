from __future__ import annotations

from typing import Any, Optional


class VoiceComputerRuntimeBridge:

    """
    Unified runtime facade connecting:
        VoiceInterruptionBridge
        VoiceComputerSynchronizer
        TTSTaskSynchronizer
        existing AIController / computer runtime

    It does not own AI reasoning or computer execution.
    """

    def __init__(
        self,
        synchronizer,
        voice_bridge=None,
        tts_sync=None,
        *,
        computer_start_callback=None,
        computer_interrupt_callback=None,
    ):

        self.sync = synchronizer

        self.voice_bridge = (
            voice_bridge
        )

        self.tts_sync = (
            tts_sync
        )

        self.computer_start_callback = (
            computer_start_callback
        )

        self.computer_interrupt_callback = (
            computer_interrupt_callback
        )

    ############################################################
    # COMMAND START
    ############################################################

    def start_command(
        self,
        command: str,
    ) -> dict[str, Any]:

        if not self.sync.can_accept_voice_command():

            return {
                "success":
                    False,

                "error":
                    "Voice command cannot start in current state.",

                "state":
                    self.sync.snapshot(),
            }

        task_id = (
            self.sync.begin_task(
                command
            )
        )

        if callable(
            self.computer_start_callback
        ):

            try:

                self.computer_start_callback(
                    command,
                    task_id,
                )

            except TypeError:

                self.computer_start_callback(
                    command
                )

        return {
            "success":
                True,

            "task_id":
                task_id,
        }

    ############################################################
    # COMPUTER START
    ############################################################

    def computer_started(
        self,
        task_id: int,
    ) -> bool:

        if not self.sync.is_current_task(
            task_id
        ):

            return False

        self.sync.set_computer_active()

        return True

    ############################################################
    # COMPUTER COMPLETE
    ############################################################

    def computer_completed(
        self,
        task_id: int,
    ) -> bool:

        completed = (
            self.sync.complete_task(
                task_id
            )
        )

        if completed:

            if self.tts_sync is not None:

                try:

                    self.tts_sync.cancel(
                        "Computer task completed; old speech generation invalidated."
                    )

                except Exception:
                    pass

        return completed

    ############################################################
    # COMPUTER ERROR
    ############################################################

    def computer_failed(
        self,
        task_id: int,
        error: str,
    ) -> bool:

        return self.sync.fail_task(
            task_id,
            error,
        )

    ############################################################
    # SPEAK
    ############################################################

    def speak(
        self,
        text: str,
    ) -> dict[str, Any]:

        if self.tts_sync is None:

            return {
                "success":
                    False,

                "error":
                    "TTS synchronizer is not configured.",
            }

        if not self.sync.can_speak():

            return {
                "success":
                    False,

                "error":
                    "Speech is blocked in the current runtime state.",
            }

        return self.tts_sync.speak(
            text
        )

    ############################################################
    # INTERRUPT EVERYTHING
    ############################################################

    def interrupt(
        self,
        reason: str = "Interrupted by user.",
    ) -> dict[str, Any]:

        state = (
            self.sync.request_interrupt(
                reason
            )
        )

        if self.tts_sync is not None:

            try:

                self.tts_sync.cancel(
                    reason
                )

            except Exception:
                pass

        if callable(
            self.computer_interrupt_callback
        ):

            try:

                self.computer_interrupt_callback(
                    reason
                )

            except TypeError:

                self.computer_interrupt_callback()

        return state

    ############################################################
    # STATE
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "synchronizer":
                self.sync.snapshot(),

            "tts":
                (
                    self.tts_sync.snapshot()
                    if self.tts_sync is not None
                    else
                    {}
                ),

            "voice_bridge":
                (
                    self.voice_bridge.snapshot()
                    if self.voice_bridge is not None
                    else
                    {}
                ),
        }