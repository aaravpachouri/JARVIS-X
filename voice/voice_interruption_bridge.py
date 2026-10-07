from __future__ import annotations

from typing import Any, Optional


class VoiceInterruptionBridge:
    """
    Adapter between the existing VoiceController / AIController
    lifecycle and VoiceComputerSynchronizer.

    It intentionally uses duck-typed signal/callback discovery so the
    existing VoiceController implementation does not need to be
    rewritten just to add synchronization.

    Responsibilities:
        - synchronize voice activation/deactivation
        - mark command/task ownership
        - detect interrupt phrases
        - propagate interruption to the computer runtime
        - prevent stale task completion from reviving old state
    """

    INTERRUPT_PHRASES = {
        "stop",
        "stop jarvis",
        "jarvis stop",
        "cancel",
        "cancel this",
        "cancel that",
        "abort",
        "abort this",
        "wait",
        "wait jarvis",
        "hold on",
        "never mind",
        "nevermind",
        "stop this",
        "stop the task",
        "stop current task",
    }

    def __init__(
        self,
        voice_controller,
        synchronizer,
        *,
        interrupt_callback=None,
        command_callback=None,
    ):

        self.voice = (
            voice_controller
        )

        self.sync = (
            synchronizer
        )

        self.interrupt_callback = (
            interrupt_callback
        )

        self.command_callback = (
            command_callback
        )

        self._connected = False

    ############################################################
    # CONNECT
    ############################################################

    def connect(
        self,
    ) -> bool:

        if self.voice is None:
            return False

        connected_any = False

        connected_any |= self._connect_signal(
            "activated",
            self._on_activated,
        )

        connected_any |= self._connect_signal(
            "deactivated",
            self._on_deactivated,
        )

        connected_any |= self._connect_signal(
            "commandRecognized",
            self._on_command,
        )

        connected_any |= self._connect_signal(
            "commandFinished",
            self._on_command_finished,
        )

        connected_any |= self._connect_signal(
            "error",
            self._on_error,
        )

        self._connected = connected_any

        return connected_any

    def _connect_signal(
        self,
        name,
        callback,
    ) -> bool:

        signal = getattr(
            self.voice,
            name,
            None,
        )

        if signal is None:
            return False

        connect = getattr(
            signal,
            "connect",
            None,
        )

        if not callable(
            connect
        ):
            return False

        try:

            connect(
                callback
            )

            return True

        except Exception:

            return False

    ############################################################
    # VOICE LIFECYCLE
    ############################################################

    def _on_activated(
        self,
        *args,
        **kwargs,
    ):

        if self.sync.is_interrupt_requested():
            return

        self.sync.set_listening()

    def _on_deactivated(
        self,
        *args,
        **kwargs,
    ):

        self.sync.set_dormant()

    ############################################################
    # COMMAND
    ############################################################

    def _on_command(
        self,
        command="",
        *args,
        **kwargs,
    ):

        command_text = str(
            command
            or
            ""
        ).strip()

        if not command_text:
            return

        if self.is_interrupt_phrase(
            command_text
        ):

            self.request_interrupt(
                (
                    "Voice interruption: "
                    +
                    command_text
                )
            )

            return

        ########################################################
        # A normal voice command becomes the owner of a new
        # synchronized computer/runtime generation.
        ########################################################

        self.sync.set_processing()

        task_id = (
            self.sync.begin_task(
                command_text
            )
        )

        if callable(
            self.command_callback
        ):

            try:

                self.command_callback(
                    command_text,
                    task_id,
                )

            except TypeError:

                self.command_callback(
                    command_text
                )

    ############################################################
    # COMMAND FINISHED
    ############################################################

    def _on_command_finished(
        self,
        *args,
        **kwargs,
    ):

        ########################################################
        # Existing VoiceController may emit this after either a
        # normal response or a cancellation. Do not blindly mark
        # a stale task complete.
        ########################################################

        if self.sync.is_interrupt_requested():

            self.sync.acknowledge_interrupt()

            return

        self.sync.set_listening()

    ############################################################
    # ERROR
    ############################################################

    def _on_error(
        self,
        error="",
        *args,
        **kwargs,
    ):

        self.sync.fail_task(
            self.sync.active_task_id,
            str(
                error
                or
                "Voice subsystem error."
            ),
        )

    ############################################################
    # EXTERNAL COMPUTER EVENTS
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

    def computer_finished(
        self,
        task_id: int,
    ) -> bool:

        return self.sync.complete_task(
            task_id
        )

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
    # INTERRUPTION
    ############################################################

    def request_interrupt(
        self,
        reason: str = "Task interrupted by voice.",
    ) -> dict[str, Any]:

        state = (
            self.sync.request_interrupt(
                reason
            )
        )

        ########################################################
        # Notify the existing computer runtime. The callback is
        # intentionally injected so this adapter doesn't import
        # or own AIController/ComputerUseAgent.
        ########################################################

        if callable(
            self.interrupt_callback
        ):

            try:

                self.interrupt_callback(
                    reason
                )

            except TypeError:

                self.interrupt_callback()

        return state

    ############################################################
    # PHRASE DETECTION
    ############################################################

    @classmethod
    def is_interrupt_phrase(
        cls,
        command: str,
    ) -> bool:

        text = str(
            command
            or
            ""
        ).strip().lower()

        if text in cls.INTERRUPT_PHRASES:
            return True

        prefixes = (
            "stop jarvis",
            "jarvis stop",
            "cancel this",
            "stop the task",
            "stop current task",
        )

        return any(
            text.startswith(
                prefix
                +
                " "
            )
            for prefix in prefixes
        )

    ############################################################
    # STATE
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "connected":
                self._connected,

            "synchronizer":
                self.sync.snapshot(),
        }


def create_voice_interruption_bridge(
    voice_controller,
    synchronizer,
    *,
    interrupt_callback=None,
    command_callback=None,
):

    bridge = (
        VoiceInterruptionBridge(
            voice_controller,
            synchronizer,
            interrupt_callback=interrupt_callback,
            command_callback=command_callback,
        )
    )

    bridge.connect()

    return bridge