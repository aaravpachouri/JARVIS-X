from vision.analyzer import ScreenAnalyzer


analyzer = ScreenAnalyzer()

scene = analyzer.analyze(

    "desktop.png"

)

print()

print("=" * 60)

print("SCREEN ANALYSIS")

print("=" * 60)

print()

for key, value in scene.items():

    print(

        key,

        ":",

        value

    )