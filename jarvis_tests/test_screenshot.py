from automation.screenshot.service import ScreenshotService


service = ScreenshotService()

print(

    "Monitors:",

    service.monitorCount()

)

path = service.save(

    "test_capture.png"

)

print(

    path
)