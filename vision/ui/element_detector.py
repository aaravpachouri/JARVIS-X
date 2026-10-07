import cv2

from vision.service import VisionService


class ElementDetector:

    def __init__(self):

        self.vision = VisionService()

    ##################################################

    def detectRectangles(

        self,

        image_path,

        minWidth=40,

        minHeight=20

    ):

        image = self.vision.loadOpenCV(

            image_path

        )

        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY

        )

        edges = cv2.Canny(

            gray,

            60,

            180

        )

        contours, _ = cv2.findContours(

            edges,

            cv2.RETR_EXTERNAL,

            cv2.CHAIN_APPROX_SIMPLE

        )

        elements = []

        for contour in contours:

            x, y, w, h = cv2.boundingRect(

                contour

            )

            if w < minWidth:

                continue

            if h < minHeight:

                continue

            elements.append({

                "x": x,

                "y": y,

                "width": w,

                "height": h

            })

        return elements