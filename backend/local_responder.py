import re
from datetime import datetime


class LocalResponder:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        ##################################################
        # EXACT / NORMALIZED RESPONSES
        ##################################################

        self.responses = {

            ##################################################
            # GREETINGS
            ##################################################

            "hello":
                "Hello, sir.",

            "hi":
                "Hello, sir.",

            "hey":
                "Hello, sir.",

            "good morning":
                "Good morning, sir. All systems are operational.",

            "good afternoon":
                "Good afternoon, sir.",

            "good evening":
                "Good evening, sir.",

            ##################################################
            # STATUS
            ##################################################

            "how are you":
                "I'm operating perfectly, sir. Thank you for asking.",

            "how are you doing":
                "I'm doing very well, sir.",

            "how are things":
                "Everything is operating smoothly, sir.",

            "how is everything":
                "Everything is operating smoothly, sir.",

            "are you fine":
                "I'm perfectly fine, sir.",

            "are you okay":
                "I'm perfectly fine, sir.",

            "are you ok":
                "I'm perfectly fine, sir.",

            "are you alright":
                "I'm perfectly fine, sir.",

            "are you all right":
                "I'm perfectly fine, sir.",

            "everything okay":
                "Everything is operating normally, sir.",

            "everything ok":
                "Everything is operating normally, sir.",

            ##################################################
            # PRESENCE
            ##################################################

            "are you there":
                "Always, sir.",

            "are you listening":
                "I'm listening, sir.",

            "are you ready":
                "Always ready, sir.",

            ##################################################
            # IDENTITY
            ##################################################

            "who are you":
                "I am JARVIS, your personal AI assistant.",

            "what are you":
                "I'm JARVIS, an intelligent personal assistant designed to help you.",

            "introduce yourself":
                "I am JARVIS. I'm here and ready to assist you, sir.",

            ##################################################
            # SIMPLE SPEECH
            ##################################################

            "say hello":
                "Hello, sir. It's good to hear from you.",

            "say hi":
                "Hello, sir.",

            ##################################################
            # POLITENESS
            ##################################################

            "thank you":
                "You're welcome, sir.",

            "thanks":
                "My pleasure, sir.",

            ##################################################
            # CAPABILITIES
            ##################################################

            "what can you do":
                "I can control applications, browse the web, manage files, interact with your computer, read your screen, and assist you with tasks, sir.",
        }

    ##################################################
    # NORMALIZE
    ##################################################

    def _normalize(self, text):

        text = str(
            text
        ).lower().strip()

        ##################################################
        # PUNCTUATION
        ##################################################

        text = re.sub(
            r"[^\w\s]",
            " ",
            text
        )

        ##################################################
        # MULTIPLE SPACES
        ##################################################

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        ##################################################
        # SPEECH-TO-TEXT VARIATIONS
        ##################################################

        replacements = {

            # How are you
            "how r u":
                "how are you",

            "how r you":
                "how are you",

            "how are u":
                "how are you",

            "how r u doing":
                "how are you doing",

            "how r you doing":
                "how are you doing",

            # Are you okay
            "are u fine":
                "are you fine",

            "are u okay":
                "are you okay",

            "are u ok":
                "are you ok",

            "are u alright":
                "are you alright",

            # Presence
            "are u there":
                "are you there",

            "are u listening":
                "are you listening",

            "are u ready":
                "are you ready",

            # Identity
            "who r you":
                "who are you",

            "what r you":
                "what are you",

            # Capabilities
            "what can u do":
                "what can you do",

            # Thanks
            "thank u":
                "thank you",
        }

        return replacements.get(
            text,
            text
        )

    ##################################################
    # REMOVE JARVIS PREFIX
    ##################################################

    def _removeJarvisPrefix(
        self,
        text
    ):

        prefixes = (

            "hey jarvis ",

            "jarvis ",

            "hey jarvis",

            "jarvis",

        )

        for prefix in prefixes:

            if text.startswith(prefix):

                text = text[
                    len(prefix):
                ].strip()

                break

        return text

    ##################################################
    # STATUS INTENT
    ##################################################

    def _isStatusQuestion(
        self,
        text
    ):

        patterns = (

            r"^how (are|r) (you|u)$",

            r"^how (are|r) (you|u) doing$",

            r"^how('?s| is) everything$",

            r"^how are things$",

            r"^are you (fine|okay|ok|alright)$",

            r"^are u (fine|okay|ok|alright)$",

            r"^you (fine|okay|ok|alright)$",

            r"^everything (okay|ok)$",

        )

        for pattern in patterns:

            if re.match(
                pattern,
                text
            ):

                return True

        return False

    ##################################################
    # PRESENCE INTENT
    ##################################################

    def _isPresenceQuestion(
        self,
        text
    ):

        patterns = (

            r"^are you there$",

            r"^are u there$",

            r"^are you listening$",

            r"^are u listening$",

            r"^are you ready$",

            r"^are u ready$",

        )

        for pattern in patterns:

            if re.match(
                pattern,
                text
            ):

                return True

        return False

    ##################################################
    # TIME INTENT
    ##################################################

    def _isTimeQuestion(
        self,
        text
    ):

        patterns = (

            r"^what time is it$",

            r"^what is the time$",

            r"^whats the time$",

            r"^what's the time$",

            r"^tell me the time$",

            r"^tell me what time it is$",

            r"^current time$",

            r"^do you know the time$",

        )

        for pattern in patterns:

            if re.match(
                pattern,
                text
            ):

                return True

        return False

    ##################################################
    # DATE INTENT
    ##################################################

    def _isDateQuestion(
        self,
        text
    ):

        patterns = (

            r"^what is (today'?s|todays) date$",

            r"^what's (today'?s|todays) date$",

            r"^whats (today'?s|todays) date$",

            r"^what is the date$",

            r"^tell me the date$",

            r"^tell me today's date$",

        )

        for pattern in patterns:

            if re.match(
                pattern,
                text
            ):

                return True

        return False

    ##################################################
    # RESPOND
    ##################################################

    def respond(
        self,
        command
    ):

        if not command:

            return None

        ##################################################
        # NORMALIZE
        ##################################################

        text = self._normalize(
            command
        )

        if not text:

            return None

        ##################################################
        # REMOVE JARVIS
        ##################################################

        text = self._removeJarvisPrefix(
            text
        )

        ##################################################
        # NORMALIZE AGAIN
        ##################################################

        text = self._normalize(
            text
        )

        ##################################################
        # EXACT RESPONSE
        ##################################################

        response = self.responses.get(
            text
        )

        if response:

            return response

        ##################################################
        # STATUS
        ##################################################

        if self._isStatusQuestion(
            text
        ):

            return (
                "I'm operating perfectly, sir. "
                "Thank you for asking."
            )

        ##################################################
        # PRESENCE
        ##################################################

        if self._isPresenceQuestion(
            text
        ):

            if (
                "listening"
                in text
            ):

                return (
                    "I'm listening, sir."
                )

            if (
                "ready"
                in text
            ):

                return (
                    "Always ready, sir."
                )

            return (
                "Always, sir."
            )

        ##################################################
        # TIME
        ##################################################

        if self._isTimeQuestion(
            text
        ):

            current_time = datetime.now().strftime(
                "%I:%M %p"
            )

            return (
                f"The current time is "
                f"{current_time}, sir."
            )

        ##################################################
        # DATE
        ##################################################

        if self._isDateQuestion(
            text
        ):

            current_date = datetime.now().strftime(
                "%A, %d %B %Y"
            )

            return (
                f"Today is "
                f"{current_date}, sir."
            )

        ##################################################
        # UNKNOWN
        ##################################################

        return None