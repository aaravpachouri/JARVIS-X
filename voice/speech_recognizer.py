from __future__ import annotations

import speech_recognition as sr
import numpy as np


class SpeechRecognizer:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(
        self,
    ):

        self.recognizer = sr.Recognizer()

        ##################################################
        # RECOGNITION SETTINGS
        ##################################################

        self.recognizer.dynamic_energy_threshold = True

        # Silence required to finish a phrase.
        self.recognizer.pause_threshold = 1.2

        # Small amount of audio retained around speech.
        self.recognizer.non_speaking_duration = 0.35

        # Prevent very long accidental recordings.
        self.command_phrase_time_limit = 12

        # How long JARVIS waits for you to START speaking.
        self.command_start_timeout = 6

        ##################################################
        # MICROPHONE
        ##################################################

        self.input_device = 1

        ##################################################
        # LANGUAGES
        ##################################################

        self.primary_language = "en-IN"

        self.fallback_language = "en-US"

        ##################################################
        # WAKE WORDS
        ##################################################

        self.wake_words = (
            "hey jarvis",
            "jarvis",
        )

        ##################################################
        # WAKE PHRASE
        ##################################################

        self.wake_phrase_time_limit = 4

        ##################################################
        # CLAP
        ##################################################

        self.clap_threshold = 0.45

        self.clap_min_gap = 0.12

        self.clap_max_gap = 0.9

    ##################################################
    # MICROPHONE SOURCE
    ##################################################

    def _open_microphone(
        self,
    ):

        return sr.Microphone(
            device_index=self.input_device
        )

    ##################################################
    # CALIBRATE
    ##################################################

    def _calibrate(
        self,
        source,
    ):

        try:

            self.recognizer.adjust_for_ambient_noise(
                source,
                duration=0.25,
            )

        except Exception as exc:

            print(
                "[Voice] Ambient calibration warning:",
                exc,
            )

    ##################################################
    # LISTEN FOR ONE COMMAND
    #
    # This captures ONE intentional speech phrase.
    #
    # It does not continuously monitor speech.
    ##################################################

    def listen(
        self,
    ) -> str:

        audio = None

        try:

            with self._open_microphone() as source:

                print(
                    "[Voice] Waiting for command..."
                )

                ##################################################
                # CALIBRATE
                ##################################################

                self._calibrate(
                    source
                )

                print(
                    "[Voice] Energy threshold:",
                    round(
                        self.recognizer.energy_threshold,
                        1,
                    ),
                )

                ##################################################
                # WAIT FOR ACTUAL SPEECH
                #
                # Random short noises / silence simply time out.
                ##################################################

                try:

                    audio = self.recognizer.listen(
                        source,
                        timeout=self.command_start_timeout,
                        phrase_time_limit=(
                            self.command_phrase_time_limit
                        ),
                    )

                except sr.WaitTimeoutError:

                    print(
                        "[Voice] No command detected."
                    )

                    return ""

        except Exception as exc:

            print(
                "[Voice] Microphone error:",
                exc,
            )

            return ""

        ##################################################
        # RECOGNIZE
        ##################################################

        if audio is None:

            return ""

        text = self.recognize(
            audio
        )

        if not text:

            return ""

        ##################################################
        # FILTER VERY SHORT / LIKELY ACCIDENTAL INPUT
        ##################################################

        if not self.isMeaningfulCommand(
            text
        ):

            print(
                "[Voice] Ignoring unclear command:",
                text,
            )

            return ""

        return text

    ##################################################
    # MEANINGFUL COMMAND FILTER
    ##################################################

    @staticmethod
    def isMeaningfulCommand(
        text,
    ) -> bool:

        text = str(
            text or ""
        ).strip()

        if not text:

            return False

        words = text.split()

        ##################################################
        # Ignore extremely short accidental recognition.
        ##################################################

        if len(words) == 1:

            word = words[0].lower()

            ignored = {
                "uh",
                "um",
                "hmm",
                "hm",
                "yeah",
                "yes",
                "no",
                "okay",
                "ok",
                "hey",
            }

            if word in ignored:

                return False

        return True

    ##################################################
    # RECOGNIZE
    ##################################################

    def recognize(
        self,
        audio,
    ) -> str:

        ##################################################
        # PRIMARY
        ##################################################

        try:

            text = self.recognizer.recognize_google(
                audio,
                language=self.primary_language,
            )

            text = str(
                text or ""
            ).strip()

            if text:

                print(
                    f"[Voice] Heard: {text}"
                )

                return text

        except sr.UnknownValueError:

            print(
                "[Voice] Speech not understood."
            )

        except sr.RequestError as exc:

            print(
                "[Voice] Speech service error:",
                exc,
            )

            return ""

        except Exception as exc:

            print(
                "[Voice] Recognition error:",
                exc,
            )

        ##################################################
        # FALLBACK
        ##################################################

        try:

            print(
                "[Voice] Trying fallback recognition..."
            )

            text = self.recognizer.recognize_google(
                audio,
                language=self.fallback_language,
            )

            text = str(
                text or ""
            ).strip()

            if text:

                print(
                    f"[Voice] Heard: {text}"
                )

                return text

        except sr.UnknownValueError:

            pass

        except sr.RequestError as exc:

            print(
                "[Voice] Fallback speech service error:",
                exc,
            )

        except Exception as exc:

            print(
                "[Voice] Fallback recognition error:",
                exc,
            )

        return ""

    ##################################################
    # WAKE WORD CHECK
    ##################################################

    def isWakeWord(
        self,
        text,
    ) -> bool:

        text = str(
            text or ""
        ).lower().strip()

        if not text:

            return False

        return any(
            wake_word in text
            for wake_word in self.wake_words
        )

    ##################################################
    # REMOVE WAKE WORD
    ##################################################

    def removeWakeWord(
        self,
        text,
    ) -> str:

        text = str(
            text or ""
        ).strip()

        lower_text = text.lower()

        for wake_word in self.wake_words:

            index = lower_text.find(
                wake_word
            )

            if index != -1:

                return text[
                    index + len(wake_word):
                ].strip()

        return text

    ##################################################
    # LISTEN FOR WAKE
    ##################################################

    def listenForWake(
        self,
    ):

        try:

            with self._open_microphone() as source:

                print(
                    "[Voice] Waiting for Hey JARVIS..."
                )

                self._calibrate(
                    source
                )

                audio = self.recognizer.listen(
                    source,
                    timeout=None,
                    phrase_time_limit=(
                        self.wake_phrase_time_limit
                    ),
                )

        except Exception as exc:

            print(
                "[Voice] Wake microphone error:",
                exc,
            )

            return ""

        ##################################################
        # DOUBLE CLAP
        ##################################################

        if self.detectDoubleClap(
            audio
        ):

            print(
                "[Voice] Double clap detected."
            )

            return "CLAP"

        ##################################################
        # SPEECH
        ##################################################

        text = self.recognize(
            audio
        )

        if not text:

            return ""

        ##################################################
        # WAKE WORD
        ##################################################

        if self.isWakeWord(
            text
        ):

            return (
                "WAKE:"
                + text
            )

        return ""

    ##################################################
    # DOUBLE CLAP DETECTION
    ##################################################

    def detectDoubleClap(
        self,
        audio,
    ) -> bool:

        try:

            sample_width = (
                audio.sample_width
            )

            sample_rate = (
                audio.sample_rate
            )

            raw = (
                audio.get_raw_data()
            )

            ##################################################
            # CONVERT
            ##################################################

            if sample_width == 2:

                samples = (
                    np.frombuffer(
                        raw,
                        dtype=np.int16,
                    ).astype(
                        np.float32
                    )
                )

            elif sample_width == 4:

                samples = (
                    np.frombuffer(
                        raw,
                        dtype=np.int32,
                    ).astype(
                        np.float32
                    )
                )

            else:

                samples = (
                    np.frombuffer(
                        raw,
                        dtype=np.uint8,
                    ).astype(
                        np.float32
                    )
                )

                samples -= 128

            if len(
                samples
            ) == 0:

                return False

            maximum = np.max(
                np.abs(samples)
            )

            if maximum == 0:

                return False

            samples /= maximum

            ##################################################
            # ENERGY WINDOWS
            ##################################################

            window_size = int(
                sample_rate * 0.025
            )

            if window_size <= 0:

                return False

            energies = []

            times = []

            for start in range(
                0,
                len(samples),
                window_size,
            ):

                chunk = samples[
                    start:
                    start + window_size
                ]

                if len(
                    chunk
                ) == 0:

                    continue

                rms = np.sqrt(
                    np.mean(
                        chunk * chunk
                    )
                )

                energies.append(
                    rms
                )

                times.append(
                    start / sample_rate
                )

            ##################################################
            # CLAP IMPULSES
            ##################################################

            clap_times = []

            last_clap = -999

            for index, energy in enumerate(
                energies
            ):

                if (
                    energy
                    <
                    self.clap_threshold
                ):

                    continue

                current_time = (
                    times[index]
                )

                if (
                    current_time
                    -
                    last_clap
                ) < self.clap_min_gap:

                    continue

                clap_times.append(
                    current_time
                )

                last_clap = (
                    current_time
                )

            ##################################################
            # REQUIRE TWO
            ##################################################

            if len(
                clap_times
            ) < 2:

                return False

            ##################################################
            # CHECK GAP
            ##################################################

            for index in range(
                1,
                len(clap_times),
            ):

                gap = (
                    clap_times[index]
                    -
                    clap_times[index - 1]
                )

                if (
                    self.clap_min_gap
                    <= gap
                    <= self.clap_max_gap
                ):

                    return True

            return False

        except Exception as exc:

            print(
                "[Voice] Clap detection error:",
                exc,
            )

            return False