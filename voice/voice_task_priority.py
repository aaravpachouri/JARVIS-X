from __future__ import annotations

import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional


class VoiceTaskPriority(IntEnum):

    BACKGROUND = 10
    NORMAL = 50
    IMPORTANT = 75
    INTERRUPT = 100


@dataclass
class VoiceTaskLease:

    task_id: int

    priority: VoiceTaskPriority

    command: str = ""

    acquired_at: float = 0.0

    active: bool = True

    metadata: dict[str, Any] | None = None

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "task_id":
                self.task_id,

            "priority":
                int(
                    self.priority
                ),

            "command":
                self.command,

            "acquired_at":
                self.acquired_at,

            "active":
                self.active,

            "metadata":
                dict(
                    self.metadata
                    or
                    {}
                ),
        }


class VoiceTaskPriorityManager:

    """
    Priority/ownership coordinator for voice-originated tasks.

    It does not execute tasks. It decides which task generation
    currently owns the interaction channel.

    Higher-priority requests may preempt lower-priority work.
    Equal/lower-priority requests are rejected while an active lease
    exists unless the current owner releases it.
    """

    def __init__(self):

        self._current: Optional[
            VoiceTaskLease
        ] = None

        self._generation = 0

        self._history: list[
            dict[str, Any]
        ] = []

    ############################################################
    # ACQUIRE
    ############################################################

    def acquire(
        self,
        command: str = "",
        priority: VoiceTaskPriority = VoiceTaskPriority.NORMAL,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> dict[str, Any]:

        try:
            priority = VoiceTaskPriority(
                priority
            )
        except Exception:
            priority = VoiceTaskPriority.NORMAL

        current = self._current

        if (
            current is not None
            and
            current.active
        ):

            ####################################################
            # Reject same/lower priority while current task owns
            # the interaction channel.
            ####################################################

            if priority <= current.priority:

                return {
                    "acquired":
                        False,

                    "preempt":
                        False,

                    "task_id":
                        current.task_id,

                    "reason":
                        (
                            "Current voice task has equal or "
                            "higher priority."
                        ),
                }

            ####################################################
            # Higher priority request preempts current owner.
            ####################################################

            current.active = False

            self._record(
                "preempted",
                {
                    "task_id":
                        current.task_id,

                    "new_priority":
                        int(
                            priority
                        ),
                },
            )

        self._generation += 1

        lease = VoiceTaskLease(
            task_id=self._generation,

            priority=priority,

            command=str(
                command
                or
                ""
            ).strip(),

            acquired_at=time.monotonic(),

            active=True,

            metadata=dict(
                metadata
                or
                {}
            ),
        )

        self._current = lease

        self._record(
            "acquired",
            lease.to_dict(),
        )

        return {
            "acquired":
                True,

            "preempt":
                current is not None,

            "task_id":
                lease.task_id,

            "lease":
                lease.to_dict(),
        }

    ############################################################
    # RELEASE
    ############################################################

    def release(
        self,
        task_id: int,
    ) -> bool:

        current = self._current

        if (
            current is None
            or
            not current.active
            or
            current.task_id
            !=
            int(
                task_id
            )
        ):

            return False

        current.active = False

        self._record(
            "released",
            {
                "task_id":
                    current.task_id,
            },
        )

        return True

    ############################################################
    # OWNERSHIP
    ############################################################

    def owns(
        self,
        task_id: int,
    ) -> bool:

        current = self._current

        return bool(
            current is not None
            and
            current.active
            and
            current.task_id
            ==
            int(
                task_id
            )
        )

    def current(
        self,
    ) -> Optional[
        VoiceTaskLease
    ]:

        return self._current

    ############################################################
    # PREEMPT
    ############################################################

    def preempt(
        self,
        reason: str = "Higher-priority task requested.",
    ) -> Optional[int]:

        current = self._current

        if (
            current is None
            or
            not current.active
        ):

            return None

        current.active = False

        self._record(
            "preempted",
            {
                "task_id":
                    current.task_id,

                "reason":
                    str(
                        reason
                        or
                        ""
                    ),
            },
        )

        return current.task_id

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "generation":
                self._generation,

            "current":
                (
                    self._current.to_dict()
                    if self._current is not None
                    else
                    None
                ),

            "history":
                list(
                    self._history[
                        -20:
                    ]
                ),
        }

    ############################################################
    # INTERNAL
    ############################################################

    def _record(
        self,
        event: str,
        data: dict[str, Any],
    ):

        self._history.append(
            {
                "timestamp":
                    time.monotonic(),

                "event":
                    event,

                "data":
                    dict(
                        data
                    ),
            }
        )

        if len(
            self._history
        ) > 50:

            del self._history[
                :-
                50
            ]