from vision.engine import VisionEngine
from automation.ocr.service import OCRService


class ScreenAnalyzer:

    def __init__(self):

        self.vision = VisionEngine()

        self.ocr = OCRService()

    ##################################################

    def analyze(

        self,

        image_path

    ):

        scene = self.vision.analyze(

            image_path

        )

        text = self.ocr.readImage(

            image_path

        )

        scene["text"] = text

        return scene