from voice.wake_detector import WakeDetector


print()
print("================================")
print("JARVIS WAKE WORD TEST")
print("================================")
print()

detector = WakeDetector()

print(
    "Say: Hey JARVIS"
)

print(
    "Press CTRL+C to stop."
)

print()

detector.test()