from voice.speech_recognizer import SpeechRecognizer


recognizer = SpeechRecognizer()

print("Say something...")

text = recognizer.listen()

print()
print("RESULT:")
print(text)