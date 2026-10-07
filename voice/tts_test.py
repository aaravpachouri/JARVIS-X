from voice.tts_engine import TTSEngine


def main():

    print()
    print("================================")
    print("JARVIS KOKORO VOICE TEST")
    print("================================")
    print()

    tts = TTSEngine()

    tts.speak(
        "Good evening. "
        "I am JARVIS. "
        "All systems are operational. "
        "How may I assist you?"
    )

    print()
    print("================================")
    print("VOICE TEST COMPLETE")
    print("================================")


if __name__ == "__main__":

    main()