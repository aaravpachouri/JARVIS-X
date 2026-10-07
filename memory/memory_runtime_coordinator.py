from __future__ import annotations

from typing import Any, Optional

from memory.unified_memory_manager import UnifiedMemoryManager
from memory.memory_lifecycle import MemoryLifecycleManager
from memory.reasoning_memory_bridge import ReasoningMemoryBridge


class MemoryRuntimeCoordinator:

    """
    Final runtime facade for Phase 8.8 memory.

    Combines:
        - unified memory management
        - lifecycle/decay
        - reasoning-memory bridge

    Existing AI reasoning remains the authority for current
    conversation interpretation. This coordinator only supplies
    persistent memory/context capabilities.
    """

    def __init__(
        self,
        manager: Optional[
            UnifiedMemoryManager
        ] = None,
        lifecycle: Optional[
            MemoryLifecycleManager
        ] = None,
    ):

        self.memory = (
            manager
            or
            UnifiedMemoryManager()
        )

        self.lifecycle = (
            lifecycle
            or
            MemoryLifecycleManager()
        )

        self.reasoning = (
            ReasoningMemoryBridge(
                self.memory
            )
        )

    ############################################################
    # RECORD
    ############################################################

    def record_user(
        self,
        command: str,
        *,
        topic: str = "",
    ):

        self.reasoning.record_user_command(
            command,
            topic=topic,
        )

    def record_assistant(
        self,
        response: str,
    ):

        self.reasoning.record_assistant_response(
            response
        )

    ############################################################
    # MEMORY
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
        source_text: str = "",
        source: str = "",
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ):

        return self.memory.remember(
            category,
            key,
            value,
            explicit=explicit,
            importance=importance,
            source=source,
            source_text=source_text,
            metadata=metadata,
        )

    def recall(
        self,
        category: str,
        key: str,
        default: Any = None,
    ):

        return self.memory.recall(
            category,
            key,
            default,
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        category: Optional[str] = None,
    ):

        return self.memory.search(
            query,
            limit=limit,
            category=category,
        )

    def forget(
        self,
        category: str,
        key: str,
    ):

        return self.memory.forget(
            category,
            key,
        )

    ############################################################
    # REASONING CONTEXT
    ############################################################

    def reasoning_context(
        self,
        query: str,
        *,
        memory_limit: int = 8,
        conversation_limit: int = 10,
    ):

        return self.memory.build_reasoning_context(
            query,
            memory_limit=memory_limit,
            conversation_limit=conversation_limit,
        )

    def reasoning_text(
        self,
        query: str,
    ) -> str:

        return self.memory.format_reasoning_context(
            query
        )

    ############################################################
    # LIFECYCLE
    ############################################################

    def memory_health(
        self,
    ) -> dict[str, Any]:

        snapshot = (
            self.memory.store.snapshot(
                limit=200
            )
        )

        items = snapshot.get(
            "items",
            [],
        )

        statuses = {
            "STRONG":
                0,

            "ACTIVE":
                0,

            "WEAK":
                0,

            "STALE":
                0,
        }

        for item in items:

            status = (
                self.lifecycle.classify(
                    item
                ).get(
                    "status",
                    "STALE",
                )
            )

            statuses[
                status
            ] = statuses.get(
                status,
                0,
            ) + 1

        return {
            "count":
                len(
                    items
                ),

            "statuses":
                statuses,
        }

    def cleanup_stale(
        self,
        limit: int = 50,
    ):

        return self.lifecycle.prune_store(
            self.memory.store,
            limit=limit,
        )

    ############################################################
    # CONTEXT
    ############################################################

    def compact_context(
        self,
        query: str = "",
    ):

        if query:

            return self.reasoning_context(
                query
            )

        return self.memory.compact_context()

    def snapshot(
        self,
    ):

        return {
            "memory":
                self.memory.snapshot(),

            "health":
                self.memory_health(),
        }