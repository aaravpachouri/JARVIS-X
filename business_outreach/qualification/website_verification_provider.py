import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from business_outreach.models.lead import (
    BusinessLead,
    WebsiteStatus,
)


############################################################
# VERIFICATION RESULT
############################################################

@dataclass
class WebsiteVerificationResult:

    status: WebsiteStatus

    url: str = ""

    reason: str = ""

    confidence: float = 0.0

    source: str = "web_check"


############################################################
# WEBSITE VERIFICATION PROVIDER
############################################################

class WebsiteVerificationProvider:

    """
    Performs a conservative website check.

    This provider does NOT claim that a business has no
    website merely because one guessed URL fails.

    It primarily checks URLs that are already associated
    with the business record and can optionally inspect
    candidate domains supplied by another discovery source.
    """

    USER_AGENT = (
        "JARVIS-X-Business-Outreach/1.0"
    )

    TIMEOUT = 10

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        timeout: int = TIMEOUT,
    ):

        self.timeout = max(
            5,
            int(timeout),
        )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent":
                    self.USER_AGENT,
                "Accept":
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8",
            }
        )

    ########################################################
    # CHECK
    ########################################################

    def check(
        self,
        lead: BusinessLead,
    ) -> WebsiteVerificationResult:

        ####################################################
        # KNOWN WEBSITE
        ####################################################

        if lead.website_url.strip():

            result = self.check_url(
                lead.website_url
            )

            if result.status in {
                WebsiteStatus.WEBSITE_LISTED,
                WebsiteStatus.WEBSITE_VERIFIED,
            }:

                return result

        ####################################################
        # NO AUTHORITATIVE URL
        ####################################################

        return WebsiteVerificationResult(
            status=WebsiteStatus.UNKNOWN,
            reason=(
                "No authoritative website URL was "
                "available to verify."
            ),
            confidence=0.0,
            source="web_check",
        )

    ########################################################
    # CHECK URL
    ########################################################

    def check_url(
        self,
        url: str,
    ) -> WebsiteVerificationResult:

        url = self._normalize_url(
            url
        )

        if not url:

            return WebsiteVerificationResult(
                status=WebsiteStatus.UNKNOWN,
                reason="Invalid website URL.",
                confidence=0.0,
                source="web_check",
            )

        try:

            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
            )

        except requests.RequestException as exc:

            return WebsiteVerificationResult(
                status=WebsiteStatus.UNKNOWN,
                url=url,
                reason=(
                    "Website could not be reached: "
                    f"{exc}"
                ),
                confidence=0.0,
                source="web_check",
            )

        ####################################################
        # SUCCESS
        ####################################################

        if 200 <= response.status_code < 400:

            return WebsiteVerificationResult(
                status=WebsiteStatus.WEBSITE_VERIFIED,
                url=response.url or url,
                reason=(
                    "Website responded successfully."
                ),
                confidence=1.0,
                source="web_check",
            )

        ####################################################
        # SERVER EXISTS BUT ACCESS FAILED
        ####################################################

        if response.status_code in {
            401,
            403,
            429,
            500,
            502,
            503,
            504,
        }:

            return WebsiteVerificationResult(
                status=WebsiteStatus.UNKNOWN,
                url=url,
                reason=(
                    "The domain may exist, but the "
                    f"website returned HTTP "
                    f"{response.status_code}."
                ),
                confidence=0.0,
                source="web_check",
            )

        ####################################################
        # NOT FOUND
        ####################################################

        return WebsiteVerificationResult(
            status=WebsiteStatus.UNKNOWN,
            url=url,
            reason=(
                f"Website returned HTTP "
                f"{response.status_code}."
            ),
            confidence=0.0,
            source="web_check",
        )

    ########################################################
    # NORMALIZE URL
    ########################################################

    @staticmethod
    def _normalize_url(
        url: str,
    ) -> str:

        url = (
            str(url or "")
            .strip()
        )

        if not url:

            return ""

        if not re.match(
            r"^https?://",
            url,
            re.IGNORECASE,
        ):

            url = (
                "https://"
                + url
            )

        parsed = urlparse(
            url
        )

        if not parsed.netloc:

            return ""

        return url