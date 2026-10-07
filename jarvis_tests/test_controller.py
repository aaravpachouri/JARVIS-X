from vision.providers.computer_use.local_provider import LocalComputerProvider
from vision.providers.computer_use.manager import ComputerUseManager

from backend.computer_controller import ComputerController


provider = LocalComputerProvider()

provider.initialize()

manager = ComputerUseManager()

manager.register(

    provider

)

controller = ComputerController()

commands = [

    "open notepad",

    "open calculator",

    "open chrome"

]

for command in commands:

    print()

    print(command)

    action = manager.predict(

        None,

        command

    )

    controller.execute(

        action

    )