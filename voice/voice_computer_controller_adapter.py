from __future__ import annotations

from typing import Any, Optional


class VoiceComputerControllerAdapter:

    """
    Thin adapter for integrating the Phase 8.7 synchronization
    coordinator with existing VoiceController / AIController code.

    It does not replace either controller.

    Responsibilities:
        - start synchronized command generations
        - notify computer-task lifecycle
        - route interruption requests
        - route speech through the synchronized TTS layer
        - reject stale task completions
    """

    def __init__(
        self,
        coordinator,
        *,
        voice_controller=None,
        ai_controller=None,
    ):

        self.coordinator = coordinator

        self.voice_controller = (
            voice_controller
        )

        self.ai_controller = (
            ai_controller
        )

    ############################################################
    # COMMAND
    ############################################################

    def begin_command(
        self,
        command: str,
    ) -> dict[str, Any]:

        return self.coordinator.start_command(
            command
        )

    ############################################################
    # COMPUTER
    ############################################################

    def computer_started(
        self,
        task_id: int,
    ) -> bool:

        return self.coordinator.computer_started(
            task_id
        )

    def computer_finished(
        self,
        task_id: int,
        result: Any = None,
    ) -> bool:

        return self.coordinator.computer_finished(
            task_id,
            result,
        )

    def computer_failed(
        self,
        task_id: int,
        error: str,
    ) -> bool:

        return self.coordinator.computer_failed(
            task_id,
            error,
        )

    ############################################################
    # SPEECH
    ############################################################

    def speak(
        self,
        text: str,
        task_id: int = 0,
    ) -> dict[str, Any]:

        return self.coordinator.speak(
            text,
            task_id=task_id,
        )

    ############################################################
    # INTERRUPTION
    ############################################################

    def interrupt(
        self,
        reason: str = "Interrupted by user.",
    ) -> dict[str, Any]:

        return self.coordinator.interrupt(
            reason
        )

    def resume_voice(
        self,
    ) -> dict[str, Any]:

        return self.coordinator.resume_voice()

    ############################################################
    # STALE RESULT GATE
    ############################################################

    def accepts_result(
        self,
        task_id: int,
    ) -> bool:

        sync = getattr(
            self.coordinator,
            "sync",
            None,
        )

        if sync is None:
            return False

        if sync.is_interrupt_requested():
            return False

        return sync.is_current_task(
            task_id
        )

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return self.coordinator.snapshot()


def create_controller_adapter(
    coordinator,
    *,
    voice_controller=None,
    ai_controller=None,
):

    return VoiceComputerControllerAdapter(
        coordinator,
        voice_controller=voice_controller,
        ai_controller=ai_controller,
    )