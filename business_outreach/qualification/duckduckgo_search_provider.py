from business_outreach.qualification.search_provider import (
    SearchProvider,
)


class DuckDuckGoSearchProvider(SearchProvider):

    def __init__(
        self,
        max_results: int = 10,
    ):

        self.max_results = max(
            1,
            min(
                int(max_results),
                20,
            ),
        )

    ########################################################
    # SEARCH
    ########################################################

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:

        if not query.strip():

            return []

        limit = max(
            1,
            min(
                int(limit),
                self.max_results,
            ),
        )

        try:

            from ddgs import DDGS

        except ImportError:

            raise RuntimeError(
                "DDGS is not installed. "
                "Run: python -m pip install ddgs"
            )

        results = []

        with DDGS() as search:

            for item in search.text(
                query,
                max_results=limit,
            ):

                if not isinstance(
                    item,
                    dict,
                ):

                    continue

                url = str(
                    item.get(
                        "href",
                        "",
                    )
                ).strip()

                if not url:

                    continue

                results.append(
                    {
                        "title": str(
                            item.get(
                                "title",
                                "",
                            )
                        ).strip(),

                        "url": url,

                        "snippet": str(
                            item.get(
                                "body",
                                "",
                            )
                        ).strip(),
                    }
                )

        return results