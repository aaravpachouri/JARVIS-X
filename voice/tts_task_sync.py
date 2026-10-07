from __future__ import annotations

import threading
import time
from typing import Any, Optional


class TTSTaskSynchronizer:

    """
    Synchronizes TTS lifecycle with voice/computer task state.

    It does not synthesize speech itself. It coordinates an injected
    TTS engine and makes sure stale speech cannot continue after a
    task is interrupted, superseded, or cancelled.
    """

    def __init__(
        self,
        tts=None,
        state_sync=None,
    ):

        self.tts = tts
        self.state_sync = state_sync

        self._lock = threading.Lock()

        self.speech_generation = 0

        self.active_generation = 0

        self.speaking = False

        self.cancel_requested = False

        self.last_text = ""

        self.last_error = ""

    ############################################################
    # BIND
    ############################################################

    def bind_tts(
        self,
        tts,
    ):

        self.tts = tts

    def bind_state_sync(
        self,
        state_sync,
    ):

        self.state_sync = state_sync

    ############################################################
    # SPEAK
    ############################################################

    def speak(
        self,
        text: str,
    ) -> dict[str, Any]:

        text = str(
            text
            or
            ""
        ).strip()

        if not text:

            return {
                "success":
                    False,

                "error":
                    "TTS text is empty.",
            }

        with self._lock:

            self.speech_generation += 1

            generation = (
                self.speech_generation
            )

            self.active_generation = (
                generation
            )

            self.cancel_requested = False

            self.speaking = True

            self.last_text = text

            self.last_error = ""

        if (
            self.state_sync is not None
            and
            hasattr(
                self.state_sync,
                "set_speaking",
            )
        ):

            try:
                self.state_sync.set_speaking()
            except Exception:
                pass

        try:

            speaker = getattr(
                self.tts,
                "speak",
                None,
            )

            if not callable(
                speaker
            ):

                raise RuntimeError(
                    "TTS engine has no speak() method."
                )

            speaker(
                text
            )

            with self._lock:

                current = (
                    generation
                    ==
                    self.active_generation
                )

                cancelled = (
                    self.cancel_requested
                )

            ####################################################
            # A stale generation must not restore an old voice
            # state after a newer speech/task has taken ownership.
            ####################################################

            if not current or cancelled:

                return {
                    "success":
                        False,

                    "cancelled":
                        True,

                    "generation":
                        generation,
                }

            return {
                "success":
                    True,

                "generation":
                    generation,
            }

        except Exception as exc:

            with self._lock:

                if generation == self.active_generation:

                    self.speaking = False

                    self.last_error = str(
                        exc
                    )

            return {
                "success":
                    False,

                "generation":
                    generation,

                "error":
                    str(
                        exc
                    ),
            }

        finally:

            with self._lock:

                if generation == self.active_generation:

                    self.speaking = False

                    if (
                        not self.cancel_requested
                    ):
                        self.last_error = ""

    ############################################################
    # CANCEL
    ############################################################

    def cancel(
        self,
        reason: str = "Speech cancelled.",
    ) -> dict[str, Any]:

        with self._lock:

            self.cancel_requested = True

            self.speech_generation += 1

            cancelled_generation = (
                self.active_generation
            )

            self.active_generation = (
                self.speech_generation
            )

            self.speaking = False

            self.last_error = ""

        ########################################################
        # Use the current TTS cancellation API when available.
        ########################################################

        try:

            cancel = getattr(
                self.tts,
                "cancel",
                None,
            )

            if callable(
                cancel
            ):

                cancel()

            else:

                stop = getattr(
                    self.tts,
                    "stop",
                    None,
                )

                if callable(
                    stop
                ):

                    stop()

        except Exception as exc:

            return {
                "success":
                    False,

                "cancelled":
                    True,

                "generation":
                    cancelled_generation,

                "reason":
                    str(
                        reason
                    ),

                "error":
                    str(
                        exc
                    ),
            }

        return {
            "success":
                True,

            "cancelled":
                True,

            "generation":
                cancelled_generation,

            "reason":
                str(
                    reason
                    or
                    "Speech cancelled."
                ),
        }

    ############################################################
    # REPLAY SAFETY
    ############################################################

    def can_continue(
        self,
        generation: int,
    ) -> bool:

        with self._lock:

            return (
                int(
                    generation
                )
                ==
                int(
                    self.active_generation
                )
                and
                not self.cancel_requested
            )

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        with self._lock:

            return {
                "speaking":
                    self.speaking,

                "speech_generation":
                    self.speech_generation,

                "active_generation":
                    self.active_generation,

                "cancel_requested":
                    self.cancel_requested,

                "last_text":
                    self.last_text,

                "last_error":
                    self.last_error,
            }