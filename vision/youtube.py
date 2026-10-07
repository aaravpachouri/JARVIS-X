import re

from automation.ocr.service import OCRService
from automation.screenshot.service import ScreenshotService


class YouTubeVision:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.ocr = OCRService()

        self.screenshot = ScreenshotService()

    ##################################################
    # CAPTURE
    ##################################################

    def capture(self):

        return self.screenshot.save(
            "youtube_results.png"
        )

    ##################################################
    # FIND RESULT TEXT
    ##################################################

    def findResults(
        self,
        query
    ):

        image = self.capture()

        results = self.ocr.readImage(
            image
        )

        query_words = [

            word.lower()

            for word in re.findall(
                r"\w+",
                query
            )

            if len(word) > 2

        ]

        matches = []

        for result in results:

            if len(result) < 3:

                continue

            box = result[0]

            text = str(
                result[1]
            ).strip()

            confidence = float(
                result[2]
            )

            lower = text.lower()

            score = 0

            for word in query_words:

                if word in lower:

                    score += 1

            if score == 0:

                continue

            xs = [
                point[0]
                for point in box
            ]

            ys = [
                point[1]
                for point in box
            ]

            x = int(
                sum(xs) / len(xs)
            )

            y = int(
                sum(ys) / len(ys)
            )

            matches.append({

                "text": text,

                "confidence":
                    confidence,

                "x": x,

                "y": y,

                "score":
                    score

            })

        ##################################################
        # SORT BY MATCH QUALITY
        ##################################################

        matches.sort(
            key=lambda item: (
                -item["score"],
                item["y"]
            )
        )

        ##################################################
        # REMOVE DUPLICATE AREAS
        ##################################################

        unique = []

        for item in matches:

            duplicate = False

            for existing in unique:

                if abs(
                    item["x"] -
                    existing["x"]
                ) < 100 and abs(
                    item["y"] -
                    existing["y"]
                ) < 60:

                    duplicate = True

                    break

            if not duplicate:

                unique.append(
                    item
                )

        ##################################################
        # ORDER TOP TO BOTTOM
        ##################################################

        unique.sort(
            key=lambda item:
                item["y"]
        )

        ##################################################

        return unique

    ##################################################
    # GET RESULT
    ##################################################

    def getResult(
        self,
        query,
        number=1
    ):

        results = self.findResults(
            query
        )

        if not results:

            print(
                "[YouTube] "
                "No matching results found."
            )

            return None

        index = int(
            number
        ) - 1

        if index < 0:

            index = 0

        if index >= len(results):

            print(
                f"[YouTube] Only "
                f"{len(results)} matching "
                f"results found."
            )

            return None

        result = results[
            index
        ]

        print(
            f"[YouTube] Result "
            f"{number}: "
            f"{result['text']} "
            f"at "
            f"({result['x']}, "
            f"{result['y']})"
        )

        return result