from __future__ import annotations

from typing import Any, Optional


class MemoryContextInjector:

    """
    Builds a compact reasoning context from conversation context
    plus ranked long-term memories.

    This layer does not decide what to store. It only selects and
    formats context that is already available to the memory system.
    """

    def __init__(
        self,
        retrieval_ranker,
        persistent_store=None,
        context_memory=None,
        conversation_context=None,
    ):

        self.ranker = retrieval_ranker

        self.store = (
            persistent_store
        )

        self.context_memory = (
            context_memory
        )

        self.conversation = (
            conversation_context
        )

    ############################################################
    # BUILD
    ############################################################

    def build(
        self,
        query: str,
        *,
        memory_limit: int = 8,
        conversation_limit: int = 10,
        category: Optional[str] = None,
    ) -> dict[str, Any]:

        memories = []

        ########################################################
        # Persistent store
        ########################################################

        if self.store is not None:

            try:

                memories.extend(
                    self.store.search(
                        query,
                        category=category,
                        limit=max(
                            memory_limit * 3,
                            12,
                        ),
                    )
                )

            except Exception as exc:

                print(
                    "[MemoryInjector] "
                    f"Persistent retrieval warning: {exc}"
                )

        ########################################################
        # Runtime context memory
        ########################################################

        if self.context_memory is not None:

            try:

                memories.extend(
                    self.context_memory.search(
                        query,
                        category=category,
                        limit=max(
                            memory_limit * 2,
                            8,
                        ),
                    )
                )

            except Exception as exc:

                print(
                    "[MemoryInjector] "
                    f"Context-memory retrieval warning: {exc}"
                )

        ########################################################
        # Normalize + deduplicate
        ########################################################

        unique = {}

        for memory in memories:

            if hasattr(
                memory,
                "to_dict",
            ):

                try:

                    memory = memory.to_dict()

                except Exception:
                    continue

            if not isinstance(
                memory,
                dict,
            ):
                continue

            key = (
                memory.get(
                    "category",
                    "",
                ),
                memory.get(
                    "key",
                    "",
                ),
            )

            unique[
                key
            ] = memory

        ranked = (
            self.ranker.rank(
                query,
                unique.values(),
                category=category,
                limit=memory_limit,
            )
        )

        ########################################################
        # Conversation context
        ########################################################

        conversation = {}

        if self.conversation is not None:

            try:

                conversation = (
                    self.conversation.compact_context(
                        conversation_limit
                    )
                )

            except Exception as exc:

                print(
                    "[MemoryInjector] "
                    f"Conversation context warning: {exc}"
                )

        selected_memories = [
            item[
                "memory"
            ]
            for item in ranked
            if isinstance(
                item,
                dict,
            )
            and
            isinstance(
                item.get(
                    "memory"
                ),
                dict,
            )
        ]

        return {
            "query":
                str(
                    query
                    or
                    ""
                ),

            "memories":
                selected_memories,

            "memory_scores":
                ranked,

            "conversation":
                conversation,

            "memory_count":
                len(
                    selected_memories
                ),
        }

    ############################################################
    # MODEL TEXT
    ############################################################

    def format_for_model(
        self,
        context: dict[str, Any],
    ) -> str:

        if not isinstance(
            context,
            dict,
        ):

            return ""

        lines = []

        conversation = context.get(
            "conversation",
            {},
        )

        if conversation:

            topic = str(
                conversation.get(
                    "active_topic",
                    "",
                )
                or
                ""
            )

            if topic:

                lines.append(
                    f"Current conversation topic: {topic}"
                )

            recent = conversation.get(
                "recent_turns",
                [],
            )

            for turn in recent[-8:]:

                if not isinstance(
                    turn,
                    dict,
                ):
                    continue

                role = str(
                    turn.get(
                        "role",
                        "",
                    )
                    or
                    ""
                ).strip()

                content = str(
                    turn.get(
                        "content",
                        "",
                    )
                    or
                    ""
                ).strip()

                if content:

                    lines.append(
                        f"{role}: {content}"
                    )

        memories = context.get(
            "memories",
            [],
        )

        if memories:

            lines.append(
                "\nRelevant long-term memory:"
            )

            for memory in memories:

                category = str(
                    memory.get(
                        "category",
                        "general",
                    )
                    or
                    "general"
                )

                key = str(
                    memory.get(
                        "key",
                        "",
                    )
                    or
                    ""
                )

                value = str(
                    memory.get(
                        "value",
                        "",
                    )
                    or
                    ""
                )

                if key:

                    lines.append(
                        f"- [{category}] {key}: {value}"
                    )

        return "\n".join(
            lines
        ).strip()

    ############################################################
    # COMPACT
    ############################################################

    def compact(
        self,
        query: str,
        *,
        memory_limit: int = 8,
        conversation_limit: int = 10,
    ) -> dict[str, Any]:

        context = self.build(
            query,
            memory_limit=memory_limit,
            conversation_limit=conversation_limit,
        )

        return {
            "conversation":
                context.get(
                    "conversation",
                    {},
                ),

            "memories":
                context.get(
                    "memories",
                    [],
                ),

            "memory_count":
                context.get(
                    "memory_count",
                    0,
                ),
        }