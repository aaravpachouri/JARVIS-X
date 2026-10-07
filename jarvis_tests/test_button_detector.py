from vision.ui.button_detector import ButtonDetector


detector = ButtonDetector()

buttons = detector.detect(

    "desktop.png"

)

print()

print(

    f"Detected {len(buttons)} buttons"

)

print()

for button in buttons:

    print(button)