from dataclasses import dataclass

from business_outreach.models.lead import (
    BusinessLead,
    WebsiteStatus,
)


############################################################
# QUALIFICATION RESULT
############################################################

@dataclass
class WebsiteQualificationResult:

    lead: BusinessLead

    status: WebsiteStatus

    qualified_for_outreach: bool

    reason: str

    confidence: float = 0.0

    source: str = ""

    checked_url: str = ""


############################################################
# WEBSITE QUALIFIER
############################################################

class WebsiteQualifier:

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
    ):

        self.providers = []

    ########################################################
    # PROVIDERS
    ########################################################

    def register_provider(
        self,
        provider,
    ):

        if provider is None:

            raise ValueError(
                "Website provider cannot be None."
            )

        if not hasattr(
            provider,
            "check",
        ):

            raise TypeError(
                "Website provider must implement "
                "check(lead)."
            )

        self.providers.append(
            provider
        )

    ########################################################
    # QUALIFY
    ########################################################

    def qualify(
        self,
        lead: BusinessLead,
    ) -> WebsiteQualificationResult:

        ####################################################
        # EXISTING AUTHORITATIVE WEBSITE
        ####################################################

        if lead.website_status in {
            WebsiteStatus.WEBSITE_LISTED,
            WebsiteStatus.WEBSITE_VERIFIED,
        }:

            return WebsiteQualificationResult(
                lead=lead,
                status=lead.website_status,
                qualified_for_outreach=False,
                reason=(
                    "A website is already listed "
                    "for this business."
                ),
                confidence=1.0,
                source="lead_record",
                checked_url=lead.website_url,
            )

        ####################################################
        # NO PROVIDERS
        ####################################################

        if not self.providers:

            return WebsiteQualificationResult(
                lead=lead,
                status=WebsiteStatus.UNKNOWN,
                qualified_for_outreach=False,
                reason=(
                    "Website status could not be "
                    "verified because no provider "
                    "is registered."
                ),
                confidence=0.0,
                source="none",
            )

        ####################################################
        # PROVIDER CHECKS
        ####################################################

        results = []

        for provider in self.providers:

            try:

                result = provider.check(
                    lead
                )

            except Exception as exc:

                print(
                    "[WebsiteQualifier] Provider failed:",
                    exc,
                )

                continue

            if result is None:

                continue

            results.append(
                result
            )

        ####################################################
        # NOTHING WORKED
        ####################################################

        if not results:

            return WebsiteQualificationResult(
                lead=lead,
                status=WebsiteStatus.VERIFICATION_FAILED,
                qualified_for_outreach=False,
                reason=(
                    "Website verification could "
                    "not be completed."
                ),
                confidence=0.0,
                source="verification_failed",
            )

        ####################################################
        # 1. WEBSITE DEFINITELY FOUND
        ####################################################

        for result in results:

            status = self._extract_status(
                result
            )

            if status in {
                WebsiteStatus.WEBSITE_LISTED,
                WebsiteStatus.WEBSITE_VERIFIED,
            }:

                url = self._extract_url(
                    result
                )

                lead.mark_website(
                    url=url,
                    verified=(
                        status
                        ==
                        WebsiteStatus.WEBSITE_VERIFIED
                    ),
                )

                return WebsiteQualificationResult(
                    lead=lead,
                    status=status,
                    qualified_for_outreach=False,
                    reason=(
                        "A website was found "
                        "for this business."
                    ),
                    confidence=1.0,
                    source=self._extract_source(
                        result
                    ),
                    checked_url=url,
                )

        ####################################################
        # 2. EXPLICIT NO WEBSITE
        ####################################################

        for result in results:

            status = self._extract_status(
                result
            )

            if status == WebsiteStatus.NO_WEBSITE_LISTED:

                reason = self._extract_reason(
                    result
                )

                confidence = (
                    self._extract_confidence(
                        result
                    )
                )

                lead.mark_no_website(
                    reason=reason
                )

                return WebsiteQualificationResult(
                    lead=lead,
                    status=(
                        WebsiteStatus
                        .NO_WEBSITE_LISTED
                    ),
                    qualified_for_outreach=True,
                    reason=(
                        reason
                        or
                        "No website was found "
                        "for this business."
                    ),
                    confidence=confidence,
                    source=self._extract_source(
                        result
                    ),
                )

        ####################################################
        # 3. SEARCH COMPLETED BUT RETURNED UNKNOWN
        #
        # IMPORTANT:
        #
        # A SearchWebsiteVerifier result with:
        #
        #     source = "web_search"
        #
        # and UNKNOWN means:
        #
        #     search ran,
        #     but no convincing website was matched.
        #
        # That should be treated as a candidate again.
        #
        # A genuine provider/search failure remains UNKNOWN
        # only when its source is not successful web search.
        ####################################################

        for result in results:

            status = self._extract_status(
                result
            )

            source = (
                self._extract_source(
                    result
                )
                .strip()
                .lower()
            )

            if (
                status
                ==
                WebsiteStatus.UNKNOWN
                and
                source
                ==
                "web_search"
            ):

                reason = self._extract_reason(
                    result
                )

                confidence = (
                    self._extract_confidence(
                        result
                    )
                )

                ################################################
                # Treat a completed web search with no match
                # as "no website found".
                ################################################

                lead.mark_no_website(
                    reason=reason
                )

                return WebsiteQualificationResult(
                    lead=lead,
                    status=(
                        WebsiteStatus
                        .NO_WEBSITE_LISTED
                    ),
                    qualified_for_outreach=True,
                    reason=(
                        reason
                        or
                        "Search completed but "
                        "no official website "
                        "was found."
                    ),
                    confidence=(
                        confidence
                        if confidence > 0
                        else 0.70
                    ),
                    source="web_search",
                )

        ####################################################
        # 4. UNKNOWN / UNRESOLVED
        ####################################################

        return WebsiteQualificationResult(
            lead=lead,
            status=WebsiteStatus.UNKNOWN,
            qualified_for_outreach=False,
            reason=(
                "The available information "
                "does not establish whether "
                "the business has a website."
            ),
            confidence=0.0,
            source="ambiguous",
        )

    ########################################################
    # STATUS EXTRACTION
    ########################################################

    @staticmethod
    def _extract_status(
        result,
    ) -> WebsiteStatus:

        if isinstance(
            result,
            WebsiteQualificationResult,
        ):

            return result.status

        if isinstance(
            result,
            WebsiteStatus,
        ):

            return result

        if isinstance(
            result,
            dict,
        ):

            value = result.get(
                "status"
            )

            if isinstance(
                value,
                WebsiteStatus,
            ):

                return value

            if value:

                try:

                    return WebsiteStatus(
                        value
                    )

                except ValueError:

                    pass

        return WebsiteStatus.UNKNOWN

    ########################################################
    # URL EXTRACTION
    ########################################################

    @staticmethod
    def _extract_url(
        result,
    ) -> str:

        if isinstance(
            result,
            WebsiteQualificationResult,
        ):

            return result.checked_url

        if isinstance(
            result,
            dict,
        ):

            return str(
                result.get(
                    "url",
                    "",
                )
                or ""
            ).strip()

        return ""

    ########################################################
    # REASON EXTRACTION
    ########################################################

    @staticmethod
    def _extract_reason(
        result,
    ) -> str:

        if isinstance(
            result,
            WebsiteQualificationResult,
        ):

            return result.reason

        if isinstance(
            result,
            dict,
        ):

            return str(
                result.get(
                    "reason",
                    "",
                )
                or ""
            ).strip()

        return ""

    ########################################################
    # CONFIDENCE EXTRACTION
    ########################################################

    @staticmethod
    def _extract_confidence(
        result,
    ) -> float:

        if isinstance(
            result,
            WebsiteQualificationResult,
        ):

            return max(
                0.0,
                min(
                    1.0,
                    float(
                        result.confidence
                    ),
                ),
            )

        if isinstance(
            result,
            dict,
        ):

            try:

                value = float(
                    result.get(
                        "confidence",
                        0.0,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                value = 0.0

            return max(
                0.0,
                min(
                    1.0,
                    value,
                ),
            )

        return 0.0

    ########################################################
    # SOURCE EXTRACTION
    ########################################################

    @staticmethod
    def _extract_source(
        result,
    ) -> str:

        if isinstance(
            result,
            WebsiteQualificationResult,
        ):

            return result.source

        if isinstance(
            result,
            dict,
        ):

            return str(
                result.get(
                    "source",
                    "",
                )
                or ""
            ).strip()

        return ""