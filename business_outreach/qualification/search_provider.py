from abc import ABC, abstractmethod


class SearchProvider(ABC):

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return normalized search results.

        Each result should contain:

            title
            url
            snippet

        Providers must return an empty list when no
        results are available.
        """
        raise NotImplementedError