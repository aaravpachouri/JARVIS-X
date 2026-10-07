from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


############################################################
# JARVIS MEMORY — CONTEXT MEMORY
############################################################


@dataclass
class MemoryItem:

    memory_id: str

    category: str

    key: str

    value: Any

    importance: float = 0.5

    created_at: float = field(
        default_factory=time.time
    )

    updated_at: float = field(
        default_factory=time.time
    )

    source: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    access_count: int = 0

    last_accessed_at: float = 0.0

    def touch(
        self,
    ):

        self.access_count += 1

        self.last_accessed_at = (
            time.time()
        )

        self.updated_at = (
            self.last_accessed_at
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "memory_id":
                self.memory_id,

            "category":
                self.category,

            "key":
                self.key,

            "value":
                self.value,

            "importance":
                self.importance,

            "created_at":
                self.created_at,

            "updated_at":
                self.updated_at,

            "source":
                self.source,

            "metadata":
                dict(
                    self.metadata
                ),

            "access_count":
                self.access_count,

            "last_accessed_at":
                self.last_accessed_at,
        }


class ContextMemory:

    """
    Runtime memory layer for JARVIS X.

    This is the first layer of Phase 8.8.

    Responsibilities:
        - store useful context explicitly
        - separate memory by category
        - retrieve exact or relevant memories
        - track importance and access
        - expose compact context to reasoning layers

    It does not automatically invent memories and does not replace
    the existing database layer. Persistence can be connected in a
    later Phase 8.8 component.
    """

    DEFAULT_LIMIT = 20

    def __init__(
        self,
        max_items: int = 1000,
    ):

        self.max_items = max(
            1,
            int(
                max_items
            ),
        )

        self._items: dict[
            str,
            MemoryItem
        ] = {}

    ############################################################
    # WRITE
    ############################################################

    def remember(
        self,
        category: str,
        key: str,
        value: Any,
        *,
        importance: float = 0.5,
        source: str = "",
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> MemoryItem:

        category = str(
            category
            or
            "general"
        ).strip().lower()

        key = str(
            key
            or
            ""
        ).strip()

        if not key:

            raise ValueError(
                "Memory key cannot be empty."
            )

        importance = max(
            0.0,
            min(
                1.0,
                float(
                    importance
                    or
                    0.0
                ),
            ),
        )

        ########################################################
        # Update an existing logical memory when category+key
        # already exists.
        ########################################################

        existing = None

        for item in self._items.values():

            if (
                item.category
                ==
                category
                and
                item.key
                ==
                key
            ):

                existing = item

                break

        if existing is not None:

            existing.value = value

            existing.importance = importance

            existing.source = str(
                source
                or
                existing.source
                or
                ""
            ).strip()

            existing.metadata = dict(
                metadata
                or
                existing.metadata
                or
                {}
            )

            existing.updated_at = (
                time.time()
            )

            return existing

        item = MemoryItem(
            memory_id=str(
                uuid.uuid4()
            ),

            category=category,

            key=key,

            value=value,

            importance=importance,

            source=str(
                source
                or
                ""
            ).strip(),

            metadata=dict(
                metadata
                or
                {}
            ),
        )

        self._items[
            item.memory_id
        ] = item

        self._enforce_limit()

        return item

    ############################################################
    # EXACT READ
    ############################################################

    def recall(
        self,
        category: str,
        key: str,
        default: Any = None,
    ) -> Any:

        category = str(
            category
            or
            "general"
        ).strip().lower()

        key = str(
            key
            or
            ""
        ).strip()

        for item in self._items.values():

            if (
                item.category
                ==
                category
                and
                item.key
                ==
                key
            ):

                item.touch()

                return item.value

        return default

    ############################################################
    # CATEGORY
    ############################################################

    def by_category(
        self,
        category: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[MemoryItem]:

        category = str(
            category
            or
            ""
        ).strip().lower()

        items = [
            item
            for item in self._items.values()
            if item.category == category
        ]

        items.sort(
            key=lambda item: (
                item.importance,
                item.updated_at,
            ),
            reverse=True,
        )

        selected = items[
            :max(
                0,
                int(
                    limit
                ),
            )
        ]

        for item in selected:
            item.touch()

        return list(
            selected
        )

    ############################################################
    # SEARCH
    ############################################################

    def search(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[MemoryItem]:

        query = str(
            query
            or
            ""
        ).strip().lower()

        if not query:
            return []

        category_filter = (
            str(
                category
                or
                ""
            ).strip().lower()
        )

        scored = []

        for item in self._items.values():

            if (
                category_filter
                and
                item.category
                !=
                category_filter
            ):

                continue

            text = " ".join(
                [
                    item.category,
                    item.key,
                    str(
                        item.value
                    ),
                ]
            ).lower()

            score = self._match_score(
                query,
                text,
            )

            if score <= 0:
                continue

            scored.append(
                (
                    score,
                    item,
                )
            )

        scored.sort(
            key=lambda pair: (
                pair[0],
                pair[1].importance,
                pair[1].updated_at,
            ),
            reverse=True,
        )

        results = [
            item
            for _, item
            in scored[
                :max(
                    0,
                    int(
                        limit
                    ),
                )
            ]
        ]

        for item in results:
            item.touch()

        return results

    ############################################################
    # REMOVE
    ############################################################

    def forget(
        self,
        category: str,
        key: str,
    ) -> bool:

        category = str(
            category
            or
            "general"
        ).strip().lower()

        key = str(
            key
            or
            ""
        ).strip()

        memory_id = None

        for item_id, item in self._items.items():

            if (
                item.category
                ==
                category
                and
                item.key
                ==
                key
            ):

                memory_id = item_id

                break

        if memory_id is None:
            return False

        del self._items[
            memory_id
        ]

        return True

    def clear(
        self,
    ):

        self._items.clear()

    ############################################################
    # CONTEXT
    ############################################################

    def compact_context(
        self,
        limit: int = DEFAULT_LIMIT,
    ) -> dict[str, Any]:

        items = sorted(
            self._items.values(),
            key=lambda item: (
                item.importance,
                item.updated_at,
            ),
            reverse=True,
        )

        items = items[
            :max(
                0,
                int(
                    limit
                ),
            )
        ]

        return {
            "count":
                len(
                    self._items
                ),

            "memories":
                [
                    item.to_dict()
                    for item
                    in items
                ],
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "count":
                len(
                    self._items
                ),

            "items":
                [
                    item.to_dict()
                    for item
                    in self._items.values()
                ],
        }

    ############################################################
    # INTERNAL
    ############################################################

    def _enforce_limit(
        self,
    ):

        if len(
            self._items
        ) <= self.max_items:

            return

        ordered = sorted(
            self._items.values(),
            key=lambda item: (
                item.importance,
                item.last_accessed_at,
                item.updated_at,
            ),
        )

        remove_count = (
            len(
                self._items
            )
            -
            self.max_items
        )

        for item in ordered[
            :remove_count
        ]:

            self._items.pop(
                item.memory_id,
                None,
            )

    @staticmethod
    def _match_score(
        query: str,
        text: str,
    ) -> float:

        if query == text:
            return 100.0

        if query in text:
            return 90.0

        query_tokens = set(
            query.split()
        )

        text_tokens = set(
            text.split()
        )

        if not query_tokens:
            return 0.0

        overlap = (
            len(
                query_tokens
                &
                text_tokens
            )
            /
            len(
                query_tokens
            )
        )

        return (
            overlap
            *
            70.0
        )