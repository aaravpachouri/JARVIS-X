from automation.mouse.controller import MouseController
from core.actions import ActionType


class MouseExecutor:

    def __init__(self):

        self.mouse = MouseController()

    ##################################################

    def execute(self, action):

        match action.action:

            case ActionType.MOUSE_MOVE:

                self.mouse.move(

                    action.parameters["x"],

                    action.parameters["y"]

                )

            case ActionType.MOUSE_MOVE_CENTER:

                self.mouse.moveToCenter()

            case ActionType.LEFT_CLICK:

                self.mouse.click()

            case ActionType.RIGHT_CLICK:

                self.mouse.rightClick()

            case ActionType.DOUBLE_CLICK:

                self.mouse.doubleClick()

            case ActionType.SCROLL_UP:

                self.mouse.scrollUp()

            case ActionType.SCROLL_DOWN:

                self.mouse.scrollDown()

            case ActionType.DRAG:

                self.mouse.dragTo(

                    action.parameters["x"],

                    action.parameters["y"]

                )

            case _:

                return