from abc import ABC, abstractmethod


class BusinessDataClient(ABC):

    """
    Base interface for business-data clients.

    Any business data source used by the discovery
    system must implement the search() method.

    Examples:
        - SerperBusinessClient
        - OSMBusinessClient
        - Future API clients

    The client returns raw business dictionaries.
    The provider layer is responsible for converting
    those dictionaries into BusinessLead objects.
    """

    ########################################################
    # SEARCH
    ########################################################

    @abstractmethod
    def search(
        self,
        location: str,
        category: str,
        keywords: list[str],
        limit: int,
        radius_km: float | None = None,
    ) -> list[dict]:

        """
        Search for businesses.

        Parameters:

            location:
                Geographic location to search.

            category:
                Business category.

            keywords:
                Optional additional search terms.

            limit:
                Maximum number of results requested.

            radius_km:
                Optional search radius.

        Returns:

            A list of raw business dictionaries.

        Important:

            Implementations must only return information
            provided by their actual data source.

            Missing data must remain missing.

            Business information must never be invented.
        """

        raise NotImplementedError