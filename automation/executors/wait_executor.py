import time

from core.actions import ActionType


class WaitExecutor:

    ##################################################
    # EXECUTE
    ##################################################

    def execute(self, action):

        if action.action != ActionType.WAIT:

            return

        seconds = action.parameters.get(
            "seconds",
            1
        )

        try:

            seconds = float(
                seconds
            )

        except (
            TypeError,
            ValueError
        ):

            seconds = 1

        seconds = max(
            0,
            seconds
        )

        print(
            f"[Wait] Waiting {seconds:.2f}s"
        )

        time.sleep(
            seconds
        )