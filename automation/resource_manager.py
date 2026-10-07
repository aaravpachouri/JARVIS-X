from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


############################################################
# RESOURCE
############################################################

@dataclass
class ManagedResource:

    name: str = ""

    resource: Any = None

    cleanup: Optional[
        Callable[[Any], None]
    ] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# RESOURCE MANAGER
############################################################

class ResourceManager:

    """
    Central lifecycle manager for runtime resources.

    Components register resources together with their cleanup
    function. The manager can then release them safely when a
    task ends, is cancelled, or the application shuts down.
    """

    def __init__(self):

        self.resources: dict[
            str,
            ManagedResource,
        ] = {}

    ########################################################
    # REGISTER
    ########################################################

    def register(
        self,
        name: str,
        resource: Any,
        cleanup: Optional[
            Callable[[Any], None]
        ] = None,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> ManagedResource:

        name = str(
            name or ""
        ).strip()

        if not name:

            raise ValueError(
                "Resource name cannot be empty."
            )

        managed = ManagedResource(
            name=name,
            resource=resource,
            cleanup=cleanup,
            metadata=dict(
                metadata or {}
            ),
        )

        self.resources[
            name
        ] = managed

        return managed

    ########################################################
    # GET
    ########################################################

    def get(
        self,
        name: str,
    ) -> Optional[
        ManagedResource
    ]:

        return self.resources.get(
            str(
                name or ""
            ).strip()
        )

    ########################################################
    # RELEASE ONE
    ########################################################

    def release(
        self,
        name: str,
    ) -> bool:

        name = str(
            name or ""
        ).strip()

        managed = self.resources.get(
            name
        )

        if managed is None:

            return False

        try:

            if callable(
                managed.cleanup
            ):

                managed.cleanup(
                    managed.resource
                )

            elif hasattr(
                managed.resource,
                "close",
            ):

                managed.resource.close()

            elif hasattr(
                managed.resource,
                "shutdown",
            ):

                managed.resource.shutdown()

        except Exception as exc:

            print(
                "[ResourceManager] "
                f"Cleanup failed for {name}:",
                exc,
            )

            return False

        finally:

            self.resources.pop(
                name,
                None,
            )

        return True

    ########################################################
    # RELEASE ALL
    ########################################################

    def release_all(
        self,
    ) -> None:

        for name in list(
            self.resources.keys()
        ):

            self.release(
                name
            )

    ########################################################
    # RESOURCE NAMES
    ########################################################

    def names(
        self,
    ) -> list[str]:

        return list(
            self.resources.keys()
        )

    ########################################################
    # SNAPSHOT
    ########################################################

    def snapshot(
        self,
    ) -> list[
        dict[str, Any]
    ]:

        return [
            {
                "name":
                    resource.name,

                "metadata":
                    dict(
                        resource.metadata
                    ),
            }

            for resource
            in self.resources.values()
        ]

    ########################################################
    # CONTEXT MANAGER
    ########################################################

    def __enter__(
        self,
    ):

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        self.release_all()

        return False

    ########################################################
    # REPRESENTATION
    ########################################################

    def __repr__(
        self,
    ):

        return (
            "<ResourceManager "
            f"resources={self.names()!r}>"
        )