import re


class CommandNormalizer:

    def __init__(self):

        self.phrases = [

            "could you",

            "can you",

            "would you",

            "please",

            "kindly",

            "for me",

            "i want to",

            "i would like to",

            "i'd like to",

            "let's",

            "lets",

            "help me",

            "try to"

        ]

    ##################################################

    def normalize(self, command):

        command = command.lower().strip()

        ##################################################
        # REMOVE POLITE PHRASES
        ##################################################

        for phrase in self.phrases:

            command = command.replace(

                phrase,

                ""

            )

        ##################################################
        # REMOVE EXTRA SPACES
        ##################################################

        command = re.sub(

            r"\s+",

            " ",

            command

        ).strip()

        return command