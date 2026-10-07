from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Optional


############################################################
# TTS LATENCY METRICS
############################################################

@dataclass
class TTSLatency:

    total_time: float = 0.0

    preparation_time: float = 0.0

    synthesis_time: float = 0.0

    first_audio_time: float = 0.0

    chunks: int = 0

    metadata: dict[str, Any] = None

    def __post_init__(self):

        if self.metadata is None:

            self.metadata = {}


############################################################
# TTS RESPONSIVENESS TRACKER
############################################################

class TTSResponsivenessTracker:

    """
    Measures how quickly JARVIS gets from generated text to
    the first playable audio.

    This does not perform TTS itself.
    """

    def __init__(self):

        self.records: list[
            TTSLatency
        ] = []

    ########################################################
    # MEASURE
    ########################################################

    def measure(
        self,
        text: str,
        prepare: Callable[[], Any],
        synthesize: Callable[
            [Any],
            Any,
        ],
        play: Callable[
            [Any],
            None,
        ],
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> TTSLatency:

        started = perf_counter()

        ####################################################
        # Preparation
        ####################################################

        prepared_started = perf_counter()

        prepared = prepare()

        preparation_time = (
            perf_counter()
            -
            prepared_started
        )

        ####################################################
        # First synthesis
        ####################################################

        synthesis_started = perf_counter()

        audio = synthesize(
            prepared
        )

        synthesis_time = (
            perf_counter()
            -
            synthesis_started
        )

        first_audio_time = (
            perf_counter()
            -
            started
        )

        ####################################################
        # Start playback immediately.
        ####################################################

        play(
            audio
        )

        total_time = (
            perf_counter()
            -
            started
        )

        metrics = TTSLatency(
            total_time=total_time,

            preparation_time=(
                preparation_time
            ),

            synthesis_time=(
                synthesis_time
            ),

            first_audio_time=(
                first_audio_time
            ),

            chunks=1,

            metadata={
                "text_length":
                    len(
                        str(
                            text or ""
                        )
                    ),

                **dict(
                    metadata or {}
                ),
            },
        )

        self.records.append(
            metrics
        )

        if len(
            self.records
        ) > 100:

            del self.records[:-100]

        return metrics

    ########################################################
    # SUMMARY
    ########################################################

    def summary(
        self,
    ) -> dict[str, float]:

        if not self.records:

            return {
                "first_audio_average": 0.0,
                "first_audio_minimum": 0.0,
                "first_audio_maximum": 0.0,
                "total_average": 0.0,
            }

        first_audio = [
            item.first_audio_time
            for item in self.records
        ]

        total = [
            item.total_time
            for item in self.records
        ]

        return {
            "first_audio_average":
                sum(
                    first_audio
                )
                /
                len(
                    first_audio
                ),

            "first_audio_minimum":
                min(
                    first_audio
                ),

            "first_audio_maximum":
                max(
                    first_audio
                ),

            "total_average":
                sum(
                    total
                )
                /
                len(
                    total
                ),
        }

    ########################################################
    # CLEAR
    ########################################################

    def clear(
        self,
    ):

        self.records.clear()