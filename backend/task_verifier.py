from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class VerificationResult:
    verified: bool = False
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskVerifier:
    name = "verifier"

    def verify(
        self,
        step,
        result,
        context: Optional[dict[str, Any]] = None,
    ) -> VerificationResult:

        return VerificationResult(
            verified=False,
            reason=(
                f"Verifier '{self.name}' "
                "does not implement verification."
            ),
        )


class FunctionVerifier(TaskVerifier):

    def __init__(
        self,
        name: str,
        handler: Callable[[Any, Any, dict[str, Any]], Any],
    ):

        self.name = str(name or "verifier").strip()
        self.handler = handler

    def verify(
        self,
        step,
        result,
        context: Optional[dict[str, Any]] = None,
    ) -> VerificationResult:

        try:

            output = self.handler(
                step,
                result,
                dict(context or {}),
            )

            if isinstance(output, VerificationResult):
                return output

            if isinstance(output, bool):
                return VerificationResult(
                    verified=output,
                    reason=f"Custom verifier returned {output}.",
                )

            return VerificationResult(
                verified=True,
                reason=str(
                    output or
                    "Custom verifier accepted the result."
                ),
            )

        except Exception as exc:

            return VerificationResult(
                verified=False,
                reason=str(exc),
                metadata={"exception": str(exc)},
            )


class TaskVerificationEngine:

    """
    Central verification layer.

    An executor can explicitly declare its own result verified
    with result.metadata["verified"] = True. Otherwise a
    dedicated verifier registered for that executor must verify it.
    """

    def __init__(self):
        self.verifiers: dict[str, TaskVerifier] = {}

    def register(
        self,
        executor_name: str,
        verifier: TaskVerifier,
    ) -> TaskVerifier:

        name = str(executor_name or "").strip().upper()

        if not name:
            raise ValueError(
                "Executor name cannot be empty."
            )

        if not isinstance(verifier, TaskVerifier):
            raise TypeError(
                "register() requires a TaskVerifier."
            )

        self.verifiers[name] = verifier

        print(
            "[Verification] "
            f"Registered verifier for {name}"
        )

        return verifier

    def get(
        self,
        executor_name: str,
    ) -> Optional[TaskVerifier]:

        return self.verifiers.get(
            str(executor_name or "").strip().upper()
        )

    def verify(
        self,
        step,
        result,
        context: Optional[dict[str, Any]] = None,
    ) -> VerificationResult:

        if result is None:
            return VerificationResult(
                verified=False,
                reason="Executor returned no result.",
            )

        if not bool(
            getattr(result, "success", False)
        ):
            return VerificationResult(
                verified=False,
                reason=str(
                    getattr(
                        result,
                        "error",
                        "Executor reported failure.",
                    )
                    or
                    "Executor reported failure."
                ),
            )

        metadata = getattr(result, "metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        if metadata.get("verified") is True:
            return VerificationResult(
                verified=True,
                reason=str(
                    getattr(result, "verification", "")
                    or
                    "Executor explicitly verified the result."
                ),
                metadata={
                    "source": "executor",
                    "executor": getattr(
                        result,
                        "executor",
                        "",
                    ),
                },
            )

        executor_name = str(
            getattr(result, "executor", "")
            or
            getattr(step, "executor", "")
            or
            ""
        ).strip().upper()

        verifier = self.get(executor_name)

        if verifier is not None:
            return verifier.verify(
                step,
                result,
                context=context,
            )

        return VerificationResult(
            verified=False,
            reason=(
                "Executor succeeded, but no independent "
                "verification source is registered."
            ),
            metadata={"executor": executor_name},
        )

    def names(self) -> list[str]:
        return list(self.verifiers.keys())

    def __repr__(self):
        return (
            "<TaskVerificationEngine "
            f"verifiers={self.names()!r}>"
        )