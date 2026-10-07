from abc import (
    ABC,
    abstractmethod,
)

from business_outreach.models.lead import (
    BusinessLead,
)


class BusinessSource(
    ABC
):

    ########################################################
    # SEARCH
    ########################################################

    @abstractmethod
    def search(
        self,
        location: str,
        category: str,
        limit: int = 20,
    ) -> list[BusinessLead]:

        raise NotImplementedError