from automation.vision.screen_locator import ScreenLocator

from core.actions import ActionType


class VisionExecutor:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.locator = ScreenLocator()

    ##################################################
    # EXECUTE
    ##################################################

    def execute(
        self,
        action
    ):

        match action.action:

            ##################################################
            # LOCATE TEXT
            ##################################################

            case ActionType.LOCATE_TEXT:

                target = action.parameters[
                    "target"
                ]

                return self.locator.find(
                    target
                )

            ##################################################
            # CLICK TEXT
            ##################################################

            case ActionType.CLICK_TEXT:

                target = action.parameters[
                    "target"
                ]

                return self.locator.click(
                    target
                )

            ##################################################
            # CLICK + TYPE + ENTER
            ##################################################

            case ActionType.CLICK_TYPE_ENTER:

                target = action.parameters.get(
                    "target",
                    "Search"
                )

                text = action.parameters.get(
                    "text",
                    ""
                )

                print(
                    f"[ScreenAction] Finding: "
                    f"{target}"
                )

                return self.locator.clickTypeEnter(
                    target,
                    text
                )

            ##################################################
            # CLICK FIRST VIDEO
            ##################################################

            case ActionType.CLICK_FIRST_VIDEO:

                print(
                    "[ScreenAction] Finding first video"
                )

                return self.locator.clickFirstVideo()

            ##################################################
            # UNSUPPORTED
            ##################################################

            case _:

                print(
                    f"[Vision] Unsupported action: "
                    f"{action.action.name}"
                )

                return False