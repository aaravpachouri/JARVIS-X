from business_outreach.qualification.website_qualifier import (
    WebsiteQualifier,
)

from business_outreach.qualification.search_website_verifier import (
    SearchWebsiteVerifier,
)

from business_outreach.qualification.duckduckgo_search_provider import (
    DuckDuckGoSearchProvider,
)


def create_website_qualifier() -> WebsiteQualifier:

    search_provider = (
        DuckDuckGoSearchProvider()
    )

    verifier = (
        SearchWebsiteVerifier(
            search_provider=search_provider,
        )
    )

    qualifier = WebsiteQualifier()

    qualifier.register_provider(
        verifier
    )

    return qualifier