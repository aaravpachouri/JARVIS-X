from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Iterator


############################################################
# LATENCY RECORD
############################################################

@dataclass
class LatencyRecord:

    name: str

    duration: float

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# LATENCY PROFILER
############################################################

class LatencyProfiler:

    """
    Lightweight timing system for JARVIS.

    It only measures execution time.

    It does NOT alter execution flow.
    """

    def __init__(self):

        self.records: list[
            LatencyRecord
        ] = []

    ########################################################
    # MEASURE BLOCK
    ########################################################

    @contextmanager
    def measure(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[None]:

        started = perf_counter()

        try:

            yield

        finally:

            elapsed = (
                perf_counter()
                -
                started
            )

            self.records.append(
                LatencyRecord(
                    name=str(
                        name
                    ),
                    duration=elapsed,
                    metadata=dict(
                        metadata or {}
                    ),
                )
            )

            ################################################
            # Keep memory bounded.
            ################################################

            if len(
                self.records
            ) > 200:

                del self.records[:-200]

    ########################################################
    # MANUAL RECORD
    ########################################################

    def record(
        self,
        name: str,
        duration: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:

        self.records.append(
            LatencyRecord(
                name=str(
                    name
                ),
                duration=float(
                    duration
                ),
                metadata=dict(
                    metadata or {}
                ),
            )
        )

        if len(
            self.records
        ) > 200:

            del self.records[:-200]

    ########################################################
    # LATEST
    ########################################################

    def latest(
        self,
        name: str,
    ) -> LatencyRecord | None:

        name = str(
            name
        )

        for record in reversed(
            self.records
        ):

            if record.name == name:

                return record

        return None

    ########################################################
    # SUMMARY
    ########################################################

    def summary(
        self,
    ) -> dict[str, dict[str, float]]:

        grouped: dict[
            str,
            list[float],
        ] = {}

        for record in self.records:

            grouped.setdefault(
                record.name,
                [],
            ).append(
                record.duration
            )

        result = {}

        for name, values in grouped.items():

            result[name] = {
                "count":
                    float(
                        len(
                            values
                        )
                    ),

                "last":
                    values[-1],

                "average":
                    sum(
                        values
                    )
                    /
                    len(
                        values
                    ),

                "minimum":
                    min(
                        values
                    ),

                "maximum":
                    max(
                        values
                    ),
            }

        return result

    ########################################################
    # SLOWEST
    ########################################################

    def slowest(
        self,
        limit: int = 10,
    ) -> list[LatencyRecord]:

        try:

            limit = max(
                1,
                int(
                    limit
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            limit = 10

        return sorted(
            self.records,
            key=lambda record:
                record.duration,
            reverse=True,
        )[:limit]

    ########################################################
    # TOTAL
    ########################################################

    def total_duration(
        self,
    ) -> float:

        return sum(
            record.duration
            for record
            in self.records
        )

    ########################################################
    # CLEAR
    ########################################################

    def clear(
        self,
    ) -> None:

        self.records.clear()

    ########################################################
    # REPORT
    ########################################################

    def report(
        self,
    ) -> str:

        summary = self.summary()

        if not summary:

            return (
                "No latency measurements recorded."
            )

        lines = [
            "JARVIS LATENCY REPORT",
            "=" * 60,
        ]

        ordered = sorted(
            summary.items(),
            key=lambda item:
                item[1]["average"],
            reverse=True,
        )

        for name, data in ordered:

            lines.append(
                (
                    f"{name}: "
                    f"avg={data['average']:.3f}s "
                    f"last={data['last']:.3f}s "
                    f"max={data['maximum']:.3f}s "
                    f"count={int(data['count'])}"
                )
            )

        return "\n".join(
            lines
        )