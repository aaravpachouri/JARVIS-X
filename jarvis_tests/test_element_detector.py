from vision.ui.element_detector import ElementDetector


detector = ElementDetector()

elements = detector.detectRectangles(

    "desktop.png"

)

print()

print(

    f"Detected {len(elements)} UI elements"

)

print()

for element in elements[:20]:

    print(element)