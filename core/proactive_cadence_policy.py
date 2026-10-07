from __future__ import annotations

import time
from typing import Any, Optional


class ProactiveCadencePolicy:

    """
    Prevents proactive JARVIS from becoming noisy or repetitive.

    It limits how often similar opportunities can be surfaced and
    supports cooldowns, daily caps, and quiet periods.
    """

    def __init__(
        self,
        *,
        cooldown_seconds: float = 300.0,
        max_notifications_per_day: int = 10,
        quiet_start_hour: Optional[int] = None,
        quiet_end_hour: Optional[int] = None,
    ):

        self.cooldown_seconds = max(
            0.0,
            float(
                cooldown_seconds
            ),
        )

        self.max_notifications_per_day = max(
            1,
            int(
                max_notifications_per_day
            ),
        )

        self.quiet_start_hour = quiet_start_hour

        self.quiet_end_hour = quiet_end_hour

        self._history: list[
            dict[str, Any]
        ] = []

    def allow(
        self,
        opportunity,
    ) -> dict[str, Any]:

        data = self._normalize(
            opportunity
        )

        if not data:
            return {
                "allowed": False,
                "reason": "Invalid proactive opportunity.",
            }

        now = time.time()

        if self._quiet_hours():
            return {
                "allowed": False,
                "reason": "Proactive notifications are currently in quiet hours.",
            }

        today_count = self._today_count(
            now
        )

        if (
            today_count
            >=
            self.max_notifications_per_day
        ):
            return {
                "allowed": False,
                "reason": "Daily proactive notification limit reached.",
            }

        opportunity_key = self._key(
            data
        )

        for event in reversed(
            self._history
        ):

            if event.get(
                "key"
            ) != opportunity_key:
                continue

            age = (
                now
                -
                float(
                    event.get(
                        "timestamp",
                        now,
                    )
                    or
                    now
                )
            )

            if age < self.cooldown_seconds:

                return {
                    "allowed": False,
                    "reason": "Similar proactive opportunity is still within cooldown.",
                    "cooldown_remaining": (
                        self.cooldown_seconds
                        -
                        age
                    ),
                }

            break

        return {
            "allowed": True,
            "reason": "Proactive cadence policy allows delivery.",
        }

    def record(
        self,
        opportunity,
    ):

        data = self._normalize(
            opportunity
        )

        if not data:
            return

        self._history.append(
            {
                "timestamp": time.time(),
                "key": self._key(data),
            }
        )

        if len(
            self._history
        ) > 200:

            del self._history[
                :-
                200
            ]

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "cooldown_seconds":
                self.cooldown_seconds,

            "max_notifications_per_day":
                self.max_notifications_per_day,

            "history_count":
                len(
                    self._history
                ),
        }

    def _today_count(
        self,
        now,
    ) -> int:

        local = time.localtime(
            now
        )

        return sum(
            1
            for item
            in self._history
            if (
                time.localtime(
                    float(
                        item.get(
                            "timestamp",
                            0.0
                        )
                    )
                ).tm_year
                ==
                local.tm_year
                and
                time.localtime(
                    float(
                        item.get(
                            "timestamp",
                            0.0
                        )
                    )
                ).tm_yday
                ==
                local.tm_yday
            )
        )

    def _quiet_hours(
        self,
    ) -> bool:

        if (
            self.quiet_start_hour is None
            or
            self.quiet_end_hour is None
        ):
            return False

        hour = time.localtime().tm_hour

        start = int(
            self.quiet_start_hour
        )

        end = int(
            self.quiet_end_hour
        )

        if start == end:
            return True

        if start < end:
            return start <= hour < end

        return (
            hour >= start
            or
            hour < end
        )

    @staticmethod
    def _key(
        data: dict[str, Any],
    ) -> str:

        return "|".join(
            [
                str(
                    data.get(
                        "trigger_type",
                        ""
                    )
                    or
                    ""
                ),
                str(
                    data.get(
                        "goal_id",
                        ""
                    )
                    or
                    ""
                ),
                str(
                    data.get(
                        "title",
                        ""
                    )
                    or
                    ""
                ),
            ]
        )

    @staticmethod
    def _normalize(
        value,
    ) -> dict[str, Any]:

        if isinstance(
            value,
            dict
        ):
            return dict(
                value
            )

        if hasattr(
            value,
            "to_dict"
        ):

            try:

                data = value.to_dict()

                return (
                    data
                    if isinstance(
                        data,
                        dict
                    )
                    else
                    {}
                )

            except Exception:
                pass

        return {}