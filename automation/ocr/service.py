import easyocr
import numpy as np
from PIL import Image


class OCRService:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.reader = easyocr.Reader(
            ["en"],
            gpu=False
        )

    ##################################################
    # READ IMAGE
    ##################################################

    def readImage(
        self,
        image_path
    ):

        image = np.array(
            Image.open(
                image_path
            )
        )

        results = self.reader.readtext(
            image,
            detail=1
        )

        return results

    ##################################################
    # READ SCREENSHOT
    ##################################################

    def readScreenshot(
        self,
        screenshot_path
    ):

        return self.readImage(
            screenshot_path
        )

    ##################################################
    # READ TEXT ONLY
    ##################################################

    def readText(
        self,
        image_path
    ):

        results = self.readImage(
            image_path
        )

        texts = []

        for result in results:

            if len(result) < 2:
                continue

            text = result[1]

            texts.append(
                text
            )

        return "\n".join(
            texts
        )

    ##################################################
    # FIND TEXT
    ##################################################

    def findText(
        self,
        image_path,
        target
    ):

        target = str(
            target
        ).lower().strip()

        if not target:
            return None

        results = self.readImage(
            image_path
        )

        ##################################################
        # EXACT / PARTIAL MATCH
        ##################################################

        for result in results:

            if len(result) < 2:
                continue

            box = result[0]

            text = str(
                result[1]
            ).strip()

            confidence = (
                float(result[2])
                if len(result) > 2
                else 0.0
            )

            if target in text.lower():

                ##################################################
                # CENTER OF BOUNDING BOX
                ##################################################

                xs = [
                    point[0]
                    for point in box
                ]

                ys = [
                    point[1]
                    for point in box
                ]

                center_x = int(
                    sum(xs) / len(xs)
                )

                center_y = int(
                    sum(ys) / len(ys)
                )

                return {
                    "text": text,
                    "confidence": confidence,
                    "box": box,
                    "x": center_x,
                    "y": center_y
                }

        return None