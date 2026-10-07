import pyautogui


class Screen:

    def __init__(self):

        pass

    ##################################################

    def width(self):

        return pyautogui.size().width

    ##################################################

    def height(self):

        return pyautogui.size().height

    ##################################################

    def size(self):

        return pyautogui.size()

    ##################################################

    def center(self):

        size = self.size()

        return (

            size.width // 2,

            size.height // 2

        )

    ##################################################

    def topLeft(self):

        return (0, 0)

    ##################################################

    def topRight(self):

        return (

            self.width() - 1,

            0

        )

    ##################################################

    def bottomLeft(self):

        return (

            0,

            self.height() - 1

        )

    ##################################################

    def bottomRight(self):

        return (

            self.width() - 1,

            self.height() - 1

        )