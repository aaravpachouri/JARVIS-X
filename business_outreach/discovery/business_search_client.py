import os
from typing import Any

import requests

from business_outreach.discovery.business_data_client import (
    BusinessDataClient,
)


class BusinessSearchClient(
    BusinessDataClient
):

    """
    HTTP client for the configured local-business
    search provider.

    The provider endpoint and API key are read from
    environment variables so credentials never live
    inside the JARVIS source code.
    """

    DEFAULT_TIMEOUT = 20

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):

        self.endpoint = (
            endpoint
            or os.getenv(
                "JARVIS_BUSINESS_SEARCH_URL",
                "",
            ).strip()
        )

        self.api_key = (
            api_key
            or os.getenv(
                "JARVIS_BUSINESS_SEARCH_API_KEY",
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

        if not self.endpoint:

            raise RuntimeError(
                "JARVIS_BUSINESS_SEARCH_URL is not configured."
            )

        if not location.strip():

            raise ValueError(
                "Business search requires a location."
            )

        ####################################################
        # NORMALIZE LIMIT
        ####################################################

        limit = max(
            1,
            min(
                int(limit),
                100,
            ),
        )

        ####################################################
        # BUILD REQUEST
        ####################################################

        payload = {
            "location": location.strip(),
            "category": category.strip(),
            "keywords": [
                keyword.strip()
                for keyword in keywords
                if keyword.strip()
            ],
            "limit": limit,
        }

        if radius_km is not None:

            payload[
                "radius_km"
            ] = float(
                radius_km
            )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.api_key:

            headers[
                "Authorization"
            ] = (
                f"Bearer {self.api_key}"
            )

        ####################################################
        # REQUEST
        ####################################################

        try:

            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                "Business search request failed: "
                f"{exc}"
            ) from exc

        ####################################################
        # RESPONSE CHECK
        ####################################################

        if not response.ok:

            raise RuntimeError(
                "Business search provider returned "
                f"HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        ####################################################
        # PARSE JSON
        ####################################################

        try:

            data = response.json()

        except ValueError as exc:

            raise RuntimeError(
                "Business search provider returned "
                "invalid JSON."
            ) from exc

        ####################################################
        # EXTRACT RESULTS
        ####################################################

        results = self._extract_results(
            data
        )

        ####################################################
        # DEBUG OUTPUT
        ####################################################

        print(
            "[Business Search] Requested:",
            limit,
        )

        print(
            "[Business Search] Provider returned:",
            len(results),
        )

        ####################################################
        # RETURN
        ####################################################

        return results

    ########################################################
    # RESULT EXTRACTION
    ########################################################

    def _extract_results(
        self,
        data: Any,
    ) -> list[dict]:

        if isinstance(
            data,
            list,
        ):

            return [
                item
                for item in data
                if isinstance(
                    item,
                    dict,
                )
            ]

        if not isinstance(
            data,
            dict,
        ):

            return []

        for key in (
            "results",
            "businesses",
            "places",
            "data",
            "items",
        ):

            value = data.get(
                key
            )

            if isinstance(
                value,
                list,
            ):

                return [
                    item
                    for item in value
                    if isinstance(
                        item,
                        dict,
                    )
                ]

        return []

    ########################################################
    # CONFIGURATION CHECK
    ########################################################

    def is_configured(self) -> bool:

        return bool(
            self.endpoint
        )