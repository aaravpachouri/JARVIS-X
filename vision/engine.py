from vision.service import VisionService

from vision.providers.manager import VisionProviderManager


class VisionEngine:

    def __init__(self):

        self.vision = VisionService()

        self.manager = VisionProviderManager()

    ##################################################

    def analyze(

        self,

        image_path

    ):

        image = self.vision.loadImage(

            image_path

        )

        scene = self.manager.current().analyze(

            image_path

        )

        scene["width"] = self.vision.width(

            image

        )

        scene["height"] = self.vision.height(

            image

        )

        scene["center"] = self.vision.center(

            image

        )

        return scene