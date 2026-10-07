from vision.providers.computer_use.provider import ComputerUseProvider
from vision.providers.computer_use.response import ComputerAction


class LocalComputerProvider(ComputerUseProvider):

    ##################################################

    def __init__(self):

        self.initialized = False

    ##################################################

    def initialize(self):

        if self.initialized:
            return

        self.initialized = True

        print()
        print("=" * 60)
        print("Local Computer Provider Ready")
        print("=" * 60)
        print()

    ##################################################

    def predict(

        self,

        image,

        instruction

    ):

        text = instruction.lower().strip()

        ##################################################
        # CLICK
        ##################################################

        if text.startswith("click"):

            target = instruction[5:].strip()

            return ComputerAction(

                action="click",

                parameters={

                    "target": target

                }

            )

        ##################################################
        # TYPE
        ##################################################

        if text.startswith("type"):

            value = instruction[4:].strip()

            return ComputerAction(

                action="type",

                parameters={

                    "text": value

                }

            )

        ##################################################
        # OPEN
        ##################################################

        if text.startswith("open"):

            app = instruction[4:].strip()

            return ComputerAction(

                action="open",

                parameters={

                    "app": app

                }

            )

        ##################################################
        # SCROLL
        ##################################################

        if text == "scroll up":

            return ComputerAction(

                action="scroll_up",

                parameters={}

            )

        ##################################################

        if text == "scroll down":

            return ComputerAction(

                action="scroll_down",

                parameters={}

            )

        ##################################################
        # UNKNOWN
        ##################################################

        return ComputerAction(

            action="unknown",

            parameters={

                "instruction": instruction

            }

        )