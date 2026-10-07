from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class VoiceComputerEvent:

    name: str

    timestamp: float = field(
        default_factory=time.monotonic
    )

    task_id: int = 0

    payload: dict[str, Any] = field(
        default_factory=dict
    )


class VoiceComputerEventBus:

    """
    Small synchronous event bus for voice/computer lifecycle events.

    It provides one event channel for:
        - command start/finish
        - computer task start/finish/failure
        - speech start/finish/cancel
        - interruption
        - cancellation
        - application transitions
        - synchronization state changes

    The bus does not execute computer actions or make scheduling
    decisions. Subscribers own those responsibilities.
    """

    def __init__(self):

        self._lock = Lock()

        self._subscribers: dict[
            str,
            list[Callable[..., Any]]
        ] = {}

        self._history: list[
            VoiceComputerEvent
        ] = []

        self.max_history = 100

    ############################################################
    # SUBSCRIBE
    ############################################################

    def subscribe(
        self,
        event_name: str,
        callback: Callable[..., Any],
    ) -> bool:

        name = str(
            event_name
            or
            ""
        ).strip()

        if (
            not name
            or
            not callable(
                callback
            )
        ):

            return False

        with self._lock:

            callbacks = self._subscribers.setdefault(
                name,
                []
            )

            if callback not in callbacks:

                callbacks.append(
                    callback
                )

        return True

    ############################################################
    # UNSUBSCRIBE
    ############################################################

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[..., Any],
    ) -> bool:

        name = str(
            event_name
            or
            ""
        ).strip()

        with self._lock:

            callbacks = self._subscribers.get(
                name,
                []
            )

            if callback not in callbacks:

                return False

            callbacks.remove(
                callback
            )

            if not callbacks:

                self._subscribers.pop(
                    name,
                    None
                )

        return True

    ############################################################
    # PUBLISH
    ############################################################

    def publish(
        self,
        event_name: str,
        *,
        task_id: int = 0,
        payload: Optional[
            dict[str, Any]
        ] = None,
    ) -> VoiceComputerEvent:

        event = (
            VoiceComputerEvent(
                name=str(
                    event_name
                    or
                    ""
                ).strip(),

                task_id=int(
                    task_id
                    or
                    0
                ),

                payload=dict(
                    payload
                    or
                    {}
                ),
            )
        )

        with self._lock:

            self._history.append(
                event
            )

            if len(
                self._history
            ) > self.max_history:

                del self._history[
                    :-
                    self.max_history
                ]

            callbacks = list(
                self._subscribers.get(
                    event.name,
                    []
                )
            )

            wildcard = list(
                self._subscribers.get(
                    "*",
                    []
                )
            )

        for callback in (
            callbacks
            +
            wildcard
        ):

            try:

                callback(
                    event
                )

            except Exception as exc:

                # Event listeners must never crash the publisher.
                print(
                    "[VoiceComputerEventBus] "
                    f"Subscriber error: {exc}"
                )

        return event

    ############################################################
    # COMMON EVENTS
    ############################################################

    def command_started(
        self,
        task_id: int,
        command: str,
    ):

        return self.publish(
            "command_started",
            task_id=task_id,
            payload={
                "command":
                    str(
                        command
                        or
                        ""
                    ).strip()
            }
        )

    def computer_started(
        self,
        task_id: int,
        command: str = "",
    ):

        return self.publish(
            "computer_started",
            task_id=task_id,
            payload={
                "command":
                    str(
                        command
                        or
                        ""
                    ).strip()
            }
        )

    def computer_finished(
        self,
        task_id: int,
        result: Any = None,
    ):

        return self.publish(
            "computer_finished",
            task_id=task_id,
            payload={
                "result":
                    result
            }
        )

    def computer_failed(
        self,
        task_id: int,
        error: str,
    ):

        return self.publish(
            "computer_failed",
            task_id=task_id,
            payload={
                "error":
                    str(
                        error
                        or
                        ""
                    )
            }
        )

    def speech_started(
        self,
        task_id: int = 0,
        generation: int = 0,
    ):

        return self.publish(
            "speech_started",
            task_id=task_id,
            payload={
                "generation":
                    generation
            }
        )

    def speech_cancelled(
        self,
        task_id: int = 0,
        generation: int = 0,
        reason: str = "",
    ):

        return self.publish(
            "speech_cancelled",
            task_id=task_id,
            payload={
                "generation":
                    generation,

                "reason":
                    str(
                        reason
                        or
                        ""
                    )
            }
        )

    def interrupted(
        self,
        task_id: int = 0,
        reason: str = "",
    ):

        return self.publish(
            "interrupted",
            task_id=task_id,
            payload={
                "reason":
                    str(
                        reason
                        or
                        ""
                    )
            }
        )

    def cancelled(
        self,
        task_id: int = 0,
        reason: str = "",
    ):

        return self.publish(
            "cancelled",
            task_id=task_id,
            payload={
                "reason":
                    str(
                        reason
                        or
                        ""
                    )
            }
        )

    def state_changed(
        self,
        state: str,
        task_id: int = 0,
    ):

        return self.publish(
            "state_changed",
            task_id=task_id,
            payload={
                "state":
                    str(
                        state
                        or
                        ""
                    )
            }
        )

    ############################################################
    # READ
    ############################################################

    def history(
        self,
        limit: int = 20,
    ) -> list[VoiceComputerEvent]:

        count = max(
            0,
            int(
                limit
            )
        )

        if count == 0:

            return []

        with self._lock:

            return list(
                self._history[
                    -count:
                ]
            )

    def clear_history(
        self,
    ):

        with self._lock:

            self._history.clear()

    def snapshot(
        self,
    ) -> dict[str, Any]:

        with self._lock:

            return {
                "subscriber_events":
                    {
                        key:
                            len(
                                value
                            )
                        for key, value
                        in self._subscribers.items()
                    },

                "history":
                    [
                        {
                            "name":
                                event.name,

                            "timestamp":
                                event.timestamp,

                            "task_id":
                                event.task_id,

                            "payload":
                                dict(
                                    event.payload
                                ),
                        }
                        for event
                        in self._history[
                            -20:
                        ]
                    ],
            }