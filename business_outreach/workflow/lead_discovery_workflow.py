from dataclasses import dataclass, field


############################################################
# DISCOVERY WORKFLOW RESULT
############################################################

@dataclass
class DiscoveryWorkflowResult:

    query: str

    location: str

    category: str

    discovered: list[dict] = field(
        default_factory=list
    )

    qualified: list[dict] = field(
        default_factory=list
    )

    rejected: list[dict] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    provider: str = ""

    success: bool = False


############################################################
# LEAD DISCOVERY WORKFLOW
############################################################

class LeadDiscoveryWorkflow:

    """
    Coordinates raw business discovery.

    This layer is responsible ONLY for:

        - provider execution
        - provider fallback
        - result normalization
        - deduplication
        - basic business-name validation

    Website qualification is deliberately NOT performed here.

    Website decisions belong to:

        WebsiteQualifier
            ↓
        SearchWebsiteVerifier
            ↓
        WebsiteMatcher
            ↓
        LeadPipeline

    Therefore:

        raw business with no website
            -> keep

        raw business with website
            -> keep

    The actual outreach decision is made later.
    """

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        providers=None,
    ):

        self.providers = []

        if providers:

            for provider in providers:

                self.register_provider(
                    provider
                )

    ########################################################
    # REGISTER PROVIDER
    ########################################################

    def register_provider(
        self,
        provider,
        name: str | None = None,
    ):

        if provider is None:

            raise ValueError(
                "Provider cannot be None."
            )

        if not hasattr(
            provider,
            "search",
        ):

            raise TypeError(
                "Provider must implement search()."
            )

        provider_name = (
            name
            or
            provider.__class__.__name__
        )

        self.providers.append(
            (
                provider_name,
                provider,
            )
        )

    ########################################################
    # DISCOVER
    ########################################################

    def discover(
        self,
        location: str,
        category: str,
        keywords=None,
        limit: int = 20,
        radius_km: float | None = None,
    ) -> DiscoveryWorkflowResult:

        location = str(
            location or ""
        ).strip()

        category = str(
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

        keywords = (
            list(keywords)
            if keywords is not None
            else []
        )

        limit = max(
            1,
            min(
                int(limit),
                100,
            ),
        )

        query = self._build_query(
            category,
            keywords,
        )

        result = DiscoveryWorkflowResult(
            query=query,
            location=location,
            category=category,
        )

        ####################################################
        # PROVIDER FALLBACK
        ####################################################

        for provider_name, provider in (
            self.providers
        ):

            try:

                raw_results = provider.search(
                    location=location,
                    category=category,
                    keywords=keywords,
                    limit=limit,
                    radius_km=radius_km,
                )

                if raw_results is None:

                    continue

                if not isinstance(
                    raw_results,
                    list,
                ):

                    raise TypeError(
                        "Provider returned "
                        "a non-list result."
                    )

                result.provider = (
                    provider_name
                )

                ################################################
                # DEDUPLICATE
                ################################################

                unique_results = (
                    self._deduplicate(
                        raw_results
                    )
                )

                result.discovered = (
                    unique_results[
                        :limit
                    ]
                )

                ################################################
                # BASIC VALIDATION ONLY
                ################################################

                for lead in result.discovered:

                    decision = (
                        self._qualify_basic(
                            lead
                        )
                    )

                    if decision[
                        "qualified"
                    ]:

                        result.qualified.append(
                            lead
                        )

                    else:

                        result.rejected.append(
                            {
                                "lead": lead,
                                "reason": (
                                    decision[
                                        "reason"
                                    ]
                                ),
                            }
                        )

                result.success = True

                break

            except Exception as exc:

                result.errors.append(
                    f"{provider_name}: {exc}"
                )

        ####################################################
        # NOTHING WORKED
        ####################################################

        if not result.success:

            return result

        return result

    ########################################################
    # BASIC QUALIFICATION
    #
    # IMPORTANT:
    #
    # This MUST NOT reject businesses because of website
    # presence.
    #
    # Website qualification happens later.
    ########################################################

    @staticmethod
    def _qualify_basic(
        lead: dict,
    ) -> dict:

        if not isinstance(
            lead,
            dict,
        ):

            return {
                "qualified": False,
                "reason": "Invalid business result.",
            }

        ####################################################
        # NAME REQUIRED
        ####################################################

        name = str(
            lead.get(
                "name",
                "",
            )
            or ""
        ).strip()

        if not name:

            return {
                "qualified": False,
                "reason": "Missing business name.",
            }

        ####################################################
        # KEEP THE BUSINESS
        #
        # Do NOT inspect:
        #
        #     website
        #     website_status
        #     website_url
        #
        # here.
        #
        # Those decisions happen downstream.
        ####################################################

        return {
            "qualified": True,
            "reason": (
                "Business contains the minimum "
                "identity information required "
                "for downstream qualification."
            ),
        }

    ########################################################
    # DEDUPLICATION
    ########################################################

    @staticmethod
    def _deduplicate(
        businesses: list[dict],
    ) -> list[dict]:

        unique = []

        seen_ids = set()

        seen_phones = set()

        seen_names = set()

        for business in businesses:

            if not isinstance(
                business,
                dict,
            ):

                continue

            ################################################
            # BUSINESS ID
            ################################################

            business_id = str(
                business.get(
                    "business_id",
                    "",
                )
                or ""
            ).strip()

            ################################################
            # PHONE
            ################################################

            phone = str(
                business.get(
                    "phone",
                    "",
                )
                or ""
            ).strip()

            normalized_phone = (
                "".join(
                    character
                    for character in phone
                    if character.isdigit()
                )
            )

            ################################################
            # NAME
            ################################################

            name = str(
                business.get(
                    "name",
                    "",
                )
                or ""
            ).strip().lower()

            ################################################
            # STRONG ID
            ################################################

            if business_id:

                normalized_id = (
                    business_id.lower()
                )

                if normalized_id in seen_ids:

                    continue

                seen_ids.add(
                    normalized_id
                )

                unique.append(
                    business
                )

                continue

            ################################################
            # PHONE FALLBACK
            ################################################

            if normalized_phone:

                if (
                    normalized_phone
                    in seen_phones
                ):

                    continue

                seen_phones.add(
                    normalized_phone
                )

                unique.append(
                    business
                )

                continue

            ################################################
            # NAME FALLBACK
            ################################################

            if name:

                if name in seen_names:

                    continue

                seen_names.add(
                    name
                )

                unique.append(
                    business
                )

                continue

        return unique

    ########################################################
    # QUERY
    ########################################################

    @staticmethod
    def _build_query(
        category: str,
        keywords: list[str],
    ) -> str:

        parts = [
            str(
                category or ""
            ).strip()
        ]

        for keyword in keywords:

            keyword = str(
                keyword or ""
            ).strip()

            if keyword:

                parts.append(
                    keyword
                )

        return " ".join(
            part
            for part in parts
            if part
        )