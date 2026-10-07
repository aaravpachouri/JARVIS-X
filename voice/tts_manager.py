from voice.tts_engine import TTSEngine


##################################################
# SHARED JARVIS TTS
##################################################

_tts = None


def get_tts():

    global _tts

    if _tts is None:

        print(
            "[TTSManager] Creating shared JARVIS voice..."
        )

        _tts = TTSEngine()

        print(
            "[TTSManager] Shared JARVIS voice ready."
        )

    return _tts