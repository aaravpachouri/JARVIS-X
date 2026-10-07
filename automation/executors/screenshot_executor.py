from automation.screenshot.service import ScreenshotService
from core.actions import ActionType


class ScreenshotExecutor:

    def __init__(self):

        self.screenshot = ScreenshotService()

    ##################################################

    def execute(self, action):

        match action.action:

            ##################################################

            case ActionType.TAKE_SCREENSHOT:

                self.screenshot.capture()

            ##################################################

            case ActionType.SAVE_SCREENSHOT:

                filename = action.parameters.get(

                    "filename",

                    "screenshot.png"

                )

                path = self.screenshot.save(

                    filename

                )

                print(

                    f"[Screenshot] Saved -> {path}"

                )

            ##################################################

            case _:

                print(

                    f"[Screenshot] Unsupported: {action.action.name}"

                )
            