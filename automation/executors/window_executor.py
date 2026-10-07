from automation.window.service import WindowService
from core.actions import ActionType


class WindowExecutor:

    def __init__(self):

        self.window = WindowService()

    ##################################################
    # WINDOW TARGET
    ##################################################

    @staticmethod
    def _get_window_target(
        parameters
    ):

        if not isinstance(
            parameters,
            dict
        ):
            return ""

        return str(
            parameters.get(
                "window",
                parameters.get(
                    "window_title",
                    parameters.get(
                        "title",
                        ""
                    )
                )
            )
            or
            ""
        ).strip()

    ##################################################
    # EXECUTE
    ##################################################

    def execute(
        self,
        action
    ):

        if action is None:

            return False

        parameters = getattr(
            action,
            "parameters",
            {}
        )

        target = self._get_window_target(
            parameters
        )

        if not target:

            print(
                "[WindowExecutor] "
                "No window target supplied."
            )

            return False

        match action.action:

            ##################################################
            # FOCUS
            ##################################################

            case ActionType.FOCUS_WINDOW:

                return self.window.focus(
                    target
                )

            ##################################################
            # CLOSE
            ##################################################

            case ActionType.CLOSE_WINDOW:

                return self.window.close(
                    target
                )

            ##################################################
            # MINIMIZE
            ##################################################

            case ActionType.MINIMIZE_WINDOW:

                return self.window.minimize(
                    target
                )

            ##################################################
            # MAXIMIZE
            ##################################################

            case ActionType.MAXIMIZE_WINDOW:

                return self.window.maximize(
                    target
                )

            ##################################################
            # RESTORE
            ##################################################

            case ActionType.RESTORE_WINDOW:

                return self.window.restore(
                    target
                )

            ##################################################
            # MOVE
            ##################################################

            case ActionType.MOVE_WINDOW:

                if (
                    "x" not in parameters
                    or
                    "y" not in parameters
                ):

                    print(
                        "[WindowExecutor] "
                        "MOVE_WINDOW requires x and y."
                    )

                    return False

                return self.window.move(
                    target,
                    parameters["x"],
                    parameters["y"]
                )

            ##################################################
            # RESIZE
            ##################################################

            case ActionType.RESIZE_WINDOW:

                if (
                    "width" not in parameters
                    or
                    "height" not in parameters
                ):

                    print(
                        "[WindowExecutor] "
                        "RESIZE_WINDOW requires width and height."
                    )

                    return False

                return self.window.resize(
                    target,
                    parameters["width"],
                    parameters["height"]
                )

            ##################################################
            # UNSUPPORTED
            ##################################################

            case _:

                print(
                    "[WindowExecutor] "
                    f"Unsupported action: "
                    f"{action.action}"
                )

                return False