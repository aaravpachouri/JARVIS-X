from vision.service import VisionService


vision = VisionService()

image = vision.loadImage(

    "desktop.png"

)

print()

print(

    "Size:",

    vision.size(image)

)

print(

    "Center:",

    vision.center(image)

)