from vision.providers.mock_provider import MockVisionProvider


class VisionProviderManager:

    def __init__(self):

        ##################################################
        # DEFAULT PROVIDER
        ##################################################

        self.provider = MockVisionProvider()

    ##################################################

    def current(self):

        return self.provider

    ##################################################

    def setProvider(

        self,

        provider

    ):

        self.provider = provider