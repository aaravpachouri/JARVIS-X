import speech_recognition as sr


DEVICE_INDEX = 1


recognizer = sr.Recognizer()

recognizer.dynamic_energy_threshold = True

recognizer.pause_threshold = 0.8


print()
print("================================")
print("JARVIS MICROPHONE TEST")
print("================================")

print(
    f"Using microphone device: {DEVICE_INDEX}"
)

print()
print("Calibrating...")

with sr.Microphone(
    device_index=DEVICE_INDEX
) as source:

    recognizer.adjust_for_ambient_noise(
        source,
        duration=1
    )

    print()
    print("Speak something...")
    print()

    audio = recognizer.listen(
        source,
        timeout=None,
        phrase_time_limit=5
    )


print()
print("Processing speech...")
print()

try:

    text = recognizer.recognize_google(
        audio
    )

    print("================================")
    print("HEARD:")
    print(text)
    print("================================")

except sr.UnknownValueError:

    print(
        "Could not understand the audio."
    )

except sr.RequestError as e:

    print(
        f"Speech service error: {e}"
    )

except Exception as e:

    print(
        f"Error: {e}"
    )