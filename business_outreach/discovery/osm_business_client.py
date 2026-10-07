import time
from typing import Any

import requests

from business_outreach.discovery.business_data_client import (
    BusinessDataClient,
)


class OSMBusinessClient(BusinessDataClient):

    ########################################################
    # PUBLIC OVERPASS INSTANCES
    ########################################################

    OVERPASS_ENDPOINTS = (

        "https://overpass.private.coffee/api/interpreter",

        "https://overpass-api.de/api/interpreter",

        "https://maps.mail.ru/osm/tools/overpass/"
        "api/interpreter",
    )

    NOMINATIM_URL = (
        "https://nominatim.openstreetmap.org/search"
    )

    USER_AGENT = (
        "JARVIS-X-Business-Outreach/1.0 "
        "(local-business-discovery)"
    )

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        timeout: int = 30,
        retries: int = 2,
    ):

        self.timeout = max(
            10,
            int(timeout),
        )

        self.retries = max(
            1,
            int(retries),
        )

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": self.USER_AGENT,
                "Accept": "application/json",
            }
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

        if not location.strip():

            raise ValueError(
                "Location is required."
            )

        limit = max(
            1,
            min(
                int(limit),
                100,
            ),
        )

        ####################################################
        # GEOCODE
        ####################################################

        latitude, longitude = self._geocode(
            location
        )

        ####################################################
        # RADIUS
        ####################################################

        radius = (
            float(radius_km) * 1000
            if radius_km is not None
            else 5000.0
        )

        ####################################################
        # BUILD CATEGORY FILTERS
        ####################################################

        filters = self._build_filters(
            category=category,
            keywords=keywords,
        )

        ####################################################
        # QUERY
        ####################################################

        query = f"""
[out:json][timeout:20];

(
{self._build_query_blocks(
    filters,
    latitude,
    longitude,
    radius,
)}
);

out center tags;
"""

        ####################################################
        # EXECUTE WITH FAILOVER
        ####################################################

        data = self._execute_overpass(
            query
        )

        ####################################################
        # CONVERT
        ####################################################

        results = []

        seen = set()

        for element in data.get(
            "elements",
            [],
        ):

            result = self._convert_element(
                element
            )

            if result is None:

                continue

            identity = self._identity(
                result
            )

            if identity in seen:

                continue

            seen.add(
                identity
            )

            results.append(
                result
            )

            if len(results) >= limit:

                break

        return results

    ########################################################
    # GEOCODE
    ########################################################

    def _geocode(
        self,
        location: str,
    ) -> tuple[float, float]:

        response = self.session.get(
            self.NOMINATIM_URL,
            params={
                "q": location.strip(),
                "format": "jsonv2",
                "limit": 1,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        results = response.json()

        if not results:

            raise RuntimeError(
                f"Could not locate: {location}"
            )

        return (
            float(results[0]["lat"]),
            float(results[0]["lon"]),
        )

    ########################################################
    # FILTER DEFINITIONS
    ########################################################

    def _build_filters(
        self,
        category: str,
        keywords: list[str],
    ) -> list[str]:

        text = (
            f"{category} "
            + " ".join(keywords)
        ).lower()

        filters = []

        ####################################################
        # DENTAL
        ####################################################

        if any(
            word in text
            for word in (
                "dentist",
                "dental",
                "orthodont",
                "tooth",
                "teeth",
            )
        ):

            filters.extend(
                [
                    '[amenity=dentist]',
                    '[healthcare=dentist]',
                ]
            )

        ####################################################
        # RESTAURANT
        ####################################################

        elif "restaurant" in text:

            filters.append(
                '[amenity=restaurant]'
            )

        ####################################################
        # CAFE
        ####################################################

        elif any(
            word in text
            for word in (
                "cafe",
                "coffee",
            )
        ):

            filters.append(
                '[amenity=cafe]'
            )

        ####################################################
        # GYM
        ####################################################

        elif any(
            word in text
            for word in (
                "gym",
                "fitness",
            )
        ):

            filters.extend(
                [
                    '[leisure=fitness_centre]',
                    '[sport=fitness]',
                ]
            )

        ####################################################
        # SALON
        ####################################################

        elif "salon" in text:

            filters.extend(
                [
                    '[shop=beauty]',
                    '[shop=hairdresser]',
                ]
            )

        ####################################################
        # HARDWARE
        ####################################################

        elif "hardware" in text:

            filters.append(
                '[shop=hardware]'
            )

        ####################################################
        # PAINT
        ####################################################

        elif "paint" in text:

            filters.append(
                '[shop=paint]'
            )

        ####################################################
        # PHARMACY
        ####################################################

        elif "pharmacy" in text:

            filters.append(
                '[amenity=pharmacy]'
            )

        ####################################################
        # DOCTOR
        ####################################################

        elif any(
            word in text
            for word in (
                "doctor",
                "physician",
            )
        ):

            filters.extend(
                [
                    '[amenity=doctors]',
                    '[healthcare=doctor]',
                ]
            )

        ####################################################
        # CLINIC
        ####################################################

        elif "clinic" in text:

            filters.extend(
                [
                    '[amenity=clinic]',
                    '[healthcare=clinic]',
                ]
            )

        ####################################################
        # HOTEL
        ####################################################

        elif "hotel" in text:

            filters.append(
                '[tourism=hotel]'
            )

        ####################################################
        # BAKERY
        ####################################################

        elif "bakery" in text:

            filters.append(
                '[shop=bakery]'
            )

        ####################################################
        # GENERAL BUSINESS
        ####################################################

        if not filters:

            filters.append(
                '[name]'
            )

        return filters

    ########################################################
    # QUERY BLOCKS
    ########################################################

    @staticmethod
    def _build_query_blocks(
        filters: list[str],
        latitude: float,
        longitude: float,
        radius: float,
    ) -> str:

        blocks = []

        for osm_filter in filters:

            blocks.append(
                (
                    f"    nwr("
                    f"around:{radius},"
                    f"{latitude},"
                    f"{longitude}"
                    f"){osm_filter};"
                )
            )

        return "\n".join(
            blocks
        )

    ########################################################
    # OVERPASS EXECUTION
    ########################################################

    def _execute_overpass(
        self,
        query: str,
    ) -> dict[str, Any]:

        last_error = None

        for endpoint in self.OVERPASS_ENDPOINTS:

            for attempt in range(
                self.retries
            ):

                try:

                    response = self.session.post(
                        endpoint,
                        data={
                            "data": query,
                        },
                        timeout=self.timeout,
                    )

                    response.raise_for_status()

                    return response.json()

                except requests.RequestException as exc:

                    last_error = exc

                    if attempt + 1 < self.retries:

                        time.sleep(
                            1.5
                            * (attempt + 1)
                        )

            print(
                "[OSM] Overpass endpoint failed:"
                f" {endpoint}"
            )

        raise RuntimeError(
            "All Overpass endpoints failed. "
            f"Last error: {last_error}"
        )

    ########################################################
    # CONVERT
    ########################################################

    def _convert_element(
        self,
        element: dict,
    ) -> dict | None:

        tags = element.get(
            "tags",
            {},
        )

        name = (
            tags.get("name")
            or tags.get("brand")
        )

        if not name:

            return None

        center = element.get(
            "center",
            {},
        )

        latitude = (
            element.get("lat")
            or center.get("lat")
        )

        longitude = (
            element.get("lon")
            or center.get("lon")
        )

        ####################################################
        # CONTACT
        ####################################################

        phone = (
            tags.get("phone")
            or tags.get("contact:phone")
            or tags.get("contact:mobile")
            or ""
        )

        website = (
            tags.get("website")
            or tags.get("contact:website")
            or tags.get("url")
            or ""
        )

        ####################################################
        # CATEGORY
        ####################################################

        category = (
            tags.get("amenity")
            or tags.get("healthcare")
            or tags.get("shop")
            or tags.get("leisure")
            or tags.get("tourism")
            or ""
        )

        ####################################################
        # ADDRESS
        ####################################################

        address_parts = [

            tags.get(
                "addr:housenumber"
            ),

            tags.get(
                "addr:street"
            ),

            tags.get(
                "addr:suburb"
            ),

            tags.get(
                "addr:neighbourhood"
            ),

            tags.get(
                "addr:city"
            ),

            tags.get(
                "addr:state"
            ),

            tags.get(
                "addr:postcode"
            ),
        ]

        address = ", ".join(
            part
            for part in address_parts
            if part
        )

        ####################################################
        # ID
        ####################################################

        element_id = (
            f"{element.get('type', 'unknown')}:"
            f"{element.get('id', '')}"
        )

        ####################################################
        # MAP URL
        ####################################################

        maps_url = ""

        if (
            latitude is not None
            and
            longitude is not None
        ):

            maps_url = (
                "https://www.openstreetmap.org/"
                f"?mlat={latitude}"
                f"&mlon={longitude}"
                f"#map=19/{latitude}/{longitude}"
            )

        ####################################################
        # RESULT
        ####################################################

        return {

            "name":
                str(name).strip(),

            "category":
                str(category).strip(),

            "business_id":
                element_id,

            "address":
                address,

            "city":
                tags.get(
                    "addr:city",
                    "",
                ),

            "state":
                tags.get(
                    "addr:state",
                    "",
                ),

            "country":
                tags.get(
                    "addr:country",
                    "India",
                ),

            "postal_code":
                tags.get(
                    "addr:postcode",
                    "",
                ),

            "latitude":
                latitude,

            "longitude":
                longitude,

            "phone":
                str(phone).strip(),

            "website":
                str(website).strip(),

            "maps_url":
                maps_url,

            "profile_url":
                maps_url,

            "source":
                "openstreetmap",

            "raw_tags":
                dict(tags),
        }

    ########################################################
    # IDENTITY
    ########################################################

    @staticmethod
    def _identity(
        result: dict,
    ) -> str:

        if result.get(
            "business_id"
        ):

            return (
                "id:"
                + result["business_id"]
            )

        phone = (
            result.get(
                "phone",
                "",
            )
            .strip()
        )

        if phone:

            return (
                "phone:"
                + phone
            )

        return (
            "name:"
            + result.get(
                "name",
                "",
            ).lower()
        )