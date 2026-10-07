from dataclasses import dataclass
from urllib.parse import urlparse
import re

import requests

from business_outreach.models.lead import (
    BusinessLead,
    WebsiteStatus,
)


############################################################
# RESULT
############################################################

@dataclass
class WebSearchVerificationResult:

    status: WebsiteStatus

    url: str = ""

    reason: str = ""

    confidence: float = 0.0

    source: str = "web_search"


############################################################
# WEB SEARCH VERIFIER
############################################################

class WebSearchVerifier:

    """
    Conservative second-stage website verification.

    It searches for a business using its name and location,
    then evaluates candidate result URLs.

    It does NOT claim that a website does not exist merely
    because a search returned nothing.
    """

    SEARCH_URL = (
        "https://www.google.com/search"
    )

    USER_AGENT = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/149.0 Safari/537.36"
    )

    def __init__(
        self,
        timeout: int = 10,
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
    ) -> WebSearchVerificationResult:

        if not lead.name.strip():

            return WebSearchVerificationResult(
                status=WebsiteStatus.UNKNOWN,
                reason=(
                    "Business name is required."
                ),
            )

        query = self._build_query(
            lead
        )

        try:

            response = self.session.get(
                self.SEARCH_URL,
                params={
                    "q": query,
                    "num": 10,
                },
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.RequestException as exc:

            return WebSearchVerificationResult(
                status=WebsiteStatus.UNKNOWN,
                reason=(
                    "Web search could not be completed: "
                    f"{exc}"
                ),
                confidence=0.0,
            )

        html = response.text

        candidates = (
            self._extract_urls(
                html
            )
        )

        ####################################################
        # MATCH OFFICIAL-LOOKING SITE
        ####################################################

        for url in candidates:

            if self._looks_like_business_site(
                url,
                lead,
            ):

                return WebSearchVerificationResult(
                    status=WebsiteStatus.WEBSITE_VERIFIED,
                    url=url,
                    reason=(
                        "A candidate business website "
                        "was found through web search."
                    ),
                    confidence=0.75,
                    source="web_search",
                )

        ####################################################
        # SEARCH COMPLETED BUT NO SITE
        ####################################################

        if candidates:

            return WebSearchVerificationResult(
                status=WebsiteStatus.UNKNOWN,
                reason=(
                    "Search completed, but no candidate "
                    "website could be confidently associated "
                    "with this business."
                ),
                confidence=0.0,
                source="web_search",
            )

        ####################################################
        # NO RESULTS
        ####################################################

        return WebSearchVerificationResult(
            status=WebsiteStatus.UNKNOWN,
            reason=(
                "No usable web result was found. "
                "This does not prove that the business "
                "has no website."
            ),
            confidence=0.0,
            source="web_search",
        )

    ########################################################
    # QUERY
    ########################################################

    @staticmethod
    def _build_query(
        lead: BusinessLead,
    ) -> str:

        parts = [
            f'"{lead.name.strip()}"'
        ]

        if lead.city.strip():

            parts.append(
                f'"{lead.city.strip()}"'
            )

        elif lead.address.strip():

            parts.append(
                f'"{lead.address.strip()}"'
            )

        if lead.category.strip():

            parts.append(
                f'"{lead.category.strip()}"'
            )

        return " ".join(
            parts
        )

    ########################################################
    # EXTRACT URLS
    ########################################################

    @staticmethod
    def _extract_urls(
        html: str,
    ) -> list[str]:

        urls = []

        pattern = re.compile(
            r'https?://[^\s"<>]+',
            re.IGNORECASE,
        )

        for match in pattern.findall(
            html
        ):

            url = (
                match
                .rstrip(
                    '.,);\'"'
                )
            )

            if url not in urls:

                urls.append(
                    url
                )

        return urls

    ########################################################
    # BUSINESS SITE CHECK
    ########################################################

    @staticmethod
    def _looks_like_business_site(
        url: str,
        lead: BusinessLead,
    ) -> bool:

        try:

            parsed = urlparse(
                url
            )

        except Exception:

            return False

        domain = (
            parsed.netloc
            .lower()
            .replace(
                "www.",
                "",
            )
        )

        if not domain:

            return False

        ####################################################
        # IGNORE SEARCH / SOCIAL / DIRECTORY SITES
        ####################################################

        blocked_domains = {
            "google.com",
            "google.co.in",
            "maps.google.com",
            "facebook.com",
            "instagram.com",
            "youtube.com",
            "linkedin.com",
            "justdial.com",
            "yelp.com",
            "tripadvisor.com",
            "sulekha.com",
            "indiamart.com",
        }

        if any(
            domain == blocked
            or domain.endswith(
                "." + blocked
            )
            for blocked in blocked_domains
        ):

            return False

        ####################################################
        # DOMAIN NAME MATCH
        ####################################################

        business_words = re.findall(
            r"[a-z0-9]+",
            lead.name.lower(),
        )

        meaningful_words = [
            word
            for word in business_words
            if len(word) >= 4
        ]

        if not meaningful_words:

            return False

        matches = sum(
            1
            for word in meaningful_words
            if word in domain
        )

        return matches >= 1