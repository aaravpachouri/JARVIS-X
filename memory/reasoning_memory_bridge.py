from __future__ import annotations

from typing import Any, Optional


class ReasoningMemoryBridge:

    """
    Thin adapter between UnifiedMemoryManager and an existing
    reasoning/AI brain.

    It does not replace the brain's conversation/context logic.
    It simply supplies optional memory context when useful.

    The caller decides where the returned context is appended to the
    existing reasoning prompt/context pipeline.
    """

    def __init__(
        self,
        memory_manager,
    ):

        self.memory = (
            memory_manager
        )

    ############################################################
    # COMMAND INGESTION
    ############################################################

    def record_user_command(
        self,
        command: str,
        *,
        topic: str = "",
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ):

        self.memory.add_user(
            command,
            metadata=metadata,
        )

        if topic:

            self.memory.set_topic(
                topic
            )

    def record_assistant_response(
        self,
        response: str,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ):

        self.memory.add_assistant(
            response,
            metadata=metadata,
        )

    ############################################################
    # MEMORY REQUESTS
    ############################################################

    def remember_explicit(
        self,
        category: str,
        key: str,
        value: Any,
        *,
        source_text: str = "",
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> dict[str, Any]:

        return self.memory.remember(
            category=category,
            key=key,
            value=value,
            explicit=True,
            source_text=source_text,
            metadata=metadata,
            source="user_explicit",
        )

    ############################################################
    # REASONING CONTEXT
    ############################################################

    def get_memory_context(
        self,
        query: str,
        *,
        memory_limit: int = 8,
        conversation_limit: int = 10,
    ) -> dict[str, Any]:

        return self.memory.build_reasoning_context(
            query,
            memory_limit=memory_limit,
            conversation_limit=conversation_limit,
        )

    def get_model_memory_text(
        self,
        query: str,
    ) -> str:

        return self.memory.format_reasoning_context(
            query
        )

    ############################################################
    # SAFE COMPATIBILITY
    ############################################################

    def augment_existing_context(
        self,
        query: str,
        existing_context: Optional[
            dict[str, Any]
        ] = None,
    ) -> dict[str, Any]:

        base = dict(
            existing_context
            or
            {}
        )

        memory_context = (
            self.get_memory_context(
                query
            )
        )

        ########################################################
        # Do not overwrite the existing conversation context.
        # Add memory under a separate namespace.
        ########################################################

        base[
            "jarvis_memory"
        ] = {
            "memories":
                memory_context.get(
                    "memories",
                    [],
                ),

            "memory_count":
                memory_context.get(
                    "memory_count",
                    0,
                ),
        }

        return base