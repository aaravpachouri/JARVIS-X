from dataclasses import dataclass, field
from typing import Optional

from business_outreach.models.lead import (
    BusinessLead,
    LeadSource,
)


############################################################
# DISCOVERY REQUEST
############################################################

@dataclass
class DiscoveryRequest:

    location: str

    category: str = ""

    limit: int = 10

    radius_km: Optional[float] = None

    keywords: list[str] = field(
        default_factory=list
    )


############################################################
# DISCOVERY RESULT
############################################################

@dataclass
class DiscoveryResult:

    request: DiscoveryRequest

    leads: list[BusinessLead] = field(
        default_factory=list
    )

    searched: bool = False

    error: Optional[str] = None

    source: LeadSource = (
        LeadSource.GOOGLE_BUSINESS_PROFILE
    )


############################################################
# BUSINESS DISCOVERY ENGINE
############################################################

class BusinessDiscovery:

    ########################################################
    # SETTINGS
    ########################################################

    SEARCH_MULTIPLIER = 3

    MAX_SEARCH_LIMIT = 100

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(self):

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
                "Discovery provider cannot be None."
            )

        if not hasattr(
            provider,
            "search",
        ):

            raise TypeError(
                "Discovery provider must implement "
                "search(request)."
            )

        self.providers.append(
            provider
        )

    ########################################################
    # SEARCH
    ########################################################

    def search(
        self,
        request: DiscoveryRequest,
    ) -> DiscoveryResult:

        if not request.location.strip():

            return DiscoveryResult(
                request=request,
                error=(
                    "A location is required "
                    "for business discovery."
                ),
            )

        if request.limit <= 0:

            return DiscoveryResult(
                request=request,
                error=(
                    "Discovery limit must be "
                    "greater than zero."
                ),
            )

        if not self.providers:

            return DiscoveryResult(
                request=request,
                error=(
                    "No business discovery provider "
                    "has been registered."
                ),
            )

        ####################################################
        # SEARCH MORE THAN THE FINAL REQUESTED LIMIT
        #
        # Example:
        #
        # User wants: 10 businesses
        #
        # Provider searches: 30 businesses
        #
        # This gives later parts of the pipeline more
        # businesses to work with after duplicates and
        # previously processed leads are removed.
        ####################################################

        search_limit = min(
            request.limit
            * self.SEARCH_MULTIPLIER,
            self.MAX_SEARCH_LIMIT,
        )

        search_request = DiscoveryRequest(
            location=request.location,
            category=request.category,
            limit=search_limit,
            radius_km=request.radius_km,
            keywords=request.keywords,
        )

        collected = []

        seen = set()

        ####################################################
        # SEARCH PROVIDERS
        ####################################################

        for provider in self.providers:

            try:

                results = provider.search(
                    search_request
                )

            except Exception:

                continue

            if not results:

                continue

            for lead in results:

                if not isinstance(
                    lead,
                    BusinessLead,
                ):

                    continue

                key = self._identity_key(
                    lead
                )

                if key in seen:

                    continue

                seen.add(
                    key
                )

                collected.append(
                    lead
                )

                ################################################
                # IMPORTANT
                #
                # We stop at search_limit, NOT request.limit.
                #
                # The outreach pipeline can now remove old
                # leads and still have extra businesses left.
                ################################################

                if (
                    len(collected)
                    >= search_limit
                ):

                    break

            if (
                len(collected)
                >= search_limit
            ):

                break

        return DiscoveryResult(
            request=request,

            leads=collected,

            searched=True,
        )

    ########################################################
    # IDENTITY
    ########################################################

    def _identity_key(
        self,
        lead: BusinessLead,
    ) -> str:

        ####################################################
        # BEST IDENTITY
        ####################################################

        if lead.business_id:

            return (
                "business:"
                + lead.business_id.strip().lower()
            )

        ####################################################
        # PROFILE
        ####################################################

        if lead.profile_url:

            return (
                "profile:"
                + lead.profile_url.strip().lower()
            )

        ####################################################
        # PHONE
        ####################################################

        if lead.normalized_phone:

            return (
                "phone:"
                + lead.normalized_phone.strip()
            )

        ####################################################
        # FALLBACK
        ####################################################

        name = (
            lead.name
            .strip()
            .lower()
        )

        address = (
            lead.address
            .strip()
            .lower()
        )

        return (
            f"business:{name}|{address}"
        )

    ########################################################
    # SEARCH QUERY
    ########################################################

    def build_search_query(
        self,
        request: DiscoveryRequest,
    ) -> str:

        parts = []

        if request.category:

            parts.append(
                request.category.strip()
            )

        parts.extend(
            keyword.strip()
            for keyword in request.keywords
            if keyword.strip()
        )

        if not parts:

            parts.append(
                "local businesses"
            )

        parts.append(
            f"in {request.location.strip()}"
        )

        return " ".join(parts)

    ########################################################
    # TARGET DESCRIPTION
    ########################################################

    def describe_request(
        self,
        request: DiscoveryRequest,
    ) -> str:

        query = self.build_search_query(
            request
        )

        description = (
            f"Find up to {request.limit} "
            f"businesses for: {query}."
        )

        if request.radius_km is not None:

            description += (
                f" Search within approximately "
                f"{request.radius_km:g} km."
            )

        return description