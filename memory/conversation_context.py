from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ConversationTurn:

    turn_id: str

    role: str

    content: str

    timestamp: float = field(
        default_factory=time.time
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "turn_id":
                self.turn_id,

            "role":
                self.role,

            "content":
                self.content,

            "timestamp":
                self.timestamp,

            "metadata":
                dict(
                    self.metadata
                ),
        }


class ConversationContext:

    """
    Short/medium-horizon conversation context.

    This is intentionally separate from persistent memory.

    Persistent memory answers:
        "What should JARVIS remember across sessions?"

    ConversationContext answers:
        "What has happened in this current conversational thread?"
    """

    MAX_TURNS = 100

    def __init__(
        self,
        max_turns: int = MAX_TURNS,
    ):

        self.max_turns = max(
            1,
            int(
                max_turns
            ),
        )

        self.conversation_id = str(
            uuid.uuid4()
        )

        self.turns: list[
            ConversationTurn
        ] = []

        self.active_topic = ""

        self.topic_history: list[
            str
        ] = []

        self.last_command = ""

        self.last_response = ""

        self.variables: dict[
            str,
            Any
        ] = {}

    ############################################################
    # ADD TURN
    ############################################################

    def add_user(
        self,
        content: str,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ):

        return self.add_turn(
            "user",
            content,
            metadata=metadata,
        )

    def add_assistant(
        self,
        content: str,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ):

        return self.add_turn(
            "assistant",
            content,
            metadata=metadata,
        )

    def add_system(
        self,
        content: str,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ):

        return self.add_turn(
            "system",
            content,
            metadata=metadata,
        )

    def add_turn(
        self,
        role: str,
        content: str,
        *,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> ConversationTurn:

        turn = ConversationTurn(
            turn_id=str(
                uuid.uuid4()
            ),

            role=str(
                role
                or
                "user"
            ).strip().lower(),

            content=str(
                content
                or
                ""
            ).strip(),

            metadata=dict(
                metadata
                or
                {}
            ),
        )

        self.turns.append(
            turn
        )

        if len(
            self.turns
        ) > self.max_turns:

            del self.turns[
                :-
                self.max_turns
            ]

        if turn.role == "user":

            self.last_command = (
                turn.content
            )

        elif turn.role == "assistant":

            self.last_response = (
                turn.content
            )

        return turn

    ############################################################
    # TOPIC
    ############################################################

    def set_topic(
        self,
        topic: str,
    ):

        topic = str(
            topic
            or
            ""
        ).strip()

        if not topic:
            return

        if (
            self.active_topic
            and
            self.active_topic
            !=
            topic
        ):

            self.topic_history.append(
                self.active_topic
            )

        self.active_topic = topic

        if len(
            self.topic_history
        ) > 20:

            del self.topic_history[
                :-
                20
            ]

    ############################################################
    # VARIABLES
    ############################################################

    def set_variable(
        self,
        name: str,
        value: Any,
    ):

        key = str(
            name
            or
            ""
        ).strip()

        if key:

            self.variables[
                key
            ] = value

    def get_variable(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        return self.variables.get(
            str(
                name
                or
                ""
            ).strip(),
            default,
        )

    ############################################################
    # CONTEXT
    ############################################################

    def recent(
        self,
        limit: int = 12,
    ) -> list[ConversationTurn]:

        return list(
            self.turns[
                :max(
                    0,
                    len(
                        self.turns
                    )
                    -
                    max(
                        0,
                        int(
                            limit
                        ),
                    ),
                )
            ]
        ) if False else list(
            self.turns[
                -max(
                    1,
                    int(
                        limit
                    )
                ):
            ]
        )

    def compact_context(
        self,
        limit: int = 12,
    ) -> dict[str, Any]:

        turns = self.recent(
            limit
        )

        return {
            "conversation_id":
                self.conversation_id,

            "active_topic":
                self.active_topic,

            "topic_history":
                list(
                    self.topic_history[
                        -10:
                    ]
                ),

            "last_command":
                self.last_command,

            "last_response":
                self.last_response,

            "variables":
                dict(
                    self.variables
                ),

            "recent_turns":
                [
                    turn.to_dict()
                    for turn
                    in turns
                ],
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "conversation_id":
                self.conversation_id,

            "turn_count":
                len(
                    self.turns
                ),

            "active_topic":
                self.active_topic,

            "topic_history":
                list(
                    self.topic_history
                ),

            "turns":
                [
                    turn.to_dict()
                    for turn
                    in self.turns
                ],

            "variables":
                dict(
                    self.variables
                ),
        }

    ############################################################
    # RESET
    ############################################################

    def clear(
        self,
    ):

        self.turns.clear()

        self.active_topic = ""

        self.topic_history.clear()

        self.last_command = ""

        self.last_response = ""

        self.variables.clear()