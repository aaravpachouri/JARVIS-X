from typing import Any

from business_outreach.discovery.business_discovery import (
    DiscoveryRequest,
)
from business_outreach.models.lead import (
    BusinessLead,
    LeadSource,
    WebsiteStatus,
)


class GoogleBusinessProvider:

    """
    Business discovery provider.

    This class is deliberately kept behind a provider
    interface so the rest of JARVIS does not depend on
    how business data is obtained.

    A real provider implementation can later use:
        - an official business API
        - an approved connected service
        - another structured business-data source

    It must return BusinessLead objects and must never
    invent missing business information.
    """

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        client=None,
    ):

        self.client = client

    ########################################################
    # SEARCH
    ########################################################

    def search(
        self,
        request: DiscoveryRequest,
    ) -> list[BusinessLead]:

        if self.client is None:

            raise RuntimeError(
                "GoogleBusinessProvider has no configured "
                "business-data client."
            )

        raw_results = self.client.search(
            location=request.location,
            category=request.category,
            keywords=request.keywords,
            limit=request.limit,
            radius_km=request.radius_km,
        )

        if not raw_results:

            return []

        leads = []

        for result in raw_results:

            lead = self._convert_result(
                result
            )

            if lead is not None:

                leads.append(
                    lead
                )

            if len(leads) >= request.limit:

                break

        return leads

    ########################################################
    # CONVERT RESULT
    ########################################################

    def _convert_result(
        self,
        result: Any,
    ) -> BusinessLead | None:

        if not isinstance(
            result,
            dict,
        ):

            return None

        name = self._text(
            result.get("name")
        )

        if not name:

            return None

        lead = BusinessLead(
            name=name,

            category=self._text(
                result.get("category")
                or result.get("primary_category")
            ),

            subcategory=self._text(
                result.get("subcategory")
            ),

            business_id=self._text(
                result.get("business_id")
                or result.get("place_id")
                or result.get("id")
            )
            or None,

            address=self._text(
                result.get("address")
            ),

            city=self._text(
                result.get("city")
            ),

            state=self._text(
                result.get("state")
            ),

            country=self._text(
                result.get("country")
            )
            or "India",

            postal_code=self._text(
                result.get("postal_code")
            ),

            latitude=self._number(
                result.get("latitude")
            ),

            longitude=self._number(
                result.get("longitude")
            ),

            phone=self._text(
                result.get("phone")
                or result.get("phone_number")
            ),

            profile_url=self._text(
                result.get("profile_url")
            ),

            maps_url=self._text(
                result.get("maps_url")
                or result.get("google_maps_url")
            ),

            social_url=self._text(
                result.get("social_url")
            ),

            website_url=self._text(
                result.get("website")
                or result.get("website_url")
            ),

            website_status=(
           WebsiteStatus.WEBSITE_LISTED
                if self._text(
                result.get("website")
                or result.get("website_url")
            )
            else WebsiteStatus.UNKNOWN
            ),

            rating=self._number(
                result.get("rating")
            ),

            review_count=self._integer(
                result.get("review_count")
                or result.get("reviews")
            ),

            source=LeadSource.GOOGLE_BUSINESS_PROFILE,
        )

        return lead

    ########################################################
    # TEXT
    ########################################################

    @staticmethod
    def _text(
        value,
    ) -> str:

        if value is None:

            return ""

        return str(
            value
        ).strip()

    ########################################################
    # NUMBER
    ########################################################

    @staticmethod
    def _number(
        value,
    ):

        if value is None:

            return None

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    ########################################################
    # INTEGER
    ########################################################

    @staticmethod
    def _integer(
        value,
    ):

        if value is None:

            return None

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None