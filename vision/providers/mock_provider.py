from vision.providers.provider import VisionProvider


class MockVisionProvider(VisionProvider):

    ##################################################

    def analyze(

        self,

        image_path

    ):

        return {

            "buttons": [],

            "icons": [],

            "windows": [],

            "text_fields": [],

            "objects": [],

            "text": ""

        }
