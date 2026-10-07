import re
import webbrowser
from urllib.parse import quote_plus

from core.actions import ActionType


class BrowserExecutor:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.search_engine = (
            "https://www.google.com/search?q="
        )

    ##################################################
    # EXECUTE
    ##################################################

    def execute(self, action):

        match action.action:

            ##################################################
            # SEARCH WEB
            ##################################################

            case ActionType.SEARCH_WEB:

                query = action.parameters.get(
                    "query",
                    ""
                )

                return self.search(
                    query
                )

            ##################################################
            # OPEN URL
            ##################################################

            case ActionType.OPEN_URL:

                url = action.parameters.get(
                    "url",
                    ""
                )

                return self.open(
                    url
                )

            ##################################################
            # UNSUPPORTED
            ##################################################

            case _:

                print(
                    f"[Browser] Unsupported action: "
                    f"{action.action.name}"
                )

                return False

    ##################################################
    # CLEAN URL
    ##################################################

    def cleanUrl(self, url):

        url = str(
            url
        ).strip()

        ##################################################
        # MARKDOWN URL
        ##################################################

        markdown = re.match(
            r"^\[([^\]]+)\]\(([^)]+)\)$",
            url
        )

        if markdown:

            url = markdown.group(
                2
            )

        ##################################################
        # REMOVE MARKDOWN BRACKETS
        ##################################################

        url = url.replace(
            "[",
            ""
        )

        url = url.replace(
            "]",
            ""
        )

        ##################################################
        # REMOVE QUOTES
        ##################################################

        url = url.strip(
            "\"'"
        ).strip()

        ##################################################
        # ADD HTTPS IF NEEDED
        ##################################################

        if url.startswith(
            "http://"
        ):

            return url

        if url.startswith(
            "https://"
        ):

            return url

        return (
            "https://"
            + url
        )

    ##################################################
    # SEARCH
    ##################################################

    def search(
        self,
        query
    ):

        query = str(
            query
        ).strip()

        if not query:

            print(
                "[Browser] Empty search query."
            )

            return False

        ##################################################
        # ENCODE QUERY PROPERLY
        ##################################################

        encoded_query = quote_plus(
            query
        )

        ##################################################
        # ALWAYS GOOGLE FOR GENERIC WEB SEARCH
        ##################################################

        url = (
            "https://www.google.com/search?q="
            + encoded_query
        )

        print()
        print(
            "[Browser] WEB SEARCH"
        )
        print(
            f"[Browser] Query: {query}"
        )
        print(
            f"[Browser] URL: {url}"
        )
        print()

        webbrowser.open(
            url,
            new=2
        )

        return True

    ##################################################
    # OPEN
    ##################################################

    def open(
        self,
        url
    ):

        url = self.cleanUrl(
            url
        )

        print(
            f"[Browser] Opening: {url}"
        )

        webbrowser.open(
            url,
            new=2
        )

        return True