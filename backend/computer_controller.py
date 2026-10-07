from automation.executors.engine import AutomationEngine

from backend.translator.automation_translator import AutomationTranslator


class ComputerController:

    ##################################################

    def __init__(self):

        self.translator = AutomationTranslator()

        self.engine = AutomationEngine()

    ##################################################

    def execute(

        self,

        computerAction

    ):

        action = self.translator.translate(

            computerAction

        )

        if action is None:

            return

        self.engine.execute(

            action

        )