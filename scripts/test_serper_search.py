from dotenv import load_dotenv

from business_outreach.discovery.serper_business_client import (
    SerperBusinessClient,
)


def main():

    load_dotenv()

    client = SerperBusinessClient()

    results = client.search(
        location="Noida",
        category="salon",
        keywords=[],
        limit=10,
    )

    print("\nRESULTS:\n")

    for index, result in enumerate(
        results,
        start=1,
    ):

        print("=" * 60)

        print(
            f"{index}. {result}"
        )

    print("=" * 60)


if __name__ == "__main__":

    main()