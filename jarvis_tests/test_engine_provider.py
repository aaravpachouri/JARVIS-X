from vision.engine import VisionEngine


engine = VisionEngine()

scene = engine.analyze(

    "desktop.png"

)

print()

print("=" * 60)

print("VISION ENGINE")

print("=" * 60)

print()

for key, value in scene.items():

    print(

        key,

        ":",

        value

    )