import re


from business_outreach.models.lead import (
    BusinessLead,
)

from business_outreach.discovery.business_source import (
    BusinessSource,
)

from business_outreach.qualification.search_provider import (
    SearchProvider,
)


class SearchBusinessSource(
    BusinessSource
):

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        search_provider: SearchProvider,
    ):

        if search_provider is None:

            raise ValueError(
                "A search provider is required."
            )

        self.search_provider = (
            search_provider
        )

    ########################################################
    # SEARCH
    ########################################################

    def search(
        self,
        location: str,
        category: str,
        limit: int = 20,
    ) -> list[BusinessLead]:

        location = (
            location or ""
        ).strip()

        category = (
            category or ""
        ).strip()

        if not location:

            raise ValueError(
                "Location is required."
            )

        if not category:

            raise ValueError(
                "Category is required."
            )

        limit = max(
            1,
            min(
                int(limit),
                50,
            ),
        )

        ####################################################
        # MULTIPLE DISCOVERY QUERIES
        #
        # One search query can fail or return poor results.
        # We try several natural variations.
        ####################################################

        queries = self._build_queries(
            location=location,
            category=category,
        )

        all_results = []

        ####################################################
        # SEARCH EACH QUERY SAFELY
        ####################################################

        for query in queries:

            try:

                results = (
                    self.search_provider.search(
                        query=query,
                        limit=20,
                    )
                )

                if results:

                    all_results.extend(
                        results
                    )

            except Exception as exc:

                print(
                    "[Discovery] Query failed:",
                    query,
                )

                print(
                    "[Discovery] Error:",
                    exc,
                )

                # One failed query should NOT
                # destroy the whole discovery process.
                continue

        ####################################################
        # EXTRACT LEADS
        ####################################################

        leads = []

        seen_names = set()

        for result in all_results:

            if not isinstance(
                result,
                dict,
            ):

                continue

            name = self._extract_name(
                result=result,
                category=category,
                location=location,
            )

            if not name:

                continue

            key = self._normalize(
                name
            )

            if not key:

                continue

            if key in seen_names:

                continue

            seen_names.add(
                key
            )

            lead = BusinessLead(
                name=name,
                category=category,
            )

            leads.append(
                lead
            )

            if len(leads) >= limit:

                break

        return leads

    ########################################################
    # BUILD QUERIES
    ########################################################

    @staticmethod
    def _build_queries(
        location: str,
        category: str,
    ) -> list[str]:

        queries = [

            f"{category} {location}",

            f"{category} in {location}",

            f"{category} near {location}",

        ]

        ####################################################
        # CATEGORY VARIATIONS
        #
        # Example:
        #
        # dentist
        # → dental clinic
        # → dental care
        ####################################################

        category_lower = (
            category.lower()
            .strip()
        )

        variations = {

            "dentist": [
                "dental clinic",
                "dental care",
            ],

            "gym": [
                "fitness centre",
                "fitness center",
            ],

            "restaurant": [
                "cafe",
                "food restaurant",
            ],

            "salon": [
                "beauty salon",
                "hair salon",
            ],

            "doctor": [
                "medical clinic",
                "clinic",
            ],

        }

        for variation in variations.get(
            category_lower,
            [],
        ):

            queries.append(
                f"{variation} {location}"
            )

        ####################################################
        # REMOVE DUPLICATES
        ####################################################

        unique_queries = []

        seen = set()

        for query in queries:

            key = query.lower().strip()

            if key in seen:

                continue

            seen.add(
                key
            )

            unique_queries.append(
                query
            )

        return unique_queries

    ########################################################
    # EXTRACT BUSINESS NAME
    ########################################################

    def _extract_name(
        self,
        result: dict,
        category: str,
        location: str,
    ) -> str:

        title = str(
            result.get(
                "title",
                "",
            )
        ).strip()

        url = str(
            result.get(
                "url",
                "",
            )
        ).strip()

        if not title:

            return ""

        if self._is_bad_result(
            title=title,
            url=url,
        ):

            return ""

        name = self._clean_title(
            title
        )

        if not name:

            return ""

        if self._looks_like_category_page(
            name=name,
            category=category,
            location=location,
        ):

            return ""

        return name

    ########################################################
    # CLEAN TITLE
    ########################################################

    @staticmethod
    def _clean_title(
        title: str,
    ) -> str:

        title = re.sub(
            r"\s+",
            " ",
            title,
        ).strip()

        separators = (

            " | ",
            " – ",
            " — ",

        )

        for separator in separators:

            if separator in title:

                title = (
                    title.split(
                        separator,
                        1,
                    )[0]
                )

        return title.strip()

    ########################################################
    # REJECT BAD RESULTS
    ########################################################

    @staticmethod
    def _is_bad_result(
        title: str,
        url: str,
    ) -> bool:

        text = (
            f"{title} {url}"
        ).lower()

        blocked_domains = (

            "google.com",
            "bing.com",
            "duckduckgo.com",

            "justdial.com",
            "sulekha.com",
            "yelp.com",
            "practo.com",

            "facebook.com",
            "instagram.com",
            "linkedin.com",

            "wikipedia.org",

        )

        if any(
            domain in text
            for domain in blocked_domains
        ):

            return True

        blocked_phrases = (

            "contact us",
            "contact:",
            "login",
            "sign in",
            "business icons",
            "symbols",
            "near me",
            "list of",
            "find a",
            "search for",

        )

        title_lower = (
            title.lower()
        )

        return any(
            phrase in title_lower
            for phrase in blocked_phrases
        )

    ########################################################
    # CATEGORY PAGE DETECTION
    ########################################################

    def _looks_like_category_page(
        self,
        name: str,
        category: str,
        location: str,
    ) -> bool:

        text = self._normalize(
            name
        )

        generic_patterns = (

            f"{category.lower()} in",

            f"{category.lower()} near",

            "best dentists",
            "best dentist",
            "top dentists",
            "top dentist",

        )

        return any(
            pattern in text
            for pattern in generic_patterns
        )

    ########################################################
    # NORMALIZE
    ########################################################

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        words = re.findall(
            r"[a-z0-9@]+",
            text.lower(),
        )

        return " ".join(
            words
        )