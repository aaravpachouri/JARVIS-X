import cv2

from vision.service import VisionService


class ButtonDetector:

    def __init__(self):

        self.vision = VisionService()

    ##################################################

    def detect(

        self,

        image_path

    ):

        image = self.vision.loadOpenCV(

            image_path

        )

        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY

        )

        blur = cv2.GaussianBlur(

            gray,

            (5, 5),

            0

        )

        edges = cv2.Canny(

            blur,

            60,

            180

        )

        contours, _ = cv2.findContours(

            edges,

            cv2.RETR_EXTERNAL,

            cv2.CHAIN_APPROX_SIMPLE

        )

        buttons = []

        for contour in contours:

            x, y, w, h = cv2.boundingRect(

                contour

            )

            ##################################################

            if w < 50:

                continue

            if h < 20:

                continue

            ##################################################

            ratio = w / h

            if ratio < 1.5:

                continue

            if ratio > 8:

                continue

            ##################################################

            area = cv2.contourArea(

                contour

            )

            if area < 1000:

                continue

            ##################################################

            buttons.append({

                "x": x,

                "y": y,

                "width": w,

                "height": h

            })

        return buttons