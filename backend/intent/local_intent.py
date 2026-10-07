import re as _re

from dataclasses import dataclass
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


##################################################
# RESULT
##################################################

@dataclass
class IntentResult:

    intent: str
    confidence: float


##################################################
# LOCAL INTENT ENGINE
##################################################

class LocalIntentEngine:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            min_df=1,
            sublinear_tf=True
        )

        self.classifier = LogisticRegression(
            max_iter=2000,
            C=8.0
        )

        ##################################################
        # TRAINING DATA
        ##################################################

        self.training_data = {

            ##################################################
            # CONVERSATION
            ##################################################

            "GREETING": [
                "hello",
                "hi",
                "hey",
                "hello jarvis",
                "hi jarvis",
                "hey jarvis",
                "good morning",
                "good afternoon",
                "good evening",
                "morning jarvis",
                "evening jarvis",
                "hello there",
                "hey there",
                "nice to see you",
                "good to have you here",
            ],

            "STATUS": [
                "how are you",
                "how r u",
                "how are u",
                "how r you",
                "how are you doing",
                "how r you doing",
                "how is everything",
                "how's everything",
                "how are things",
                "how are things going",
                "are you fine",
                "are u fine",
                "are you okay",
                "are u okay",
                "are you ok",
                "are u ok",
                "are you alright",
                "are u alright",
                "are you all right",
                "you alright",
                "you okay",
                "you ok",
                "everything okay",
                "everything ok",
                "everything good",
                "are things okay",
                "are things good",
                "you doing alright",
                "you doing okay",
                "you doing good",
            ],

            "PRESENCE": [
                "are you there",
                "are u there",
                "you there",
                "are you listening",
                "are u listening",
                "can you hear me",
                "can u hear me",
                "are you awake",
                "are u awake",
                "are you active",
                "are you online",
                "are you ready",
                "are u ready",
                "jarvis are you there",
            ],

            "IDENTITY": [
                "who are you",
                "who r you",
                "what are you",
                "what r you",
                "tell me about yourself",
                "introduce yourself",
                "what is your name",
                "whats your name",
                "who am i talking to",
                "what should i call you",
                "tell me who you are",
            ],

            "CAPABILITIES": [
                "what can you do",
                "what can u do",
                "what are your capabilities",
                "what are you capable of",
                "what can you help me with",
                "what can you help with",
                "what do you do",
                "what are your functions",
                "what features do you have",
                "what can jarvis do",
                "tell me what you can do",
                "show me your capabilities",
            ],

            "THANKS": [
                "thank you",
                "thanks",
                "thank u",
                "thanks jarvis",
                "thank you jarvis",
                "many thanks",
                "i appreciate it",
                "appreciate it",
                "that's helpful",
                "that was helpful",
            ],

            "GOODBYE": [
                "goodbye",
                "bye",
                "bye jarvis",
                "goodbye jarvis",
                "see you",
                "see you later",
                "talk to you later",
                "i am leaving",
                "go to sleep",
                "that's all",
                "we are done",
                "we're done",
            ],

            "HELP": [
                "help",
                "i need help",
                "can you help me",
                "could you help me",
                "help me jarvis",
                "what should i do",
                "i need some help",
                "assist me",
            ],

            ##################################################
            # TIME / DATE
            ##################################################

            "TIME": [
                "what time is it",
                "what is the time",
                "whats the time",
                "tell me the time",
                "tell me what time it is",
                "do you know the time",
                "current time",
                "can you tell me the time",
                "could you tell me the time",
                "what's the current time",
                "show me the time",
            ],

            "DATE": [
                "what is today's date",
                "what is todays date",
                "what's today's date",
                "whats todays date",
                "what is the date",
                "tell me the date",
                "tell me today's date",
                "what day is it",
                "what day is today",
                "today's date",
                "current date",
            ],

            ##################################################
            # APPLICATIONS
            ##################################################

            "OPEN_APP": [
                "open chrome",
                "launch chrome",
                "start chrome",
                "run chrome",
                "open google chrome",
                "launch google chrome",
                "start google chrome",
                "open calculator",
                "launch calculator",
                "start calculator",
                "open notepad",
                "launch notepad",
                "start notepad",
                "open spotify",
                "launch spotify",
                "start spotify",
                "open discord",
                "launch discord",
                "open vscode",
                "launch vscode",
                "start vscode",
            ],

            "CLOSE_APP": [
                "close chrome",
                "quit chrome",
                "exit chrome",
                "close calculator",
                "quit calculator",
                "close notepad",
                "quit notepad",
                "close spotify",
                "quit spotify",
                "close discord",
                "quit discord",
                "close vscode",
                "quit vscode",
            ],

            ##################################################
            # WEB
            ##################################################

            "OPEN_URL": [
                "open youtube",
                "open google",
                "open instagram",
                "open facebook",
                "open reddit",
                "open github",
                "open this website",
                "open this url",
                "go to youtube",
                "go to google",
                "take me to youtube",
                "take me to google",
            ],

            "SEARCH_WEB": [
                "search the web",
                "search google",
                "search for something",
                "look this up",
                "look it up",
                "search for python",
                "search for ai",
                "find this online",
                "find it online",
                "google this",
                "search the internet",
            ],

            ##################################################
            # SCREEN
            ##################################################

            "TAKE_SCREENSHOT": [
                "take a screenshot",
                "take screenshot",
                "capture my screen",
                "capture the screen",
                "screenshot this",
                "take a screen capture",
                "capture my display",
            ],

            "OCR_SCREEN": [
                "read my screen",
                "read the screen",
                "what is on my screen",
                "read what's on the screen",
                "read what is on my screen",
                "tell me what is on the screen",
                "look at my screen",
            ],

            ##################################################
            # CLIPBOARD
            ##################################################

            "READ_CLIPBOARD": [
                "read my clipboard",
                "read clipboard",
                "what is in my clipboard",
                "tell me what's copied",
                "tell me what is copied",
                "what did i copy",
            ],

            "CLEAR_CLIPBOARD": [
                "clear my clipboard",
                "clear clipboard",
                "delete my clipboard",
                "empty clipboard",
                "clear what i copied",
            ],

            ##################################################
            # KEYBOARD
            ##################################################

            "PRESS_KEY": [
                "press enter",
                "press escape",
                "press esc",
                "press tab",
                "press space",
                "press backspace",
                "press delete",
                "press shift",
                "press control",
                "press ctrl",
                "press alt",
                "press windows key",
            ],

            "HOTKEY": [
                "press ctrl c",
                "press ctrl v",
                "press ctrl x",
                "press ctrl z",
                "press ctrl a",
                "press ctrl s",
                "press ctrl shift escape",
                "use ctrl c",
                "use ctrl v",
                "hit ctrl c",
            ],

            ##################################################
            # MOUSE
            ##################################################

            "LEFT_CLICK": [
                "click",
                "left click",
                "click here",
                "click there",
                "click the button",
                "left click the button",
            ],

            "RIGHT_CLICK": [
                "right click",
                "right click here",
                "right click there",
                "right click the button",
            ],

            "DOUBLE_CLICK": [
                "double click",
                "double click here",
                "double click there",
                "double click the file",
            ],

            "SCROLL_UP": [
                "scroll up",
                "scroll upward",
                "move up the page",
                "go up the page",
                "scroll higher",
            ],

            "SCROLL_DOWN": [
                "scroll down",
                "scroll downward",
                "move down the page",
                "go down the page",
                "scroll lower",
            ],

            ##################################################
            # FILE SYSTEM
            ##################################################

            "CREATE_FOLDER": [
                "create a folder",
                "make a folder",
                "new folder",
                "create folder",
                "make me a folder",
                "create a new directory",
            ],

            "CREATE_FILE": [
                "create a file",
                "make a file",
                "new file",
                "create a new file",
                "make me a file",
            ],

            "DELETE_FILE": [
                "delete a file",
                "remove a file",
                "delete this file",
                "remove this file",
            ],

            "DELETE_FOLDER": [
                "delete a folder",
                "remove a folder",
                "delete this folder",
                "remove this folder",
            ],

            ##################################################
            # TERMINAL
            ##################################################

            "RUN_COMMAND": [
                "run a command",
                "run this command",
                "execute a command",
                "execute this command",
                "open terminal and run a command",
            ],

            "RUN_PYTHON": [
                "run python",
                "run a python script",
                "execute python",
                "execute a python script",
                "run this python script",
            ],
        }

        ##################################################
        # BUILD DATASET
        ##################################################

        texts = []
        labels = []

        for intent, examples in self.training_data.items():

            for example in examples:

                texts.append(
                    self._normalize(example)
                )

                labels.append(
                    intent
                )

        ##################################################
        # TRAIN VECTORIZER
        ##################################################

        X = self.vectorizer.fit_transform(
            texts
        )

        ##################################################
        # TRAIN CLASSIFIER
        ##################################################

        self.classifier.fit(
            X,
            labels
        )

        print(
            "[Intent] Local intent engine ready."
        )

        print(
            f"[Intent] Examples: {len(texts)}"
        )

        print(
            f"[Intent] Intents: {len(self.training_data)}"
        )

    ##################################################
    # NORMALIZE TEXT
    ##################################################

    def _normalize(
        self,
        text
    ):

        text = str(
            text
        ).lower().strip()

        ##################################################
        # REMOVE PUNCTUATION
        ##################################################

        text = _re.sub(
            r"[^\w\s]",
            " ",
            text
        )

        ##################################################
        # COLLAPSE WHITESPACE
        ##################################################

        text = _re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        ##################################################
        # COMMON SPEECH VARIATIONS
        ##################################################

        replacements = {

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

            "are u":
                "are you",

            "who r you":
                "who are you",

            "what r you":
                "what are you",

            "what can u do":
                "what can you do",

            "thank u":
                "thank you",

        }

        return replacements.get(
            text,
            text
        )

       ##################################################
    # PREDICT INTENT
    ##################################################

    def predict(
        self,
        command,
        minimum_confidence=0.72
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
        # DETERMINISTIC COMMANDS
        #
        # These prevent the ML model from getting confused
        # by an application name it has never seen before.
        ##################################################

        ##################################################
        # SCREENSHOT
        ##################################################

        screenshot_patterns = (

            "take a screenshot",
            "take screenshot",
            "capture my screen",
            "capture the screen",
            "capture my display",
            "take a screen capture",
            "screenshot this",
            "capture my screen please",
        )

        if any(
            pattern in text
            for pattern in screenshot_patterns
        ):

            intent = "TAKE_SCREENSHOT"

            confidence = 0.99

            print(
                f"[Intent] {intent} "
                f"({confidence:.2f})"
            )

            return IntentResult(
                intent=intent,
                confidence=confidence
            )

        ##################################################
        # OPEN WEBSITE
        ##################################################

        web_targets = (
            "youtube",
            "google",
            "instagram",
            "facebook",
            "reddit",
            "github",
            "twitter",
            "x.com",
            "gmail",
            "google drive",
            "google docs",
        )

        if (
            text.startswith("open ")
            or text.startswith("launch ")
            or text.startswith("go to ")
            or text.startswith("take me to ")
        ):

            for target in web_targets:

                if target in text:

                    intent = "OPEN_URL"

                    confidence = 0.99

                    print(
                        f"[Intent] {intent} "
                        f"({confidence:.2f})"
                    )

                    return IntentResult(
                        intent=intent,
                        confidence=confidence
                    )

        ##################################################
        # OPEN APPLICATION
        #
        # This deliberately accepts unknown application
        # names because AppService now performs dynamic
        # Windows application discovery.
        ##################################################

        open_prefixes = (
            "open ",
            "launch ",
            "start ",
        )

        if text.startswith(
            open_prefixes
        ):

            intent = "OPEN_APP"

            confidence = 0.98

            print(
                f"[Intent] {intent} "
                f"({confidence:.2f})"
            )

            return IntentResult(
                intent=intent,
                confidence=confidence
            )

        ##################################################
        # CLOSE APPLICATION
        ##################################################

        close_prefixes = (
            "close ",
            "quit ",
            "exit ",
        )

        if text.startswith(
            close_prefixes
        ):

            intent = "CLOSE_APP"

            confidence = 0.98

            print(
                f"[Intent] {intent} "
                f"({confidence:.2f})"
            )

            return IntentResult(
                intent=intent,
                confidence=confidence
            )

        ##################################################
        # VECTORIZE
        ##################################################

        X = self.vectorizer.transform(
            [text]
        )

        ##################################################
        # PREDICT
        ##################################################

        probabilities = (
            self.classifier.predict_proba(X)[0]
        )

        best_index = probabilities.argmax()

        confidence = float(
            probabilities[best_index]
        )

        intent = self.classifier.classes_[
            best_index
        ]

        ##################################################
        # CONFIDENCE GATE
        ##################################################

        if confidence < minimum_confidence:

            print(
                f"[Intent] UNKNOWN "
                f"(best={intent}, "
                f"confidence={confidence:.2f})"
            )

            return None

        ##################################################
        # RESULT
        ##################################################

        print(
            f"[Intent] {intent} "
            f"({confidence:.2f})"
        )

        return IntentResult(
            intent=intent,
            confidence=confidence
        )

            ##################################################
    # NORMALIZE TEXT
    ##################################################

    def _normalize(
        self,
        text
    ):

        text = str(
            text
        ).lower().strip()

        ##################################################
        # REMOVE PUNCTUATION
        ##################################################

        text = _re.sub(
            r"[^\w\s]",
            " ",
            text
        )

        ##################################################
        # COLLAPSE WHITESPACE
        ##################################################

        text = _re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        ##################################################
        # COMMON SPEECH VARIATIONS
        ##################################################

        replacements = {

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

            "are u":
                "are you",

            "who r you":
                "who are you",

            "what r you":
                "what are you",

            "what can u do":
                "what can you do",

            "thank u":
                "thank you",

        }

        text = replacements.get(
            text,
            text
        )

        ##################################################
        # NATURAL COMMAND CLEANUP
        #
        # Only remove conversational filler when the
        # sentence clearly contains an action command.
        ##################################################

        action_starters = (
            "open ",
            "launch ",
            "start ",
            "run ",
            "take ",
            "capture ",
            "read ",
            "search ",
            "find ",
            "create ",
            "make ",
            "delete ",
            "remove ",
            "close ",
            "quit ",
            "exit ",
            "press ",
            "click ",
            "scroll ",
            "clear ",
            "move ",
            "type ",
        )

        filler_prefixes = (
            "please ",
            "could you ",
            "can you ",
            "would you ",
            "will you ",
            "can u ",
            "could u ",
            "would u ",
            "please can you ",
            "please could you ",
            "hey jarvis ",
            "jarvis ",
        )

        changed = True

        while changed:

            changed = False

            for prefix in filler_prefixes:

                if text.startswith(prefix):

                    candidate = text[
                        len(prefix):
                    ].strip()

                    if candidate.startswith(
                        action_starters
                    ):

                        text = candidate

                        changed = True

                        break

        ##################################################
        # REMOVE POLITE ENDINGS
        ##################################################

        endings = (
            " please",
            " for me",
            " for me please",
        )

        for ending in endings:

            if text.endswith(ending):

                text = text[
                    :-len(ending)
                ].strip()

                break

        ##################################################
        # FINAL WHITESPACE CLEANUP
        ##################################################

        text = _re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        return text