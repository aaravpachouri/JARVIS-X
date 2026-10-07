from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any


############################################################
# PERFORMANCE PROFILE
############################################################

@dataclass
class PerformanceProfile:

    # Computer-agent timing
    action_delay: float = 0.12
    observation_delay: float = 0.08

    # Reasoning budgets
    max_reasoning_seconds: float = 20.0
    max_observation_seconds: float = 5.0

    # TTS
    max_tts_chunk_chars: int = 420

    # Context limits
    max_history_items: int = 8
    max_record_items: int = 10

    # Safety
    allow_parallel_safe_operations: bool = True


############################################################
# PERFORMANCE TRACKER
############################################################

class PerformanceTracker:

    """
    Lightweight latency tracker.

    It measures where JARVIS spends time without changing
    how any executor works.
    """

    def __init__(self):

        self.records: list[
            dict[str, Any]
        ] = []

    def measure(
        self,
        name: str,
    ):

        return _PerformanceTimer(
            self,
            name,
        )

    def add(
        self,
        name: str,
        duration: float,
    ) -> None:

        self.records.append(
            {
                "name": str(
                    name
                ),
                "duration": float(
                    duration
                ),
            }
        )

        # Keep memory bounded.
        if len(
            self.records
        ) > 100:

            del self.records[:-100]

    def summary(
        self,
    ) -> dict[str, Any]:

        grouped: dict[
            str,
            list[float],
        ] = {}

        for record in self.records:

            grouped.setdefault(
                record["name"],
                [],
            ).append(
                record["duration"]
            )

        result = {}

        for name, values in grouped.items():

            result[name] = {
                "count":
                    len(values),

                "last":
                    values[-1],

                "average":
                    sum(values)
                    /
                    len(values),

                "max":
                    max(values),
            }

        return result

    def clear(
        self,
    ) -> None:

        self.records.clear()


############################################################
# TIMER
############################################################

class _PerformanceTimer:

    def __init__(
        self,
        tracker: PerformanceTracker,
        name: str,
    ):

        self.tracker = tracker
        self.name = name
        self.started = 0.0

    def __enter__(self):

        self.started = perf_counter()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        elapsed = (
            perf_counter()
            -
            self.started
        )

        self.tracker.add(
            self.name,
            elapsed,
        )

        return False


############################################################
# DEFAULT PROFILE
############################################################

DEFAULT_PERFORMANCE = (
    PerformanceProfile()
)