from automation.ocr.service import OCRService


ocr = OCRService()

text = ocr.readImage(

    "desktop.png"

)

print()

print("===== OCR RESULT =====")

print()

print(text)