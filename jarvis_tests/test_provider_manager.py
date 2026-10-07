from vision.engine import VisionEngine


engine = VisionEngine()

scene = engine.analyze(

    "desktop.png"

)

print()

print("Current Provider:")

print(

    engine.manager.current().__class__.__name__

)

print()

for key, value in scene.items():

    print(

        key,

        value

    )