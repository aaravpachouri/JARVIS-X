class ComputerUseManager:

    def __init__(self):

        self.provider = None

    ##############################################

    def register(

        self,

        provider

    ):

        self.provider = provider

    ##############################################

    def predict(

        self,

        image,

        instruction

    ):

        return self.provider.predict(

            image,

            instruction

        )