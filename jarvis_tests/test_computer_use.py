from vision.providers.computer_use.manager import ComputerUseManager
from vision.providers.computer_use.local_provider import LocalComputerProvider


manager = ComputerUseManager()

provider = LocalComputerProvider()

provider.initialize()

manager.register(provider)

commands = [

    "click chrome",

    "type hello world",

    "open spotify"

]

for command in commands:

    result = manager.predict(

        None,

        command

    )

    print()

    print(command)

    print(result)