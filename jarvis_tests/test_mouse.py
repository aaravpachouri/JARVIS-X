from automation.mouse.controller import MouseController

mouse = MouseController()

print("Position:", mouse.position())

print("Moving to center in 3 seconds...")

import time

time.sleep(3)

mouse.moveToCenter()

print("Done!")