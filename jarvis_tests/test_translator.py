from vision.providers.computer_use.local_provider import LocalComputerProvider
from vision.providers.computer_use.manager import ComputerUseManager

from backend.translator.automation_translator import AutomationTranslator


provider = LocalComputerProvider()

provider.initialize()

manager = ComputerUseManager()

manager.register(provider)

translator = AutomationTranslator()

commands = [

    "open chrome",

    "click chrome",

    "type hello world"

]

for command in commands:

    computerAction = manager.predict(

        None,

        command

    )

    automationAction = translator.translate(

        computerAction

    )

    print()

    print(command)

    print(computerAction)

    print(automationAction)