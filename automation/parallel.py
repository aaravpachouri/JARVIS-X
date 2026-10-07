from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


############################################################
# OPERATION
############################################################

@dataclass
class ParallelOperation:

    name: str = ""

    handler: Optional[
        Callable[..., Any]
    ] = None

    dependencies: list[str] = field(
        default_factory=list
    )

    parallel_safe: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# PARALLEL GROUP
############################################################

@dataclass
class ParallelGroup:

    operations: list[
        ParallelOperation
    ] = field(
        default_factory=list
    )

    ########################################################
    # ADD
    ########################################################

    def add(
        self,
        operation: ParallelOperation,
    ) -> None:

        if not isinstance(
            operation,
            ParallelOperation,
        ):

            raise TypeError(
                "Expected ParallelOperation."
            )

        self.operations.append(
            operation
        )

    ########################################################
    # SAFE OPERATIONS
    ########################################################

    def safe_operations(
        self,
    ) -> list[ParallelOperation]:

        return [
            operation

            for operation
            in self.operations

            if operation.parallel_safe
        ]

    ########################################################
    # SERIAL OPERATIONS
    ########################################################

    def serial_operations(
        self,
    ) -> list[ParallelOperation]:

        return [
            operation

            for operation
            in self.operations

            if not operation.parallel_safe
        ]


############################################################
# PARALLEL SAFETY ANALYZER
############################################################

class ParallelSafetyAnalyzer:

    """
    Determines whether operations can safely share an execution
    window.

    Conservative by design:

        read-only / independent operations
            -> potentially parallel

        state-changing operations
            -> serial unless explicitly marked safe

        dependency-linked operations
            -> serial
    """

    def can_parallelize(
        self,
        operations: list[
            ParallelOperation
        ],
    ) -> bool:

        if len(
            operations
        ) < 2:

            return False

        ####################################################
        # Every operation must explicitly opt in.
        ####################################################

        if not all(
            operation.parallel_safe

            for operation
            in operations
        ):

            return False

        ####################################################
        # Dependency check.
        ####################################################

        names = {
            operation.name
            for operation
            in operations
        }

        for operation in operations:

            if any(
                dependency in names
                for dependency
                in operation.dependencies
            ):

                return False

        ####################################################
        # Duplicate operation names are treated as
        # potentially conflicting.
        ####################################################

        if len(
            names
        ) != len(
            operations
        ):

            return False

        return True

    ########################################################
    # GROUP
    ########################################################

    def group(
        self,
        operations: list[
            ParallelOperation
        ],
    ) -> list[
        ParallelGroup
    ]:

        if not operations:

            return []

        groups: list[
            ParallelGroup
        ] = []

        current = ParallelGroup()

        for operation in operations:

            ################################################
            # Start a new parallel-safe group when possible.
            ################################################

            candidate = (
                current.operations
                +
                [
                    operation
                ]
            )

            if self.can_parallelize(
                candidate
            ):

                current.add(
                    operation
                )

                continue

            ################################################
            # Flush previous group.
            ################################################

            if current.operations:

                groups.append(
                    current
                )

                current = (
                    ParallelGroup()
                )

            ################################################
            # Unsafe operations remain isolated.
            ################################################

            if operation.parallel_safe:

                current.add(
                    operation
                )

            else:

                groups.append(
                    ParallelGroup(
                        operations=[
                            operation
                        ]
                    )
                )

        if current.operations:

            groups.append(
                current
            )

        return groups