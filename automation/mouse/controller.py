import pyautogui

from automation.mouse.screen import Screen


class MouseController:

    def __init__(self):

        self.screen = Screen()

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    ##################################################
    # POSITION
    ##################################################

    def position(self):

        return pyautogui.position()

    ##################################################

    def x(self):

        return self.position().x

    ##################################################

    def y(self):

        return self.position().y

    ##################################################
    # MOVE
    ##################################################

    def move(self, x, y):

        pyautogui.moveTo(

            x,

            y

        )

    ##################################################

    def moveSmooth(

        self,

        x,

        y,

        duration=0.4

    ):

        pyautogui.moveTo(

            x,

            y,

            duration=duration

        )

    ##################################################

    def moveRelative(

        self,

        dx,

        dy

    ):

        pyautogui.moveRel(

            dx,

            dy,

            duration=0.2

        )

    ##################################################

    def moveToCenter(self):

        x, y = self.screen.center()

        self.moveSmooth(

            x,

            y

        )

    ##################################################
    # CLICK
    ##################################################

    def click(self):

        pyautogui.click()

    ##################################################

    def doubleClick(self):

        pyautogui.doubleClick()

    ##################################################

    def rightClick(self):

        pyautogui.rightClick()

    ##################################################

    def middleClick(self):

        pyautogui.middleClick()

    ##################################################
    # SCROLL
    ##################################################

    def scrollUp(

        self,

        amount=500

    ):

        pyautogui.scroll(amount)

    ##################################################

    def scrollDown(

        self,

        amount=500

    ):

        pyautogui.scroll(-amount)

    ##################################################
    # DRAG
    ##################################################

    def dragTo(

        self,

        x,

        y,

        duration=0.5

    ):

        pyautogui.dragTo(

            x,

            y,

            duration=duration,

            button="left"

        )

    ##################################################

    def dragRelative(

        self,

        dx,

        dy,

        duration=0.5

    ):

        pyautogui.dragRel(

            dx,

            dy,

            duration=duration,

            button="left"

        )