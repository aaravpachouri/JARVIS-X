import time

from automation.vision.screen_locator import ScreenLocator
from automation.keyboard.controller import KeyboardController


class ScreenActionService:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.locator = ScreenLocator()

        self.keyboard = KeyboardController()

    ##################################################
    # CLICK AND TYPE
    ##################################################

    def clickAndType(
        self,
        target,
        text,
        wait=0.5
    ):

        print(
            f"[ScreenAction] Finding: {target}"
        )

        clicked = self.locator.click(
            target
        )

        if not clicked:

            print(
                f"[ScreenAction] "
                f"Could not find: {target}"
            )

            return False

        time.sleep(
            wait
        )

        print(
            f"[ScreenAction] Typing: {text}"
        )

        self.keyboard.type(
            text
        )

        return True

    ##################################################
    # CLICK, TYPE AND ENTER
    ##################################################

    def clickTypeEnter(
        self,
        target,
        text,
        wait=0.5
    ):

        success = self.clickAndType(
            target,
            text,
            wait
        )

        if not success:

            return False

        time.sleep(
            0.2
        )

        self.keyboard.press(
            "enter"
        )

        return True