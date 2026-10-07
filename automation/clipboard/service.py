import pyperclip


class ClipboardService:

    def __init__(self):

        pass

    ##################################################
    # READ
    ##################################################

    def read(self):

        try:

            return pyperclip.paste()

        except Exception:

            return ""

    ##################################################
    # WRITE
    ##################################################

    def write(self, text):

        try:

            pyperclip.copy(text)

            return True

        except Exception:

            return False

    ##################################################
    # CLEAR
    ##################################################

    def clear(self):

        return self.write("")

    ##################################################
    # HAS TEXT
    ##################################################

    def hasText(self):

        return self.read() != ""