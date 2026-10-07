from __future__ import annotations

import time
from enum import Enum
from threading import Lock
from typing import Any, Optional


class VoiceComputerState(str, Enum):

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    COMPUTER_ACTIVE = "COMPUTER_ACTIVE"
    SPEAKING = "SPEAKING"
    INTERRUPTING = "INTERRUPTING"
    CANCELLING = "CANCELLING"
    DORMANT = "DORMANT"
    ERROR = "ERROR"


class VoiceComputerSynchronizer:
    """
    Synchronizes voice lifecycle with computer-task lifecycle.

    This is intentionally a state coordinator, not a speech recognizer
    and not a computer executor.

    Responsibilities:
        - maintain a single synchronized runtime state
        - prevent stale voice/computer transitions
        - propagate user interruption intent
        - manage active task ownership
        - expose compact state to UI/controllers
    """

    def __init__(self):

        self._lock = Lock()

        self.state = (
            VoiceComputerState.IDLE
        )

        self.active_task_id = 0

        self.task_generation = 0

        self.interrupt_requested = False

        self.interrupt_reason = ""

        self.last_transition_at = (
            time.monotonic()
        )

        self.last_command = ""

        self.last_error = ""

    ############################################################
    # TASK OWNERSHIP
    ############################################################

    def begin_task(
        self,
        command: str = "",
    ) -> int:

        with self._lock:

            self.task_generation += 1

            self.active_task_id = (
                self.task_generation
            )

            self.interrupt_requested = False

            self.interrupt_reason = ""

            self.last_command = str(
                command
                or
                ""
            ).strip()

            self.last_error = ""

            self._set_state(
                VoiceComputerState.COMPUTER_ACTIVE
            )

            return self.active_task_id

    def is_current_task(
        self,
        task_id: int,
    ) -> bool:

        with self._lock:

            return (
                int(task_id)
                ==
                self.active_task_id
                and
                int(task_id) != 0
            )

    ############################################################
    # VOICE STATES
    ############################################################

    def set_listening(
        self,
    ):

        with self._lock:

            if (
                self.state
                not in {
                    VoiceComputerState.INTERRUPTING,
                    VoiceComputerState.CANCELLING,
                }
            ):

                self._set_state(
                    VoiceComputerState.LISTENING
                )

    def set_processing(
        self,
    ):

        with self._lock:

            self._set_state(
                VoiceComputerState.PROCESSING
            )

    def set_speaking(
        self,
    ):

        with self._lock:

            self._set_state(
                VoiceComputerState.SPEAKING
            )

    def set_dormant(
        self,
    ):

        with self._lock:

            self._set_state(
                VoiceComputerState.DORMANT
            )

    ############################################################
    # COMPUTER STATES
    ############################################################

    def set_computer_active(
        self,
    ):

        with self._lock:

            if self.interrupt_requested:

                return

            self._set_state(
                VoiceComputerState.COMPUTER_ACTIVE
            )

    def set_idle(
        self,
    ):

        with self._lock:

            if self.interrupt_requested:

                return

            self.active_task_id = 0

            self._set_state(
                VoiceComputerState.IDLE
            )

    ############################################################
    # INTERRUPTION
    ############################################################

    def request_interrupt(
        self,
        reason: str = "User interruption.",
    ) -> dict[str, Any]:

        with self._lock:

            self.interrupt_requested = True

            self.interrupt_reason = str(
                reason
                or
                "User interruption."
            )

            self._set_state(
                VoiceComputerState.INTERRUPTING
            )

            return self.snapshot()

    def begin_cancellation(
        self,
    ):

        with self._lock:

            self.interrupt_requested = True

            self._set_state(
                VoiceComputerState.CANCELLING
            )

    def is_interrupt_requested(
        self,
    ) -> bool:

        with self._lock:

            return bool(
                self.interrupt_requested
            )

    def acknowledge_interrupt(
        self,
    ):

        with self._lock:

            self.active_task_id = 0

            self._set_state(
                VoiceComputerState.LISTENING
            )

    def clear_interrupt(
        self,
    ):

        with self._lock:

            self.interrupt_requested = False

            self.interrupt_reason = ""

    ############################################################
    # TASK COMPLETION
    ############################################################

    def complete_task(
        self,
        task_id: int,
    ) -> bool:

        with self._lock:

            if (
                int(task_id)
                !=
                self.active_task_id
            ):

                return False

            if self.interrupt_requested:

                return False

            self.active_task_id = 0

            self._set_state(
                VoiceComputerState.IDLE
            )

            return True

    def fail_task(
        self,
        task_id: int,
        error: str,
    ) -> bool:

        with self._lock:

            if (
                int(task_id)
                !=
                self.active_task_id
            ):

                return False

            self.last_error = str(
                error
                or
                ""
            )

            self.active_task_id = 0

            self._set_state(
                VoiceComputerState.ERROR
            )

            return True

    ############################################################
    # TRANSITION VALIDATION
    ############################################################

    def can_accept_voice_command(
        self,
    ) -> bool:

        with self._lock:

            return self.state in {
                VoiceComputerState.IDLE,
                VoiceComputerState.LISTENING,
            }

    def can_speak(
        self,
    ) -> bool:

        with self._lock:

            return (
                self.state
                !=
                VoiceComputerState.DORMANT
            )

    def can_start_computer_task(
        self,
    ) -> bool:

        with self._lock:

            return (
                not self.interrupt_requested
                and
                self.state
                not in {
                    VoiceComputerState.CANCELLING,
                    VoiceComputerState.INTERRUPTING,
                }
            )

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        with self._lock:

            return {
                "state":
                    self.state.value,

                "active_task_id":
                    self.active_task_id,

                "task_generation":
                    self.task_generation,

                "interrupt_requested":
                    self.interrupt_requested,

                "interrupt_reason":
                    self.interrupt_reason,

                "last_command":
                    self.last_command,

                "last_error":
                    self.last_error,

                "last_transition_at":
                    self.last_transition_at,
            }

    ############################################################
    # INTERNAL
    ############################################################

    def _set_state(
        self,
        state: VoiceComputerState,
    ):

        self.state = state

        self.last_transition_at = (
            time.monotonic()
        )