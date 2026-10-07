from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional


class PersistentMemoryStore:

    """
    SQLite-backed persistent memory store for JARVIS X.

    This is the persistence layer for ContextMemory.

    Responsibilities:
        - persist explicit memories across application restarts
        - retrieve/update/delete memories
        - keep category/key uniqueness
        - store structured Python values as JSON
        - expose compact context for the reasoning layer

    It does NOT decide what should be remembered. That policy belongs
    to the higher-level memory manager.
    """

    SCHEMA_VERSION = 1

    def __init__(
        self,
        db_path: str | Path = "database/jarvis_memory.db",
    ):

        self.db_path = Path(
            db_path
        )

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = threading.RLock()

        self._initialize()

    ############################################################
    # INITIALIZATION
    ############################################################

    def _connect(
        self,
    ) -> sqlite3.Connection:

        connection = sqlite3.connect(
            str(
                self.db_path
            ),

            timeout=10.0,

            check_same_thread=False,
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def _initialize(
        self,
    ):

        with self._lock:

            connection = self._connect()

            try:

                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_items (
                        memory_id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        memory_key TEXT NOT NULL,
                        value_json TEXT NOT NULL,
                        importance REAL NOT NULL DEFAULT 0.5,
                        source TEXT DEFAULT '',
                        metadata_json TEXT NOT NULL DEFAULT '{}',
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        access_count INTEGER NOT NULL DEFAULT 0,
                        last_accessed_at REAL NOT NULL DEFAULT 0.0
                    )
                    """
                )

                connection.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                    idx_memory_category_key
                    ON memory_items(category, memory_key)
                    """
                )

                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_memory_category
                    ON memory_items(category)
                    """
                )

                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_memory_importance
                    ON memory_items(importance DESC)
                    """
                )

                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )

                connection.execute(
                    """
                    INSERT OR IGNORE INTO memory_meta(
                        key,
                        value
                    )
                    VALUES(
                        'schema_version',
                        ?
                    )
                    """,
                    (
                        str(
                            self.SCHEMA_VERSION
                        ),
                    ),
                )

                connection.commit()

            finally:

                connection.close()

    ############################################################
    # WRITE / UPDATE
    ############################################################

    def upsert(
        self,
        *,
        memory_id: Optional[str] = None,
        category: str,
        key: str,
        value: Any,
        importance: float = 0.5,
        source: str = "",
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> dict[str, Any]:

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

        now = time.time()

        if not memory_id:

            memory_id = str(
                uuid.uuid4()
            )

        value_json = json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )

        metadata_json = json.dumps(
            dict(
                metadata
                or
                {}
            ),
            ensure_ascii=False,
            default=str,
        )

        with self._lock:

            connection = self._connect()

            try:

                existing = connection.execute(
                    """
                    SELECT memory_id
                    FROM memory_items
                    WHERE category = ?
                      AND memory_key = ?
                    """,
                    (
                        category,
                        key,
                    ),
                ).fetchone()

                if existing is not None:

                    memory_id = (
                        existing[
                            "memory_id"
                        ]
                    )

                    connection.execute(
                        """
                        UPDATE memory_items
                        SET value_json = ?,
                            importance = ?,
                            source = ?,
                            metadata_json = ?,
                            updated_at = ?
                        WHERE memory_id = ?
                        """,
                        (
                            value_json,
                            importance,
                            str(
                                source
                                or
                                ""
                            ),
                            metadata_json,
                            now,
                            memory_id,
                        ),
                    )

                else:

                    connection.execute(
                        """
                        INSERT INTO memory_items (
                            memory_id,
                            category,
                            memory_key,
                            value_json,
                            importance,
                            source,
                            metadata_json,
                            created_at,
                            updated_at,
                            access_count,
                            last_accessed_at
                        )
                        VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0.0
                        )
                        """,
                        (
                            memory_id,
                            category,
                            key,
                            value_json,
                            importance,
                            str(
                                source
                                or
                                ""
                            ),
                            metadata_json,
                            now,
                            now,
                        ),
                    )

                connection.commit()

                row = connection.execute(
                    """
                    SELECT *
                    FROM memory_items
                    WHERE memory_id = ?
                    """,
                    (
                        memory_id,
                    ),
                ).fetchone()

                return self._row_to_dict(
                    row
                )

            finally:

                connection.close()

    ############################################################
    # READ
    ############################################################

    def get(
        self,
        category: str,
        key: str,
    ) -> Optional[dict[str, Any]]:

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

        with self._lock:

            connection = self._connect()

            try:

                row = connection.execute(
                    """
                    SELECT *
                    FROM memory_items
                    WHERE category = ?
                      AND memory_key = ?
                    """,
                    (
                        category,
                        key,
                    ),
                ).fetchone()

                if row is None:

                    return None

                self._touch_row(
                    connection,
                    row[
                        "memory_id"
                    ],
                )

                connection.commit()

                refreshed = connection.execute(
                    """
                    SELECT *
                    FROM memory_items
                    WHERE memory_id = ?
                    """,
                    (
                        row[
                            "memory_id"
                        ],
                    ),
                ).fetchone()

                return self._row_to_dict(
                    refreshed
                )

            finally:

                connection.close()

    def list_category(
        self,
        category: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:

        category = str(
            category
            or
            ""
        ).strip().lower()

        limit = max(
            0,
            int(
                limit
            ),
        )

        if limit == 0:
            return []

        with self._lock:

            connection = self._connect()

            try:

                rows = connection.execute(
                    """
                    SELECT *
                    FROM memory_items
                    WHERE category = ?
                    ORDER BY
                        importance DESC,
                        updated_at DESC
                    LIMIT ?
                    """,
                    (
                        category,
                        limit,
                    ),
                ).fetchall()

                ids = [
                    row[
                        "memory_id"
                    ]
                    for row in rows
                ]

                for memory_id in ids:

                    self._touch_row(
                        connection,
                        memory_id,
                    )

                connection.commit()

                return [
                    self._row_to_dict(
                        row
                    )
                    for row in rows
                ]

            finally:

                connection.close()

    ############################################################
    # SEARCH
    ############################################################

    def search(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:

        query = str(
            query
            or
            ""
        ).strip().lower()

        if not query:
            return []

        limit = max(
            1,
            int(
                limit
            ),
        )

        category_value = (
            str(
                category
                or
                ""
            ).strip().lower()
        )

        like_query = (
            f"%{query}%"
        )

        with self._lock:

            connection = self._connect()

            try:

                if category_value:

                    rows = connection.execute(
                        """
                        SELECT *
                        FROM memory_items
                        WHERE category = ?
                          AND (
                              LOWER(memory_key) LIKE ?
                              OR LOWER(value_json) LIKE ?
                              OR LOWER(source) LIKE ?
                              OR LOWER(metadata_json) LIKE ?
                          )
                        ORDER BY
                            importance DESC,
                            updated_at DESC
                        LIMIT ?
                        """,
                        (
                            category_value,
                            like_query,
                            like_query,
                            like_query,
                            like_query,
                            limit,
                        ),
                    ).fetchall()

                else:

                    rows = connection.execute(
                        """
                        SELECT *
                        FROM memory_items
                        WHERE
                            LOWER(category) LIKE ?
                            OR LOWER(memory_key) LIKE ?
                            OR LOWER(value_json) LIKE ?
                            OR LOWER(source) LIKE ?
                            OR LOWER(metadata_json) LIKE ?
                        ORDER BY
                            importance DESC,
                            updated_at DESC
                        LIMIT ?
                        """,
                        (
                            like_query,
                            like_query,
                            like_query,
                            like_query,
                            like_query,
                            limit,
                        ),
                    ).fetchall()

                for row in rows:

                    self._touch_row(
                        connection,
                        row[
                            "memory_id"
                        ],
                    )

                connection.commit()

                return [
                    self._row_to_dict(
                        row
                    )
                    for row in rows
                ]

            finally:

                connection.close()

    ############################################################
    # DELETE
    ############################################################

    def delete(
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

        with self._lock:

            connection = self._connect()

            try:

                cursor = connection.execute(
                    """
                    DELETE FROM memory_items
                    WHERE category = ?
                      AND memory_key = ?
                    """,
                    (
                        category,
                        key,
                    ),
                )

                connection.commit()

                return (
                    cursor.rowcount
                    >
                    0
                )

            finally:

                connection.close()

    def clear(
        self,
        category: Optional[str] = None,
    ) -> int:

        with self._lock:

            connection = self._connect()

            try:

                if category:

                    cursor = connection.execute(
                        """
                        DELETE FROM memory_items
                        WHERE category = ?
                        """,
                        (
                            str(
                                category
                            ).strip().lower(),
                        ),
                    )

                else:

                    cursor = connection.execute(
                        """
                        DELETE FROM memory_items
                        """
                    )

                connection.commit()

                return int(
                    cursor.rowcount
                )

            finally:

                connection.close()

    ############################################################
    # COUNT / SNAPSHOT
    ############################################################

    def count(
        self,
    ) -> int:

        with self._lock:

            connection = self._connect()

            try:

                row = connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM memory_items
                    """
                ).fetchone()

                return int(
                    row[
                        "count"
                    ]
                )

            finally:

                connection.close()

    def snapshot(
        self,
        limit: int = 100,
    ) -> dict[str, Any]:

        limit = max(
            1,
            int(
                limit
            ),
        )

        with self._lock:

            connection = self._connect()

            try:

                rows = connection.execute(
                    """
                    SELECT *
                    FROM memory_items
                    ORDER BY
                        importance DESC,
                        updated_at DESC
                    LIMIT ?
                    """,
                    (
                        limit,
                    ),
                ).fetchall()

                return {
                    "db_path":
                        str(
                            self.db_path
                        ),

                    "count":
                        self.count(),

                    "items":
                        [
                            self._row_to_dict(
                                row
                            )
                            for row in rows
                        ],
                }

            finally:

                connection.close()

    ############################################################
    # HELPERS
    ############################################################

    @staticmethod
    def _touch_row(
        connection,
        memory_id: str,
    ):

        connection.execute(
            """
            UPDATE memory_items
            SET access_count = access_count + 1,
                last_accessed_at = ?
            WHERE memory_id = ?
            """,
            (
                time.time(),
                memory_id,
            ),
        )

    @staticmethod
    def _row_to_dict(
        row,
    ) -> dict[str, Any]:

        if row is None:
            return {}

        try:

            value = json.loads(
                row[
                    "value_json"
                ]
            )

        except Exception:

            value = (
                row[
                    "value_json"
                ]
            )

        try:

            metadata = json.loads(
                row[
                    "metadata_json"
                ]
            )

        except Exception:

            metadata = {}

        return {
            "memory_id":
                row[
                    "memory_id"
                ],

            "category":
                row[
                    "category"
                ],

            "key":
                row[
                    "memory_key"
                ],

            "value":
                value,

            "importance":
                float(
                    row[
                        "importance"
                    ]
                ),

            "source":
                row[
                    "source"
                ],

            "metadata":
                metadata,

            "created_at":
                row[
                    "created_at"
                ],

            "updated_at":
                row[
                    "updated_at"
                ],

            "access_count":
                int(
                    row[
                        "access_count"
                    ]
                ),

            "last_accessed_at":
                row[
                    "last_accessed_at"
                ],
        }