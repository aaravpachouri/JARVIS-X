import os
import re
import threading
import unicodedata

import numpy as np
import sounddevice as sd

from kokoro_onnx import Kokoro


############################################################
# SPEECH NORMALIZATION HELPERS
############################################################

_DIGIT_WORDS = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}

_SUPERSCRIPT_WORDS = {
    "⁰": " zero",
    "¹": " one",
    "²": " two",
    "³": " three",
    "⁴": " four",
    "⁵": " five",
    "⁶": " six",
    "⁷": " seven",
    "⁸": " eight",
    "⁹": " nine",
}

_SUBSCRIPT_WORDS = {
    "₀": " zero",
    "₁": " one",
    "₂": " two",
    "₃": " three",
    "₄": " four",
    "₅": " five",
    "₆": " six",
    "₇": " seven",
    "₈": " eight",
    "₉": " nine",
}

############################################################
# Unicode symbols that have a useful spoken meaning.
############################################################

_SYMBOL_REPLACEMENTS = (
    ("⟶", " leads to "),
    ("⟹", " leads to "),
    ("→", " leads to "),
    ("⇒", " leads to "),
    ("➜", " leads to "),
    ("➔", " leads to "),
    ("←", " from "),
    ("↔", " to and from "),
    ("⇄", " to and from "),
    ("×", " times "),
    ("÷", " divided by "),
    ("±", " plus or minus "),
    ("≈", " approximately "),
    ("≠", " not equal to "),
    ("≤", " less than or equal to "),
    ("≥", " greater than or equal to "),
    ("∞", " infinity "),
    ("°", " degrees "),
    ("•", " "),
    ("·", " "),
    ("—", " — "),
    ("–", " – "),
)

############################################################
# Characters that should simply disappear from speech.
############################################################

_SYMBOLS_TO_REMOVE = {
    "│",
    "┃",
    "━",
    "─",
    "┌",
    "┐",
    "└",
    "┘",
    "├",
    "┤",
    "┬",
    "┴",
    "┼",
    "╭",
    "╮",
    "╰",
    "╯",
    "✅",
    "☑",
    "✔",
    "❌",
    "❗",
    "❓",
    "⭐",
    "🌟",
    "💡",
    "🧠",
    "💾",
    "💻",
    "🔹",
    "🔸",
    "👉",
    "👈",
    "😊",
    "🙂",
    "😀",
    "😄",
    "😂",
    "😉",
    "😎",
    "❤️",
    "❤",
    "👍",
    "👏",
    "🏠",
    "📌",
    "📋",
    "📊",
    "🔬",
    "🧪",
    "📖",
    "🎯",
}

def _replace_unicode_symbols(
    text: str,
) -> str:

    for old, new in _SYMBOL_REPLACEMENTS:

        text = text.replace(
            old,
            new,
        )

    for symbol in _SUPERSCRIPT_WORDS:

        text = text.replace(
            symbol,
            _SUPERSCRIPT_WORDS[symbol],
        )

    for symbol in _SUBSCRIPT_WORDS:

        text = text.replace(
            symbol,
            _SUBSCRIPT_WORDS[symbol],
        )

    cleaned = []

    for char in text:

        if char in _SYMBOLS_TO_REMOVE:

            cleaned.append(" ")

            continue

        category = unicodedata.category(
            char
        )

        ####################################################
        # Remove remaining emoji / pictographic symbols.
        #
        # So UI decoration never becomes spoken content.
        ####################################################

        if category in {
            "So",
            "Sk",
        }:

            cleaned.append(" ")

            continue

        cleaned.append(
            char
        )

    return "".join(
        cleaned
    )



_ONES = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)

_TENS = (
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
)


def _integer_to_words(
    value: int,
) -> str:

    value = int(value)

    if value < 0:
        return "minus " + _integer_to_words(-value)

    if value < 20:
        return _ONES[value]

    if value < 100:
        tens, ones = divmod(value, 10)
        return _TENS[tens] + (
            f" {_ONES[ones]}" if ones else ""
        )

    if value < 1000:
        hundreds, remainder = divmod(value, 100)
        result = f"{_ONES[hundreds]} hundred"
        if remainder:
            result += f" {_integer_to_words(remainder)}"
        return result

    scales = (
        (1_000_000_000, "billion"),
        (1_000_000, "million"),
        (1_000, "thousand"),
    )

    parts = []

    remainder = value

    for scale, name in scales:
        if remainder >= scale:
            count, remainder = divmod(
                remainder,
                scale,
            )
            parts.append(
                f"{_integer_to_words(count)} {name}"
            )

    if remainder:
        parts.append(
            _integer_to_words(remainder)
        )

    return " ".join(parts)


def _spoken_decimal(
    integer_part: str,
    decimal_part: str,
) -> str:

    integer_value = int(integer_part)

    integer_words = _integer_to_words(
        integer_value
    )

    decimal_words = " ".join(
        _DIGIT_WORDS[digit]
        for digit in decimal_part
    )

    return (
        f"{integer_words} point "
        f"{decimal_words}"
    )
    
    ############################################################
# INTEGER NUMBER NORMALIZATION
############################################################

_ONES = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)

_TENS = (
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
)


def _integer_to_words(
    value: int,
) -> str:

    value = int(
        value
    )

    if value < 0:

        return (
            "minus "
            +
            _integer_to_words(
                -value
            )
        )

    if value < 20:

        return _ONES[
            value
        ]

    if value < 100:

        tens, ones = divmod(
            value,
            10
        )

        return (
            _TENS[tens]
            +
            (
                f" {_ONES[ones]}"
                if ones
                else ""
            )
        )

    if value < 1000:

        hundreds, remainder = divmod(
            value,
            100
        )

        result = (
            f"{_ONES[hundreds]} hundred"
        )

        if remainder:

            result += (
                " "
                +
                _integer_to_words(
                    remainder
                )
            )

        return result

    scales = (
        (
            1_000_000_000_000,
            "trillion",
        ),
        (
            1_000_000_000,
            "billion",
        ),
        (
            1_000_000,
            "million",
        ),
        (
            1_000,
            "thousand",
        ),
    )

    parts = []

    remainder = value

    for scale, name in scales:

        if remainder >= scale:

            count, remainder = divmod(
                remainder,
                scale
            )

            parts.append(
                f"{_integer_to_words(count)} {name}"
            )

    if remainder:

        parts.append(
            _integer_to_words(
                remainder
            )
        )

    return " ".join(
        parts
    )


def _normalize_integer_numbers(
    text: str,
) -> str:

    """
    Convert long standalone integers into natural speech.

    Examples:
        200000  -> two hundred thousand
        1200    -> one thousand two hundred
        4500000 -> four million five hundred thousand
    """

    def replacement(
        match
    ):

        raw = match.group(
            0
        )

        digits = raw.replace(
            ",",
            ""
        )

        try:

            value = int(
                digits
            )

        except ValueError:

            return raw

        # Leave short numbers alone.
        if len(digits) < 4:

            return raw

        return _integer_to_words(
            value
        )

    return re.sub(
        r"(?<![A-Za-z])"
        r"(?:\d{1,3}(?:,\d{3})+|\d{4,})"
        r"(?![A-Za-z])",
        replacement,
        text,
    )


def _normalize_decimal_numbers(
    text: str,
) -> str:

    def decimal_replacement(
        match,
    ):

        return _spoken_decimal(
            match.group(1),
            match.group(2),
        )

    text = re.sub(
        r"(?<![\w.])"
        r"(\d+)\.(\d+)"
        r"(?![\w.])",
        decimal_replacement,
        text,
    )

    return text


def _normalize_math_symbols(
    text: str,
) -> str:

    replacements = (
        ("^", " to the power of "),
        ("%", " percent "),
        ("=", " equals "),
        ("~", " approximately "),
    )

    for old, new in replacements:

        text = text.replace(
            old,
            new,
        )

    return text


def _normalize_scientific_notation(
    text: str,
) -> str:

    text = re.sub(
        r"\b10\^(\d+)\b",
        r"ten to the power of \1",
        text,
    )

    return text


def _normalize_units(
    text: str,
) -> str:

    unit_map = (
        (r"\bGB\b", " gigabytes "),
        (r"\bTB\b", " terabytes "),
        (r"\bMB\b", " megabytes "),
        (r"\bKB\b", " kilobytes "),
        (r"\bMHz\b", " megahertz "),
        (r"\bGHz\b", " gigahertz "),
        (r"\bHz\b", " hertz "),
        (r"\bkm\b", " kilometres "),
        (r"\bcm\b", " centimetres "),
        (r"\bmm\b", " millimetres "),
        (r"\bkg\b", " kilograms "),
        (r"\bmg\b", " milligrams "),
        (r"\bml\b", " millilitres "),
        (r"\bms\b", " milliseconds "),
        (r"\bμs\b", " microseconds "),
        (r"\bus\b", " microseconds "),
    )

    for pattern, replacement in unit_map:

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    return text


class TTSEngine:

    """
    JARVIS X
    NATURAL SPEECH ENGINE

    The UI may receive rich Markdown from the AI brain.

    TTS must NEVER read Markdown formatting literally.

    Example:

        **Speed**
        ### Overview
        - Fast
        [OpenAI](...)

    becomes natural speech:

        Speed
        Overview
        Fast
        OpenAI

    The original response is NOT modified for the UI.
    Only the speech representation is cleaned.
    """

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(self):

        self.lock = threading.Lock()

        self.speaking = False

        ########################################################
        # SPEECH GENERATION TOKEN
        ########################################################

        self._speech_generation = 0

        self._speech_lock = threading.Lock()

        ########################################################
        # PATHS
        ########################################################

        base_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        model_path = os.path.join(
            base_dir,
            "models",
            "kokoro",
            "kokoro-v1.0.onnx"
        )

        voices_path = os.path.join(
            base_dir,
            "models",
            "kokoro",
            "voices-v1.0.bin"
        )

        ########################################################
        # CHECK MODEL
        ########################################################

        if not os.path.exists(
            model_path
        ):

            raise FileNotFoundError(
                f"Kokoro model not found:\n{model_path}"
            )

        if not os.path.exists(
            voices_path
        ):

            raise FileNotFoundError(
                f"Kokoro voices file not found:\n{voices_path}"
            )

        ########################################################
        # LOAD KOKORO
        ########################################################

        print(
            "[TTS] Loading Kokoro neural voice..."
        )

        self.kokoro = Kokoro(
            model_path,
            voices_path
        )

        ########################################################
        # JARVIS VOICE
        ########################################################

        self.voice = "bm_fable"

        self.language = "en-gb"

        self.speed = 0.95

        print(
            f"[TTS] Voice: {self.voice}"
        )

        print(
            f"[TTS] Language: {self.language}"
        )

        print(
            "[TTS] Kokoro neural voice ready."
        )

    ############################################################
    # CLEAN FOR SPEECH
    ############################################################

    @staticmethod
    def clean_for_speech(
        text
    ):

        """
        Convert rich AI output into a speech-only representation.

        The UI keeps the original Markdown. Only the text sent to
        Kokoro is transformed.

        This layer specifically prevents:

            arrows      -> spoken "right arrow"
            emojis      -> spoken emoji names
            markdown    -> literal formatting
            LaTeX       -> literal commands
            decimals    -> misread thousands-style numbers
        """

        if text is None:

            return ""

        text = str(
            text
        ).strip()

        if not text:

            return ""

        ########################################################
        # CODE FENCES
        ########################################################

        text = re.sub(
            r"```[a-zA-Z0-9_+\-#]*",
            "",
            text,
        )

        text = text.replace(
            "```",
            "",
        )

        ########################################################
        # LINKS
        ########################################################

        text = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            text,
        )

        ########################################################
        # HEADINGS
        ########################################################

        text = re.sub(
            r"(?m)^[ \t]*#{1,6}[ \t]*",
            "",
            text,
        )

        ########################################################
        # BLOCK QUOTES
        ########################################################

        text = re.sub(
            r"(?m)^[ \t]*>[ \t]?",
            "",
            text,
        )

        ########################################################
        # BULLETS
        ########################################################

        text = re.sub(
            r"(?m)^[ \t]*[-*+][ \t]+",
            "",
            text,
        )

        ########################################################
        # NUMBERED LISTS
        ########################################################

        text = re.sub(
            r"(?m)^[ \t]*(\d+)[.)][ \t]+",
            r"\1. ",
            text,
        )

        ########################################################
        # MARKDOWN EMPHASIS
        ########################################################

        text = re.sub(
            r"(\*\*|__)(.*?)\1",
            r"\2",
            text,
            flags=re.DOTALL,
        )

        text = re.sub(
            r"~~(.*?)~~",
            r"\1",
            text,
            flags=re.DOTALL,
        )

        text = re.sub(
            r"(?<!\w)\*([^*\n]+)\*(?!\w)",
            r"\1",
            text,
        )

        text = re.sub(
            r"(?<!\w)_([^_\n]+)_(?!\w)",
            r"\1",
            text,
        )

        ########################################################
        # INLINE CODE
        ########################################################

        text = re.sub(
            r"`([^`]+)`",
            r"\1",
            text,
        )

        ########################################################
        # HTML
        ########################################################

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        ########################################################
        # Escaped markdown
        ########################################################

        for escaped, plain in (
            (r"\*", "*"),
            (r"\_", "_"),
            (r"\#", "#"),
            (r"\[", "["),
            (r"\]", "]"),
        ):

            text = text.replace(
                escaped,
                plain,
            )

        ########################################################
        # LaTeX / common scientific notation
        ########################################################

        latex_replacements = {
            r"\times": " times ",
            r"\cdot": " times ",
            r"\div": " divided by ",
            r"\pm": " plus or minus ",
            r"\approx": " approximately ",
            r"\neq": " not equal to ",
            r"\leq": " less than or equal to ",
            r"\geq": " greater than or equal to ",
            r"\rightarrow": " leads to ",
            r"\to": " to ",
            r"\alpha": " alpha ",
            r"\beta": " beta ",
            r"\gamma": " gamma ",
            r"\delta": " delta ",
            r"\sigma": " sigma ",
            r"\pi": " pi ",
        }

        for old, new in latex_replacements.items():

            text = text.replace(
                old,
                new,
            )

        text = re.sub(
            r"\\([a-zA-Z]+)",
            r"\1",
            text,
        )

        text = text.replace(
            "$$",
            "",
        )

        text = text.replace(
            "$",
            "",
        )

        ########################################################
        # Unicode symbols before generic symbol stripping.
        ########################################################

        text = _replace_unicode_symbols(
            text
        )

        ########################################################
        # Common ASCII arrows / operators.
        ########################################################

        text = text.replace(
            "=>",
            " leads to ",
        )

        text = text.replace(
            "->",
            " leads to ",
        )

        text = text.replace(
            "<-",
            " from ",
        )

        text = _normalize_math_symbols(
            text
        )

        text = _normalize_scientific_notation(
            text
        )

        text = _normalize_decimal_numbers(
            text
        )

        text = _normalize_integer_numbers(
            text
        )

        text = _normalize_units(
            text
        )

        ########################################################
        # Tables
        ########################################################

        text = re.sub(
            r"(?m)^\s*\|?[\s:|-]+\|[\s:|-]+\|?\s*$",
            "",
            text,
        )

        text = text.replace(
            "|",
            ". ",
        )

        ########################################################
        # Remove remaining visual-only markdown chars.
        ########################################################

        text = text.replace(
            "#",
            "",
        )

        text = text.replace(
            "`",
            "",
        )

        ########################################################
        # Normalize punctuation / whitespace.
        ########################################################

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n[ \t]+",
            "\n",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        text = re.sub(
            r"\.{4,}",
            "...",
            text,
        )

        text = re.sub(
            r"\?{2,}",
            "?",
            text,
        )

        text = re.sub(
            r"!{2,}",
            "!",
            text,
        )

        ########################################################
        # Remove empty lines while preserving paragraph pauses.
        ########################################################

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if line:

                lines.append(
                    line
                )

        return "\n".join(
            lines
        ).strip()

    ############################################################
    ############################################################
    # SPEAK
    ############################################################

    @staticmethod
    def _speech_chunks(
        text,
        max_chars=420,
    ):

        """
        Split speech into natural sentence/paragraph chunks.

        This lets JARVIS begin speaking before an entire long
        response is synthesized, while keeping each Kokoro input
        comfortably bounded.
        """

        text = str(
            text or ""
        ).strip()

        if not text:

            return []

        paragraphs = re.split(
            r"\n{2,}",
            text,
        )

        chunks = []

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:

                continue

            sentences = re.split(
                r"(?<=[.!?])\s+",
                paragraph,
            )

            current = ""

            for sentence in sentences:

                sentence = sentence.strip()

                if not sentence:

                    continue

                candidate = (
                    f"{current} {sentence}"
                    .strip()
                )

                if (
                    current
                    and
                    len(candidate)
                    >
                    max_chars
                ):

                    chunks.append(
                        current
                    )

                    current = sentence

                else:

                    current = candidate

            if current:

                chunks.append(
                    current
                )

        return [
            chunk.strip()
            for chunk in chunks
            if chunk.strip()
        ]

    ############################################################
    # SPEAK
    ############################################################

    def speak(
        self,
        text
    ):

        if not text:

            return

        original_text = str(
            text
        ).strip()

        if not original_text:

            return

        speech_text = (
            self.clean_for_speech(
                original_text
            )
        )

        if not speech_text:

            return

        chunks = self._speech_chunks(
            speech_text
        )

        if not chunks:

            return

        with self._speech_lock:

            generation = (
                self._speech_generation
            )

        with self.lock:

            try:

                self.speaking = True

                for index, chunk in enumerate(
                    chunks,
                    start=1,
                ):

                    ################################################
                    # Check cancellation before every synthesis.
                    ################################################

                    with self._speech_lock:

                        cancelled = (
                            generation
                            !=
                            self._speech_generation
                        )

                    if cancelled:

                        print(
                            "[TTS] "
                            "Speech queue discarded after stop."
                        )

                        return

                    print(
                        "[JARVIS:TTS] "
                        f"{chunk}"
                    )

                    ################################################
                    # Generate one bounded chunk.
                    ################################################

                    samples, sample_rate = (
                        self.kokoro.create(
                            chunk,
                            voice=self.voice,
                            speed=self.speed,
                            lang=self.language
                        )
                    )

                    ################################################
                    # Cancellation can happen while Kokoro is
                    # generating. Discard stale audio.
                    ################################################

                    with self._speech_lock:

                        cancelled = (
                            generation
                            !=
                            self._speech_generation
                        )

                    if cancelled:

                        print(
                            "[TTS] "
                            "Generated speech discarded after stop."
                        )

                        return

                    audio = np.asarray(
                        samples,
                        dtype=np.float32
                    )

                    sd.play(
                        audio,
                        sample_rate
                    )

                    sd.wait()

                    ################################################
                    # Stop between chunks if interrupted.
                    ################################################

                    with self._speech_lock:

                        cancelled = (
                            generation
                            !=
                            self._speech_generation
                        )

                    if cancelled:

                        sd.stop()

                        print(
                            "[TTS] "
                            "Speech queue cancelled."
                        )

                        return

            except Exception as e:

                print(
                    f"[TTS] Error: {e}"
                )

            finally:

                self.speaking = False

    ############################################################
    ############################################################
    # SPEAK CLEAN
    ############################################################

    def speak_clean(
        self,
        text
    ):

        """
        Explicit alias for callers that want to make it clear
        they are sending rich AI text that should be converted
        into natural speech.
        """

        self.speak(
            text
        )

    ############################################################
    # STOP
    ############################################################

    def stop(
        self
    ):

        try:

            with self._speech_lock:

                self._speech_generation += 1

            sd.stop()

            self.speaking = False

            print(
                "[TTS] Speech cancelled."
            )

        except Exception as e:

            print(
                f"[TTS] Stop error: {e}"
            )

    ############################################################
    # IS SPEAKING
    ############################################################

    def is_speaking(
        self
    ):

        return bool(
            self.speaking
        )

    ############################################################
    # REPRESENTATION
    ############################################################

    def __repr__(
        self
    ):

        return (
            "<TTSEngine "
            f"voice={self.voice!r} "
            f"language={self.language!r} "
            f"speaking={self.speaking}>"
        )