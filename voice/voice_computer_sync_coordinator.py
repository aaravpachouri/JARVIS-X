from __future__ import annotations

from typing import Any, Optional

from voice.voice_computer_sync import VoiceComputerSynchronizer
from voice.voice_interruption_recovery import VoiceInterruptionRecovery
from voice.tts_task_sync import TTSTaskSynchronizer
from voice.voice_task_priority import VoiceTaskPriorityManager, VoiceTaskPriority
from voice.voice_computer_event_bus import VoiceComputerEventBus


class VoiceComputerSyncCoordinator:

    """
    Unified synchronization facade for Phase 8.7.

    Combines:
        - voice/computer state synchronization
        - task priority/ownership
        - interruption/recovery
        - TTS synchronization
        - voice/computer event publication

    It does not replace VoiceController, AIController, or
    ComputerUseAgent. Those remain the actual runtime components.
    """

    def __init__(
        self,
        *,
        tts=None,
        event_bus: Optional[
            VoiceComputerEventBus
        ] = None,
        synchronizer: Optional[
            VoiceComputerSynchronizer
        ] = None,
        task_priority: Optional[
            VoiceTaskPriorityManager
        ] = None,
        computer_start_callback=None,
        computer_interrupt_callback=None,
    ):

        self.sync = (
            synchronizer
            or
            VoiceComputerSynchronizer()
        )

        self.event_bus = (
            event_bus
            or
            VoiceComputerEventBus()
        )

        self.priority = (
            task_priority
            or
            VoiceTaskPriorityManager()
        )

        self.tts = (
            TTSTaskSynchronizer(
                tts=tts,
                state_sync=self.sync,
            )
        )

        self.recovery = (
            VoiceInterruptionRecovery(
                self.sync,
                self.tts,
                computer_interrupt_callback=(
                    computer_interrupt_callback
                ),
            )
        )

        self.computer_start_callback = (
            computer_start_callback
        )

    ############################################################
    # COMMAND START
    ############################################################

    def start_command(
        self,
        command: str,
        priority: VoiceTaskPriority = VoiceTaskPriority.NORMAL,
    ) -> dict[str, Any]:

        lease = self.priority.acquire(
            command=command,
            priority=priority,
        )

        if not lease.get(
            "acquired",
            False,
        ):

            return {
                "success":
                    False,

                "reason":
                    lease.get(
                        "reason",
                        "Voice task channel is busy.",
                    ),

                "priority":
                    lease,
            }

        task_id = (
            self.sync.begin_task(
                command
            )
        )

        ########################################################
        # Task ID from the synchronization layer is the canonical
        # runtime generation.
        ########################################################

        self.event_bus.command_started(
            task_id,
            command,
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

            "priority":
                lease,
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

        self.event_bus.computer_started(
            task_id
        )

        return True

    ############################################################
    # COMPUTER FINISH
    ############################################################

    def computer_finished(
        self,
        task_id: int,
        result: Any = None,
    ) -> bool:

        if not self.sync.complete_task(
            task_id
        ):

            return False

        self.priority.release(
            task_id
        )

        self.event_bus.computer_finished(
            task_id,
            result,
        )

        return True

    ############################################################
    # COMPUTER FAILURE
    ############################################################

    def computer_failed(
        self,
        task_id: int,
        error: str,
    ) -> bool:

        if not self.sync.fail_task(
            task_id,
            error,
        ):

            return False

        self.priority.release(
            task_id
        )

        self.event_bus.computer_failed(
            task_id,
            error,
        )

        return True

    ############################################################
    # SPEECH
    ############################################################

    def speak(
        self,
        text: str,
        task_id: int = 0,
    ) -> dict[str, Any]:

        result = (
            self.tts.speak(
                text
            )
        )

        if result.get(
            "success",
            False,
        ):

            self.event_bus.speech_started(
                task_id=task_id,
                generation=result.get(
                    "generation",
                    0,
                ),
            )

        return result

    ############################################################
    # INTERRUPTION
    ############################################################

    def interrupt(
        self,
        reason: str = "User interruption.",
    ) -> dict[str, Any]:

        task = self.priority.current()

        task_id = (
            task.task_id
            if task is not None
            else
            self.sync.active_task_id
        )

        result = (
            self.recovery.request(
                reason
            )
        )

        self.priority.preempt(
            reason
        )

        self.event_bus.interrupted(
            task_id=task_id,
            reason=reason,
        )

        self.event_bus.cancelled(
            task_id=task_id,
            reason=reason,
        )

        return result

    ############################################################
    # RESUME
    ############################################################

    def resume_voice(
        self,
    ) -> dict[str, Any]:

        result = (
            self.recovery.resume()
        )

        if result.get(
            "resumed",
            False,
        ):

            self.event_bus.state_changed(
                "LISTENING"
            )

        return result

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "sync":
                self.sync.snapshot(),

            "priority":
                self.priority.snapshot(),

            "tts":
                self.tts.snapshot(),

            "recovery":
                self.recovery.snapshot(),

            "events":
                self.event_bus.snapshot(),
        }