from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


############################################################
# APPLICATION CONTEXT
############################################################

@dataclass
class ApplicationContext:

    name: str = ""

    purpose: str = ""

    state: str = ""

    completed: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


############################################################
# MULTI-APPLICATION TASK
############################################################

@dataclass
class MultiApplicationTask:

    goal: str = ""

    applications: list[
        ApplicationContext
    ] = field(
        default_factory=list
    )

    current_application: Optional[
        str
    ] = None

    completed: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    ########################################################
    # APPLICATION REGISTRATION
    ########################################################

    def add_application(
        self,
        name: str,
        purpose: str = "",
    ) -> ApplicationContext:

        name = str(
            name or ""
        ).strip()

        if not name:

            raise ValueError(
                "Application name cannot be empty."
            )

        context = ApplicationContext(
            name=name,
            purpose=str(
                purpose or ""
            ).strip(),
        )

        self.applications.append(
            context
        )

        if self.current_application is None:

            self.current_application = name

        return context

    ########################################################
    # CURRENT APPLICATION
    ########################################################

    def current(
        self,
    ) -> Optional[
        ApplicationContext
    ]:

        if not self.current_application:

            return None

        for application in self.applications:

            if (
                application.name.lower()
                ==
                self.current_application.lower()
            ):

                return application

        return None

    ########################################################
    # SWITCH APPLICATION
    ########################################################

    def switch_to(
        self,
        name: str,
    ) -> bool:

        for application in self.applications:

            if (
                application.name.lower()
                ==
                str(name or "").strip().lower()
            ):

                self.current_application = (
                    application.name
                )

                return True

        return False

    ########################################################
    # COMPLETE APPLICATION
    ########################################################

    def complete_application(
        self,
        name: Optional[str] = None,
        state: str = "",
    ) -> bool:

        target = (
            str(
                name
                or
                self.current_application
                or
                ""
            ).strip()
        )

        for application in self.applications:

            if (
                application.name.lower()
                ==
                target.lower()
            ):

                application.completed = True

                application.state = str(
                    state or ""
                ).strip()

                return True

        return False

    ########################################################
    # STATUS
    ########################################################

    def all_applications_complete(
        self,
    ) -> bool:

        if not self.applications:

            return False

        return all(
            application.completed
            for application
            in self.applications
        )

    def complete_task(
        self,
    ) -> None:

        if self.all_applications_complete():

            self.completed = True

    ########################################################
    # CONTEXT
    ########################################################

    def reasoning_context(
        self,
    ) -> dict[str, Any]:

        return {
            "goal": self.goal,

            "current_application":
                self.current_application,

            "applications": [
                {
                    "name":
                        application.name,

                    "purpose":
                        application.purpose,

                    "state":
                        application.state,

                    "completed":
                        application.completed,

                    "metadata":
                        dict(
                            application.metadata
                        ),
                }

                for application
                in self.applications
            ],

            "task_completed":
                self.completed,

            "metadata":
                dict(
                    self.metadata
                ),
        }