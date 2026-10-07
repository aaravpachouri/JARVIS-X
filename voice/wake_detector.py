import queue
import time

import numpy as np
import sounddevice as sd

from openwakeword.model import Model


class WakeDetector:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.sample_rate = 16000

        self.channels = 1

        self.block_size = 1280

        self.device = 1

        ##################################################
        # WAKE WORD
        ##################################################

        self.wake_threshold = 0.5

        self.model = Model(
            wakeword_models=[
                "hey_jarvis"
            ]
        )

        ##################################################
        # AUDIO
        ##################################################

        self.audioQueue = queue.Queue()

        ##################################################
        # CLAP DETECTION
        ##################################################

        self.clap_peak_threshold = 150

        self.clap_rms_threshold = 25

        self.clap_crest_threshold = 3.0

        self.clap_min_gap = 0.25

        self.clap_max_gap = 0.65

        ##################################################
        # STATE
        ##################################################

        self.lastCandidateTime = 0

        self.candidateTimes = []

    ##################################################
    # AUDIO CALLBACK
    ##################################################

    def _audioCallback(
        self,
        indata,
        frames,
        timeInfo,
        status
    ):

        if status:

            print(
                f"[Wake] Audio status: {status}"
            )

        audio = indata[:, 0].copy()

        self.audioQueue.put(
            audio
        )

    ##################################################
    # RESET
    ##################################################

    def _reset(self):

        self.lastCandidateTime = 0

        self.candidateTimes = []

        self.model.reset()

        while not self.audioQueue.empty():

            try:

                self.audioQueue.get_nowait()

            except queue.Empty:

                break

    ##################################################
    # ANALYZE AUDIO
    ##################################################

    def _analyzeAudio(self, audio):

        samples = np.asarray(
            audio,
            dtype=np.float32
        )

        if len(samples) == 0:

            return None

        ##################################################
        # PEAK
        ##################################################

        peak = float(
            np.max(
                np.abs(samples)
            )
        )

        ##################################################
        # RMS
        ##################################################

        rms = float(
            np.sqrt(
                np.mean(
                    samples * samples
                )
            )
        )

        ##################################################
        # CREST
        ##################################################

        crest = (
            peak /
            max(
                rms,
                1
            )
        )

        return {
            "peak": peak,
            "rms": rms,
            "crest": crest
        }

    ##################################################
    # CANDIDATE CLAP
    ##################################################

    def _isClapCandidate(self, audio):

        info = self._analyzeAudio(
            audio
        )

        if info is None:

            return False

        peak = info["peak"]

        rms = info["rms"]

        crest = info["crest"]

        ##################################################
        # TOO QUIET
        ##################################################

        if peak < self.clap_peak_threshold:

            return False

        ##################################################
        # TOO MUCH ENERGY
        # Usually speech / large environmental noise
        ##################################################

        if peak > 500:

            return False

        ##################################################
        # RMS
        ##################################################

        if rms < self.clap_rms_threshold:

            return False

        ##################################################
        # SHARPNESS
        ##################################################

        if crest < self.clap_crest_threshold:

            return False

        ##################################################
        # DIAGNOSTIC
        ##################################################

        print(
            "[Wake] Clap candidate: "
            f"peak={peak:.0f} "
            f"rms={rms:.0f} "
            f"crest={crest:.2f}"
        )

        return True

    ##################################################
    # DOUBLE CLAP
    ##################################################

    def _checkDoubleClap(self, audio):

        if not self._isClapCandidate(
            audio
        ):

            return False

        now = time.monotonic()

        ##################################################
        # IGNORE DUPLICATE BLOCKS
        ##################################################

        if (
            now -
            self.lastCandidateTime
        ) < self.clap_min_gap:

            return False

        self.lastCandidateTime = now

        ##################################################
        # ADD CANDIDATE
        ##################################################

        self.candidateTimes.append(
            now
        )

        ##################################################
        # REMOVE OLD CANDIDATES
        ##################################################

        self.candidateTimes = [

            timestamp

            for timestamp
            in self.candidateTimes

            if (
                now -
                timestamp
            ) <= self.clap_max_gap

        ]

        ##################################################
        # NEED TWO
        ##################################################

        if len(
            self.candidateTimes
        ) < 2:

            return False

        ##################################################
        # GAP
        ##################################################

        gap = (
            self.candidateTimes[-1]
            -
            self.candidateTimes[-2]
        )

        ##################################################
        # VALID DOUBLE CLAP
        ##################################################

        if (
            self.clap_min_gap
            <= gap
            <= self.clap_max_gap
        ):

            print(
                "[Wake] DOUBLE CLAP DETECTED"
            )

            self.candidateTimes = []

            return True

        return False

    ##################################################
    # LISTEN
    ##################################################

    def listen(self):

        self._reset()

        print(
            "[Wake] Waiting for "
            "Hey JARVIS or double clap..."
        )

        with sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            device=self.device,
            channels=self.channels,
            dtype="int16",
            callback=self._audioCallback
        ):

            while True:

                audio = (
                    self.audioQueue.get()
                )

                ##################################################
                # DOUBLE CLAP
                ##################################################

                if self._checkDoubleClap(
                    audio
                ):

                    return "CLAP"

                ##################################################
                # WAKE WORD
                ##################################################

                audio = np.asarray(
                    audio,
                    dtype=np.int16
                )

                prediction = (
                    self.model.predict(
                        audio
                    )
                )

                ##################################################
                # WAKE SCORE
                ##################################################

                for name, score in prediction.items():

                    if score >= self.wake_threshold:

                        print(
                            f"[Wake] Detected: "
                            f"{name} "
                            f"({score:.2f})"
                        )

                        self.model.reset()

                        return "WAKE"

    ##################################################
    # TEST
    ##################################################

    def test(self):

        try:

            result = self.listen()

            if result == "WAKE":

                print(
                    "[Wake] HEY JARVIS DETECTED"
                )

                return True

            if result == "CLAP":

                print(
                    "[Wake] DOUBLE CLAP DETECTED"
                )

                return True

        except KeyboardInterrupt:

            print(
                "\n[Wake] Test stopped."
            )

        except Exception as e:

            print(
                f"[Wake] Error: {e}"
            )

        return False