from vision.providers.mock_provider import MockVisionProvider


provider = MockVisionProvider()

scene = provider.analyze(

    "desktop.png"

)

print(scene)