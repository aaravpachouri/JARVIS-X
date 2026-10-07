from business_outreach.models.lead import (
    BusinessLead,
    LeadSource,
)


class LeadConverter:

    ########################################################
    # CONVERT ONE
    ########################################################

    def convert(
        self,
        data: dict,
    ) -> BusinessLead | None:

        if not isinstance(
            data,
            dict,
        ):

            return None

        name = self._text(
            data.get("name")
        )

        if not name:

            return None

        return BusinessLead(

            name=name,

            category=self._text(
                data.get("category")
            ),

            subcategory=self._text(
                data.get("subcategory")
            ),

            business_id=self._text(
                data.get("business_id")
            ) or None,

            address=self._text(
                data.get("address")
            ),

            city=self._text(
                data.get("city")
            ),

            state=self._text(
                data.get("state")
            ),

            country=self._text(
                data.get("country")
            ) or "India",

            postal_code=self._text(
                data.get("postal_code")
            ),

            latitude=self._number(
                data.get("latitude")
            ),

            longitude=self._number(
                data.get("longitude")
            ),

            phone=self._text(
                data.get("phone")
            ),

            profile_url=self._text(
                data.get("profile_url")
            ),

            maps_url=self._text(
                data.get("maps_url")
            ),

            social_url=self._text(
                data.get("social_url")
            ),

            website_url=self._text(
                data.get("website")
                or data.get("website_url")
            ),

            rating=self._number(
                data.get("rating")
            ),

            review_count=self._integer(
                data.get("review_count")
            ),

            source=self._source(
                data.get("source")
            ),
        )

    ########################################################
    # CONVERT MANY
    ########################################################

    def convert_many(
        self,
        businesses: list[dict],
    ) -> list[BusinessLead]:

        leads = []

        for business in businesses:

            lead = self.convert(
                business
            )

            if lead is not None:

                leads.append(
                    lead
                )

        return leads

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

    ########################################################
    # SOURCE
    ########################################################

    @staticmethod
    def _source(
        value,
    ):

        if isinstance(
            value,
            LeadSource,
        ):

            return value

        if value:

            try:
                

                return LeadSource(
                    value
                )

            except ValueError:

                pass

        return LeadSource.OTHER
    
    