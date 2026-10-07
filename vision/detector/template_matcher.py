import cv2

from vision.service import VisionService


class TemplateMatcher:

    def __init__(self):

        self.vision = VisionService()

    ##################################################

    def locate(

        self,

        image_path,

        template_path,

        threshold=0.90

    ):

        image = self.vision.loadOpenCV(

            image_path

        )

        template = self.vision.loadOpenCV(

            template_path

        )

        result = cv2.matchTemplate(

            image,

            template,

            cv2.TM_CCOEFF_NORMED

        )

        _, maxValue, _, maxLocation = cv2.minMaxLoc(

            result

        )

        if maxValue < threshold:

            return None

        h, w = template.shape[:2]

        return {

            "x": maxLocation[0],

            "y": maxLocation[1],

            "width": w,

            "height": h,

            "confidence": float(maxValue)

        }