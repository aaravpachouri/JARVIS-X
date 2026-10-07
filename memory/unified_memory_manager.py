from __future__ import annotations

from typing import Any, Optional

from memory.context_memory import ContextMemory
from database.persistent_memory_store import PersistentMemoryStore
from memory.memory_retrieval_ranker import MemoryRetrievalRanker
from memory.conversation_context import ConversationContext
from memory.memory_context_injector import MemoryContextInjector
from memory.memory_policy import MemoryPolicy


class UnifiedMemoryManager:

    """
    Unified facade for JARVIS X memory.

    Layers:
        ContextMemory
        PersistentMemoryStore
        MemoryRetrievalRanker
        ConversationContext
        MemoryContextInjector
        MemoryPolicy

    The manager owns the policy decision and delegates persistence,
    retrieval, conversation context, and injection to specialized
    components.
    """

    def __init__(
        self,
        *,
        context_memory: Optional[ContextMemory] = None,
        persistent_store: Optional[
            PersistentMemoryStore
        ] = None,
        ranker: Optional[
            MemoryRetrievalRanker
        ] = None,
        conversation: Optional[
            ConversationContext
        ] = None,
        policy: Optional[
            MemoryPolicy
        ] = None,
    ):

        self.context = (
            context_memory
            or
            ContextMemory()
        )

        self.store = (
            persistent_store
            or
            PersistentMemoryStore()
        )

        self.ranker = (
            ranker
            or
            MemoryRetrievalRanker()
        )

        self.conversation = (
            conversation
            or
            ConversationContext()
        )

        self.policy = (
            policy
            or
            MemoryPolicy()
        )

        self.injector = (
            MemoryContextInjector(
                retrieval_ranker=self.ranker,
                persistent_store=self.store,
                context_memory=self.context,
                conversation_context=self.conversation,
            )
        )

    ############################################################
    # CONVERSATION
    ############################################################

    def add_user(
        self,
        content: str,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ):

        return self.conversation.add_user(
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

        return self.conversation.add_assistant(
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

        return self.conversation.add_system(
            content,
            metadata=metadata,
        )

    def set_topic(
        self,
        topic: str,
    ):

        self.conversation.set_topic(
            topic
        )

    ############################################################
    # REMEMBER
    ############################################################

    def remember(
        self,
        category: str,
        key: str,
        value: Any,
        *,
        explicit: bool = False,
        importance: Optional[
            float
        ] = None,
        source: str = "",
        metadata: Optional[
            dict[str, Any]
        ] = None,
        source_text: str = "",
    ) -> dict[str, Any]:

        decision = (
            self.policy.evaluate(
                category=category,
                key=key,
                value=value,
                explicit=explicit,
                importance=importance,
                source_text=source_text,
            )
        )

        if not decision.get(
            "allowed",
            False,
        ):

            return {
                "stored":
                    False,

                "reason":
                    decision.get(
                        "reason",
                        "Memory policy rejected the memory.",
                    ),
            }

        final_importance = decision.get(
            "importance",
            0.5,
        )

        runtime_item = (
            self.context.remember(
                category,
                key,
                value,
                importance=final_importance,
                source=source,
                metadata=metadata,
            )
        )

        persistent_item = (
            self.store.upsert(
                category=category,
                key=key,
                value=value,
                importance=final_importance,
                source=source,
                metadata=metadata,
            )
        )

        return {
            "stored":
                True,

            "runtime":
                runtime_item.to_dict(),

            "persistent":
                persistent_item,

            "importance":
                final_importance,

            "reason":
                decision.get(
                    "reason",
                    "",
                ),
        }

    ############################################################
    # RECALL
    ############################################################

    def recall(
        self,
        category: str,
        key: str,
        default: Any = None,
    ) -> Any:

        persistent = (
            self.store.get(
                category,
                key,
            )
        )

        if persistent is not None:

            return persistent.get(
                "value",
                default,
            )

        return self.context.recall(
            category,
            key,
            default,
        )

    ############################################################
    # SEARCH
    ############################################################

    def search(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:

        memories = []

        try:

            memories.extend(
                self.store.search(
                    query,
                    category=category,
                    limit=max(
                        20,
                        limit * 3,
                    ),
                )
            )

        except Exception:
            pass

        try:

            memories.extend(
                item.to_dict()
                for item
                in self.context.search(
                    query,
                    category=category,
                    limit=max(
                        10,
                        limit * 2,
                    ),
                )
            )

        except Exception:
            pass

        unique = {}

        for item in memories:

            key = (
                item.get(
                    "category",
                    "",
                ),
                item.get(
                    "key",
                    "",
                ),
            )

            unique[
                key
            ] = item

        ranked = (
            self.ranker.rank(
                query,
                unique.values(),
                category=category,
                limit=limit,
            )
        )

        return [
            item[
                "memory"
            ]
            for item in ranked
        ]

    ############################################################
    # INJECT
    ############################################################

    def build_reasoning_context(
        self,
        query: str,
        *,
        memory_limit: int = 8,
        conversation_limit: int = 10,
        category: Optional[str] = None,
    ) -> dict[str, Any]:

        return self.injector.build(
            query,
            memory_limit=memory_limit,
            conversation_limit=conversation_limit,
            category=category,
        )

    def format_reasoning_context(
        self,
        query: str,
    ) -> str:

        context = (
            self.build_reasoning_context(
                query
            )
        )

        return (
            self.injector.format_for_model(
                context
            )
        )

    ############################################################
    # FORGET
    ############################################################

    def forget(
        self,
        category: str,
        key: str,
    ) -> dict[str, Any]:

        persistent_deleted = (
            self.store.delete(
                category,
                key,
            )
        )

        runtime_deleted = (
            self.context.forget(
                category,
                key,
            )
        )

        return {
            "deleted":
                (
                    persistent_deleted
                    or
                    runtime_deleted
                ),

            "persistent":
                persistent_deleted,

            "runtime":
                runtime_deleted,
        }

    ############################################################
    # CONTEXT
    ############################################################

    def compact_context(
        self,
        query: str = "",
    ) -> dict[str, Any]:

        if query:

            return self.build_reasoning_context(
                query
            )

        return {
            "conversation":
                self.conversation.compact_context(),

            "memory":
                self.context.compact_context(),

            "persistent":
                self.store.snapshot(
                    limit=20
                ),
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "conversation":
                self.conversation.snapshot(),

            "context_memory":
                self.context.snapshot(),

            "persistent_memory":
                self.store.snapshot(),

            "policy":
                {
                    "minimum_importance":
                        self.policy.minimum_importance,
                },
        }

    ############################################################
    # CLEAR
    ############################################################

    def clear_session(
        self,
    ):

        self.conversation.clear()

        self.context.clear()