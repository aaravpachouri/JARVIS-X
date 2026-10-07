import os

import requests

from business_outreach.discovery.business_data_client import (
    BusinessDataClient,
)


class SerperBusinessClient(
    BusinessDataClient
):

    """
    Structured local-business discovery using
    Serper Places search.
    """

    ENDPOINT = (
        "https://google.serper.dev/places"
    )

    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):

        self.api_key = (
            api_key
            or os.getenv(
                "SERPER_API_KEY",
                "",
            ).strip()
        )

        self.timeout = max(
            5,
            int(timeout),
        )

    ########################################################
    # SEARCH
    ########################################################

    def search(
        self,
        location: str,
        category: str,
        keywords: list[str],
        limit: int,
        radius_km: float | None = None,
    ) -> list[dict]:

        if not self.api_key:

            raise RuntimeError(
                "SERPER_API_KEY is not configured."
            )

        if not location.strip():

            raise ValueError(
                "Business search requires a location."
            )

        if not category.strip():

            raise ValueError(
                "Business search requires a category."
            )

        limit = max(
            1,
            min(
                int(limit),
                100,
            ),
        )

        ####################################################
        # BUILD SEARCH QUERY
        ####################################################

        query_parts = [
            category.strip(),
        ]

        for keyword in keywords:

            keyword = (
                keyword or ""
            ).strip()

            if keyword:

                query_parts.append(
                    keyword
                )

        query_parts.append(
            location.strip()
        )

        query = " ".join(
            query_parts
        )

        ####################################################
        # REQUEST
        ####################################################

        headers = {
            "X-API-KEY":
                self.api_key,

            "Content-Type":
                "application/json",
        }

        payload = {
            "q": query,
            "gl": "in",
            "hl": "en",
            "num": limit,
        }

        try:

            response = requests.post(
                self.ENDPOINT,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                "Serper business search failed: "
                f"{exc}"
            ) from exc

        if not response.ok:

            raise RuntimeError(
                "Serper returned "
                f"HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        try:

            data = response.json()

        except ValueError as exc:

            raise RuntimeError(
                "Serper returned invalid JSON."
            ) from exc

        ####################################################
        # EXTRACT PLACES
        ####################################################

        places = data.get(
            "places",
            [],
        )

        if not isinstance(
            places,
            list,
        ):

            return []

        ####################################################
        # NORMALIZE RESULTS
        ####################################################

        results = []

        for place in places:

            if not isinstance(
                place,
                dict,
            ):

                continue

            name = str(
                place.get(
                    "title",
                    "",
                )
            ).strip()

            if not name:

                continue

            result = {

                "name":
                    name,

                "category":
                    str(
                        place.get(
                            "category"
                        )
                        or place.get(
                            "type"
                        )
                        or category
                    ).strip(),

                "business_id":
                    str(
                        place.get(
                            "placeId"
                        )
                        or place.get(
                            "cid"
                        )
                        or ""
                    ).strip(),

                "address":
                    str(
                        place.get(
                            "address",
                            "",
                        )
                    ).strip(),

                "latitude":
                    place.get(
                        "latitude"
                    ),

                "longitude":
                    place.get(
                        "longitude"
                    ),

                "phone":
                    str(
                        place.get(
                            "phoneNumber",
                            "",
                        )
                    ).strip(),

                "website":
                    str(
                        place.get(
                            "website",
                            "",
                        )
                    ).strip(),

                "rating":
                    place.get(
                        "rating"
                    ),

                "review_count":
                    place.get(
                        "ratingCount"
                    )
                    or place.get(
                        "reviewCount"
                    ),

            }

            results.append(
                result
            )

            if len(results) >= limit:

                break

        return results

    ########################################################
    # CONFIGURATION
    ########################################################

    def is_configured(
        self,
    ) -> bool:

        return bool(
            self.api_key
        )