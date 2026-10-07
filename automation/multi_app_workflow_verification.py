from __future__ import annotations

from typing import Any, Callable, Optional


class MultiAppWorkflowVerification:

    """
    Verification layer for multi-application workflows.

    It verifies each workflow stage using an injected verifier and
    supports deterministic application-state checks before a stage
    is accepted as complete.

    It does not execute computer actions.
    """

    def __init__(
        self,
        verifier: Optional[Callable[..., Any]] = None,
    ):

        self.verifier = verifier

        self.results: list[
            dict[str, Any]
        ] = []

    def set_verifier(
        self,
        verifier: Callable[..., Any],
    ):

        self.verifier = verifier

    ############################################################
    # VERIFY STAGE
    ############################################################

    def verify_stage(
        self,
        workflow,
        stage,
        *,
        observed_application: str = "",
        result: Any = None,
        verifier: Optional[Callable[..., Any]] = None,
    ) -> dict[str, Any]:

        if workflow is None:

            return self._failure(
                "No workflow context supplied."
            )

        if stage is None:

            return self._failure(
                "No workflow stage supplied."
            )

        expected_application = str(
            getattr(
                stage,
                "application",
                "",
            )
            or
            ""
        ).strip()

        observed = str(
            observed_application
            or
            ""
        ).strip()

        ########################################################
        # Application verification
        ########################################################

        if (
            expected_application
            and
            observed
            and
            expected_application.lower()
            !=
            observed.lower()
        ):

            return self._record_failure(
                stage,
                (
                    "Workflow stage expected application "
                    f"'{expected_application}' but observed "
                    f"'{observed}'."
                ),
                observed_application=observed,
            )

        if (
            expected_application
            and
            not observed
        ):

            return self._record_failure(
                stage,
                (
                    "Expected application was not observable "
                    "for workflow-stage verification."
                ),
                observed_application=observed,
            )

        ########################################################
        # External semantic verifier
        ########################################################

        selected_verifier = (
            verifier
            or
            self.verifier
        )

        if selected_verifier is not None:

            try:

                verification = (
                    self._call_verifier(
                        selected_verifier,
                        workflow,
                        stage,
                        result,
                    )
                )

            except Exception as exc:

                return self._record_failure(
                    stage,
                    (
                        "Workflow verifier raised an exception: "
                        f"{exc}"
                    ),
                    observed_application=observed,
                )

            if isinstance(
                verification,
                dict,
            ):

                verified = (
                    verification.get(
                        "verified",
                        verification.get(
                            "success",
                            False,
                        ),
                    )
                )

                if verified is not True:

                    return self._record_failure(
                        stage,
                        str(
                            verification.get(
                                "reason",
                                "Stage verification failed.",
                            )
                        ),
                        observed_application=observed,
                        extra=verification,
                    )

            elif verification is not True:

                return self._record_failure(
                    stage,
                    "Stage verification returned false.",
                    observed_application=observed,
                )

        ########################################################
        # All required verification layers passed.
        ########################################################

        record = {
            "verified":
                True,

            "stage":
                getattr(
                    stage,
                    "name",
                    "",
                ),

            "application":
                expected_application,

            "observed_application":
                observed,

            "result":
                result,
        }

        self.results.append(
            record
        )

        return record

    ############################################################
    # VERIFY WORKFLOW
    ############################################################

    def verify_workflow(
        self,
        workflow,
        *,
        verifier: Optional[Callable[..., Any]] = None,
    ) -> dict[str, Any]:

        if workflow is None:

            return self._failure(
                "No workflow supplied."
            )

        stages = getattr(
            workflow,
            "stages",
            [],
        )

        failures = []

        for stage in stages:

            status = str(
                getattr(
                    stage,
                    "status",
                    "",
                )
                or
                ""
            ).upper()

            if status != "COMPLETED":

                failures.append(
                    {
                        "stage":
                            getattr(
                                stage,
                                "name",
                                "",
                            ),

                        "status":
                            status,

                        "reason":
                            (
                                getattr(
                                    stage,
                                    "error",
                                    ""
                                )
                                or
                                "Stage was not completed."
                            ),
                    }
                )

        verified = not failures

        return {
            "verified":
                verified,

            "workflow_id":
                getattr(
                    workflow,
                    "workflow_id",
                    "",
                ),

            "failures":
                failures,

            "reason":
                (
                    "All workflow stages are completed."
                    if verified
                    else
                    "One or more workflow stages are incomplete."
                ),
        }

    ############################################################
    # HELPERS
    ############################################################

    @staticmethod
    def _call_verifier(
        verifier,
        workflow,
        stage,
        result,
    ):

        try:

            return verifier(
                workflow,
                stage,
                result,
            )

        except TypeError:

            try:

                return verifier(
                    stage,
                    result,
                )

            except TypeError:

                return verifier(
                    stage
                )

    def _record_failure(
        self,
        stage,
        reason,
        *,
        observed_application: str = "",
        extra: Optional[dict[str, Any]] = None,
    ):

        record = {
            "verified":
                False,

            "stage":
                getattr(
                    stage,
                    "name",
                    "",
                ),

            "application":
                getattr(
                    stage,
                    "application",
                    "",
                ),

            "observed_application":
                observed_application,

            "reason":
                str(
                    reason
                ),
        }

        if extra is not None:
            record[
                "details"
            ] = extra

        self.results.append(
            record
        )

        return record

    @staticmethod
    def _failure(
        reason,
    ):

        return {
            "verified":
                False,

            "reason":
                str(
                    reason
                ),
        }

    def snapshot(
        self,
    ) -> list[dict[str, Any]]:

        return list(
            self.results[
                -50:
            ]
        )


def verify_multi_app_workflow(
    workflow,
    verifier=None,
) -> dict[str, Any]:

    checker = (
        MultiAppWorkflowVerification(
            verifier
        )
    )

    return checker.verify_workflow(
        workflow,
        verifier=verifier,
    )