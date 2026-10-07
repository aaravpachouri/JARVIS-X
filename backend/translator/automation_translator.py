from core.actions import Action
from core.actions import ActionType


class AutomationTranslator:

    ##################################################

    def translate(self, computerAction):

        action = computerAction.action
        data = computerAction.parameters

        ##################################################
        # APPLICATIONS
        ##################################################

        if action == "open":

            return Action(

                action=ActionType.OPEN_APP,

                parameters=data

            )

        ##################################################

        if action == "close":

            return Action(

                action=ActionType.CLOSE_APP,

                parameters=data

            )

        ##################################################
        # MOUSE
        ##################################################

        if action == "click":

            return Action(

                action=ActionType.LEFT_CLICK,

                parameters=data

            )

        ##################################################

        if action == "double_click":

            return Action(

                action=ActionType.DOUBLE_CLICK,

                parameters=data

            )

        ##################################################

        if action == "right_click":

            return Action(

                action=ActionType.RIGHT_CLICK,

                parameters=data

            )

        ##################################################

        if action == "scroll_up":

            return Action(

                action=ActionType.SCROLL_UP,

                parameters={}

            )

        ##################################################

        if action == "scroll_down":

            return Action(

                action=ActionType.SCROLL_DOWN,

                parameters={}

            )

        ##################################################
        # KEYBOARD
        ##################################################

        if action == "type":

            return Action(

                action=ActionType.TYPE_TEXT,

                parameters=data

            )

        ##################################################

        return Action(

            action=ActionType.UNKNOWN,

            parameters=data

        )