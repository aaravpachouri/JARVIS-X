from vision.engine import VisionEngine


engine = VisionEngine()

result = engine.analyze(

    "desktop.png"

)

print()

for key, value in result.items():

    print(

        key,

        ":",

        value

    )