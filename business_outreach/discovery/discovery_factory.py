from dotenv import load_dotenv

from business_outreach.discovery.business_discovery import (
    BusinessDiscovery,
)

from business_outreach.discovery.google_business_provider import (
    GoogleBusinessProvider,
)

from business_outreach.discovery.serper_business_client import (
    SerperBusinessClient,
)


def create_business_discovery() -> BusinessDiscovery:

    load_dotenv()

    client = SerperBusinessClient()

    provider = GoogleBusinessProvider(
        client
    )

    discovery = BusinessDiscovery()

    discovery.register_provider(
        provider
    )

    return discovery