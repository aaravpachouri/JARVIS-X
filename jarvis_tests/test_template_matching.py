from vision.detector.template_matcher import TemplateMatcher


matcher = TemplateMatcher()

result = matcher.locate(

    "desktop.png",

    "desktop.png"

)

print(result)