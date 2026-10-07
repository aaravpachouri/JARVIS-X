from automation.ocr.service import OCRService

from core.actions import ActionType


class OCRExecutor:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.ocr = OCRService()

    ##################################################
    # EXECUTE
    ##################################################

    def execute(self, action):

        match action.action:

            ##################################################
            # OCR SCREEN
            ##################################################

            case ActionType.OCR_SCREEN:

                path = action.parameters.get(
                    "image",
                    "desktop.png"
                )

                results = self.ocr.readScreenshot(
                    path
                )

                print()

                print("=" * 60)
                print("OCR RESULT")
                print("=" * 60)

                for result in results:

                    if len(result) < 2:
                        continue

                    text = result[1]

                    confidence = (
                        result[2]
                        if len(result) > 2
                        else 0
                    )

                    print(
                        f"{text} "
                        f"(confidence={confidence:.2f})"
                    )

                print()

                return results

            ##################################################
            # OCR IMAGE
            ##################################################

            case ActionType.OCR_IMAGE:

                path = action.parameters[
                    "image"
                ]

                results = self.ocr.readImage(
                    path
                )

                print()

                print("=" * 60)
                print("OCR RESULT")
                print("=" * 60)

                for result in results:

                    if len(result) < 2:
                        continue

                    text = result[1]

                    confidence = (
                        result[2]
                        if len(result) > 2
                        else 0
                    )

                    print(
                        f"{text} "
                        f"(confidence={confidence:.2f})"
                    )

                print()

                return results

            ##################################################
            # UNKNOWN
            ##################################################

            case _:

                print(
                    f"[OCR] Unsupported: "
                    f"{action.action.name}"
                )

                return None