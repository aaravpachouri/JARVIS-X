from business_outreach.models.lead import (
    BusinessLead,
    WebsiteStatus,
)

from business_outreach.qualification.search_provider import (
    SearchProvider,
)

from business_outreach.qualification.website_matcher import (
    WebsiteMatcher,
)


############################################################
# SEARCH WEBSITE VERIFIER
############################################################

class SearchWebsiteVerifier:

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        search_provider: SearchProvider,
        matcher: WebsiteMatcher | None = None,
        result_limit: int = 10,
    ):

        if search_provider is None:

            raise ValueError(
                "A search provider is required."
            )

        self.search_provider = (
            search_provider
        )

        self.matcher = (
            matcher
            or WebsiteMatcher()
        )

        self.result_limit = max(
            3,
            min(
                int(result_limit),
                20,
            ),
        )

    ########################################################
    # VERIFY
    ########################################################

    def verify(
        self,
        lead: BusinessLead,
    ) -> dict:

        ####################################################
        # INVALID LEAD
        ####################################################

        if lead is None:

            return self._unknown(
                reason="Lead is missing.",
                source="web_search",
            )

        business_name = str(
            getattr(
                lead,
                "name",
                "",
            )
        ).strip()

        if not business_name:

            return self._unknown(
                reason="Business name is missing.",
                source="web_search",
            )

        ####################################################
        # BUILD SEARCH QUERY
        ####################################################

        query = self._build_query(
            lead
        )

        ####################################################
        # SEARCH
        ####################################################

        try:

            results = (
                self.search_provider.search(
                    query=query,
                    limit=self.result_limit,
                )
            )

        except Exception as exc:

            ################################################
            # SEARCH FAILURE IS UNKNOWN
            #
            # We must NOT call this "no website".
            ################################################

            return self._unknown(
                reason=(
                    "Search provider failed: "
                    f"{exc}"
                ),
                source="search_provider",
            )

        ####################################################
        # EMPTY SEARCH
        ####################################################

        if not results:

            ################################################
            # The search completed successfully but found
            # nothing that can be associated with the
            # business.
            #
            # For outreach qualification this is treated
            # as "no website found/listed".
            ################################################

            return self._no_website(
                reason=(
                    "Search completed but no website "
                    "result was found for this business."
                ),
                confidence=0.70,
            )

        ####################################################
        # MATCH WEBSITE
        ####################################################

        try:

            match = self.matcher.match(
                business_name=business_name,
                results=results,
            )

        except Exception as exc:

            return self._unknown(
                reason=(
                    "Website matching failed: "
                    f"{exc}"
                ),
                source="website_matcher",
            )

        ####################################################
        # WEBSITE FOUND
        ####################################################

        if match.get(
            "matched",
            False,
        ):

            return {
                "status":
                    WebsiteStatus.WEBSITE_VERIFIED,

                "url":
                    str(
                        match.get(
                            "url",
                            "",
                        )
                    ).strip(),

                "reason":
                    str(
                        match.get(
                            "reason",
                            (
                                "A likely official "
                                "website was found."
                            ),
                        )
                    ),

                "confidence":
                    self._confidence(
                        match.get(
                            "confidence",
                            0.0,
                        )
                    ),

                "source":
                    "web_search",
            }

        ####################################################
        # NO WEBSITE MATCH
        #
        # IMPORTANT:
        #
        # A search that completes successfully but does not
        # produce a convincing business-domain match is
        # treated as a no-website candidate by the current
        # outreach workflow.
        ####################################################

        return self._no_website(
            reason=str(
                match.get(
                    "reason",
                    (
                        "Search completed but no "
                        "official website could be "
                        "associated with the business."
                    ),
                )
            ),
            confidence=(
                self._no_website_confidence(
                    match.get(
                        "confidence",
                        0.0,
                    )
                )
            ),
        )

    ########################################################
    # CHECK
    ########################################################

    def check(
        self,
        lead: BusinessLead,
    ) -> dict:

        return self.verify(
            lead
        )

    ########################################################
    # QUERY
    ########################################################

    @staticmethod
    def _build_query(
        lead: BusinessLead,
    ) -> str:

        parts = [
            str(
                lead.name
                or ""
            ).strip()
        ]

        city = str(
            getattr(
                lead,
                "city",
                "",
            )
            or ""
        ).strip()

        if city:

            parts.append(
                city
            )

        parts.append(
            "official website"
        )

        return " ".join(
            part
            for part in parts
            if part
        )

    ########################################################
    # NO WEBSITE RESULT
    ########################################################

    @staticmethod
    def _no_website(
        reason: str,
        confidence: float = 0.70,
    ) -> dict:

        return {
            "status":
                WebsiteStatus.NO_WEBSITE_LISTED,

            "url":
                "",

            "reason":
                reason,

            "confidence":
                max(
                    0.0,
                    min(
                        float(confidence),
                        1.0,
                    ),
                ),

            "source":
                "web_search",
        }

    ########################################################
    # UNKNOWN RESULT
    ########################################################

    @staticmethod
    def _unknown(
        reason: str,
        confidence: float = 0.0,
        source: str = "web_search",
    ) -> dict:

        return {
            "status":
                WebsiteStatus.UNKNOWN,

            "url":
                "",

            "reason":
                reason,

            "confidence":
                max(
                    0.0,
                    min(
                        float(confidence),
                        1.0,
                    ),
                ),

            "source":
                source,
        }

    ########################################################
    # CONFIDENCE
    ########################################################

    @staticmethod
    def _confidence(
        value,
    ) -> float:

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            value = 0.0

        return max(
            0.0,
            min(
                value,
                1.0,
            ),
        )

    ########################################################
    # NO-WEBSITE CONFIDENCE
    ########################################################

    @staticmethod
    def _no_website_confidence(
        value,
    ) -> float:

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            value = 0.0

        ####################################################
        # A matcher confidence describes how strongly it
        # matched something. For an unmatched result, that
        # value should not directly become "no website"
        # confidence.
        #
        # Use a conservative baseline instead.
        ####################################################

        if value <= 0:

            return 0.70

        return max(
            0.60,
            min(
                0.90,
                1.0 - value * 0.25,
            ),
        )