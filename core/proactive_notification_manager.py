from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ProactiveNotification:

    notification_id: str

    title: str

    message: str

    priority: int = 50

    opportunity_id: str = ""

    created_at: float = field(
        default_factory=time.time
    )

    expires_at: Optional[float] = None

    status: str = "PENDING"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "notification_id":
                self.notification_id,

            "title":
                self.title,

            "message":
                self.message,

            "priority":
                self.priority,

            "opportunity_id":
                self.opportunity_id,

            "created_at":
                self.created_at,

            "expires_at":
                self.expires_at,

            "status":
                self.status,

            "metadata":
                dict(
                    self.metadata
                ),
        }


class ProactiveNotificationManager:

    """
    Delivery-neutral notification layer for proactive intelligence.

    It creates notification objects from approved/safe proactive
    opportunities. It does not directly display UI or execute tasks.
    A future UI/voice adapter can consume these notifications.
    """

    MAX_NOTIFICATIONS = 100

    def __init__(self):

        self.notifications: dict[
            str,
            ProactiveNotification
        ] = {}

    ############################################################
    # CREATE
    ############################################################

    def create(
        self,
        title: str,
        message: str,
        *,
        priority: int = 50,
        opportunity_id: str = "",
        expires_at: Optional[float] = None,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> ProactiveNotification:

        item = ProactiveNotification(
            notification_id=str(
                uuid.uuid4()
            ),

            title=str(
                title
                or
                ""
            ).strip(),

            message=str(
                message
                or
                ""
            ).strip(),

            priority=max(
                0,
                min(
                    100,
                    int(
                        priority
                    ),
                ),
            ),

            opportunity_id=str(
                opportunity_id
                or
                ""
            ).strip(),

            expires_at=expires_at,

            metadata=dict(
                metadata
                or
                {}
            ),
        )

        self.notifications[
            item.notification_id
        ] = item

        self._trim()

        return item

    ############################################################
    # FROM OPPORTUNITY
    ############################################################

    def from_opportunity(
        self,
        opportunity,
    ) -> Optional[ProactiveNotification]:

        data = self._normalize(
            opportunity
        )

        if not data:
            return None

        return self.create(
            data.get(
                "title",
                "JARVIS suggestion",
            ),

            data.get(
                "reason",
                data.get(
                    "suggested_action",
                    "",
                )
            ),

            priority=int(
                data.get(
                    "priority",
                    50,
                )
                or
                50
            ),

            opportunity_id=str(
                data.get(
                    "opportunity_id",
                    "",
                )
                or
                ""
            ),

            expires_at=data.get(
                "expires_at"
            ),

            metadata={
                "suggested_action":
                    data.get(
                        "suggested_action",
                        "",
                    ),

                "trigger_type":
                    data.get(
                        "trigger_type",
                        "",
                    ),
            },
        )

    ############################################################
    # QUEUE
    ############################################################

    def pending(
        self,
        limit: int = 20,
    ) -> list[ProactiveNotification]:

        now = time.time()

        result = []

        for item in self.notifications.values():

            if item.status != "PENDING":
                continue

            if (
                item.expires_at is not None
                and
                now >= item.expires_at
            ):

                item.status = "EXPIRED"

                continue

            result.append(
                item
            )

        result.sort(
            key=lambda item: (
                item.priority,
                item.created_at,
            ),
            reverse=True,
        )

        return result[
            :max(
                0,
                int(
                    limit
                ),
            )
        ]

    ############################################################
    # DELIVERY STATE
    ############################################################

    def mark_delivered(
        self,
        notification_id: str,
    ) -> bool:

        item = self.notifications.get(
            str(
                notification_id
                or
                ""
            ).strip()
        )

        if item is None:
            return False

        item.status = "DELIVERED"

        return True

    def dismiss(
        self,
        notification_id: str,
    ) -> bool:

        item = self.notifications.get(
            str(
                notification_id
                or
                ""
            ).strip()
        )

        if item is None:
            return False

        item.status = "DISMISSED"

        return True

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "pending":
                [
                    item.to_dict()
                    for item
                    in self.pending(
                        100
                    )
                ]
        }

    ############################################################
    # INTERNAL
    ############################################################

    @staticmethod
    def _normalize(
        item,
    ) -> dict[str, Any]:

        if isinstance(
            item,
            dict,
        ):

            return dict(
                item
            )

        if hasattr(
            item,
            "to_dict",
        ):

            try:

                data = item.to_dict()

                if isinstance(
                    data,
                    dict,
                ):

                    return data

            except Exception:
                pass

        return {}

    def _trim(
        self,
    ):

        if len(
            self.notifications
        ) <= self.MAX_NOTIFICATIONS:

            return

        removable = [
            item
            for item
            in self.notifications.values()
            if item.status
            in {
                "DELIVERED",
                "DISMISSED",
                "EXPIRED",
            }
        ]

        removable.sort(
            key=lambda item:
                item.created_at
        )

        count = (
            len(
                self.notifications
            )
            -
            self.MAX_NOTIFICATIONS
        )

        for item in removable[
            :count
        ]:

            self.notifications.pop(
                item.notification_id,
                None,
            )