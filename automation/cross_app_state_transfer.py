from __future__ import annotations

import time
from copy import deepcopy
from typing import Any, Optional


class CrossAppStateTransfer:
    """
    Transfers explicit workflow state between application stages.

    Only state deliberately published by the workflow is transferred.
    This avoids leaking arbitrary UI state from one application into
    another application.

    Typical examples:
        downloaded_file -> File Explorer
        selected_text   -> Word
        source_url      -> browser/another app
        spreadsheet     -> reporting stage
    """

    MAX_ARTIFACTS = 100

    def __init__(self):

        self._artifacts: dict[
            str,
            dict[str, Any]
        ] = {}

        self._variables: dict[
            str,
            Any
        ] = {}

    ############################################################
    # PUBLISH ARTIFACT
    ############################################################

    def publish_artifact(
        self,
        name: str,
        value: Any,
        source_application: str = "",
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> dict[str, Any]:

        key = str(
            name
            or
            ""
        ).strip()

        if not key:

            return {
                "success":
                    False,

                "error":
                    "Artifact name cannot be empty.",
            }

        self._artifacts[
            key
        ] = {
            "value":
                deepcopy(
                    value
                ),

            "source_application":
                str(
                    source_application
                    or
                    ""
                ).strip(),

            "metadata":
                dict(
                    metadata
                    or
                    {}
                ),

            "timestamp":
                time.monotonic(),
        }

        if len(
            self._artifacts
        ) > self.MAX_ARTIFACTS:

            oldest = min(
                self._artifacts,
                key=lambda item:
                    self._artifacts[
                        item
                    ].get(
                        "timestamp",
                        0.0,
                    ),
            )

            del self._artifacts[
                oldest
            ]

        return {
            "success":
                True,

            "name":
                key,

            "value":
                deepcopy(
                    value
                ),
        }

    ############################################################
    # READ ARTIFACT
    ############################################################

    def get_artifact(
        self,
        name: str,
        target_application: str = "",
    ) -> Optional[Any]:

        key = str(
            name
            or
            ""
        ).strip()

        entry = self._artifacts.get(
            key
        )

        if entry is None:
            return None

        ########################################################
        # If an explicit target application was provided, only
        # return the artifact as transferable state. The caller
        # remains responsible for deciding whether it is valid
        # for the target application's task.
        ########################################################

        return deepcopy(
            entry.get(
                "value"
            )
        )

    def artifact_metadata(
        self,
        name: str,
    ) -> dict[str, Any]:

        entry = self._artifacts.get(
            str(
                name
                or
                ""
            ).strip()
        )

        if entry is None:
            return {}

        return deepcopy(
            entry
        )

    ############################################################
    # VARIABLES
    ############################################################

    def publish_variable(
        self,
        name: str,
        value: Any,
    ) -> bool:

        key = str(
            name
            or
            ""
        ).strip()

        if not key:
            return False

        self._variables[
            key
        ] = deepcopy(
            value
        )

        return True

    def get_variable(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        key = str(
            name
            or
            ""
        ).strip()

        return deepcopy(
            self._variables.get(
                key,
                default,
            )
        )

    ############################################################
    # IMPORT / EXPORT
    ############################################################

    def export_to_workflow(
        self,
        workflow,
    ):

        if workflow is None:
            return

        for name, entry in self._artifacts.items():

            workflow.add_artifact(
                name,
                {
                    "value":
                        deepcopy(
                            entry.get(
                                "value"
                            )
                        ),

                    "source_application":
                        entry.get(
                            "source_application",
                            "",
                        ),

                    "metadata":
                        deepcopy(
                            entry.get(
                                "metadata",
                                {}
                            )
                        ),
                },
            )

        for name, value in self._variables.items():

            workflow.set_variable(
                name,
                deepcopy(
                    value
                ),
            )

    def import_from_workflow(
        self,
        workflow,
    ):

        if workflow is None:
            return

        artifacts = getattr(
            workflow,
            "artifacts",
            {},
        )

        if isinstance(
            artifacts,
            dict,
        ):

            for name, value in artifacts.items():

                self.publish_artifact(
                    name,
                    value,
                    metadata={
                        "imported":
                            True
                    },
                )

        variables = getattr(
            workflow,
            "variables",
            {},
        )

        if isinstance(
            variables,
            dict,
        ):

            for name, value in variables.items():

                self.publish_variable(
                    name,
                    value,
                )

    ############################################################
    # CONTEXT
    ############################################################

    def compact_context(
        self,
    ) -> dict[str, Any]:

        return {
            "artifact_names":
                list(
                    self._artifacts.keys()
                ),

            "variables":
                deepcopy(
                    self._variables
                ),
        }

    def clear(
        self,
    ):

        self._artifacts.clear()

        self._variables.clear()