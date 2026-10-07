from automation.clipboard.service import ClipboardService
from core.actions import ActionType


class ClipboardExecutor:

    def __init__(self):

        self.clipboard = ClipboardService()

    ##################################################

    def execute(self, action):

        match action.action:

            ##################################################

            case ActionType.READ_CLIPBOARD:

                print(

                    self.clipboard.read()

                )

            ##################################################

            case ActionType.WRITE_CLIPBOARD:

                self.clipboard.write(

                    action.parameters["text"]

                )

            ##################################################

            case ActionType.CLEAR_CLIPBOARD:

                self.clipboard.clear()

            ##################################################

            case _:

                return