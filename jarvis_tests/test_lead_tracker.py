from business_outreach.models.lead import (
    BusinessLead,
)

from business_outreach.outreach.lead_tracker import (
    LeadTracker,
)


def main():

    tracker = LeadTracker()

    lead = BusinessLead(
        name="Test Lead Clinic",
        category="Dentist",
        phone="081308 88991",
    )

    print("\nSaving test lead...")

    tracker.mark_contacted(
        lead=lead,
        message=(
            "This is a test outreach message."
        ),
    )

    print(
        "Saved successfully."
    )

    print(
        "\nLead status:",
        tracker.get_status(lead),
    )

    print(
        "\nAll tracked leads:"
    )

    for key, data in tracker.leads.items():

        print(
            "\nKey:",
            key,
        )

        print(
            "Name:",
            data.get("name"),
        )

        print(
            "Status:",
            data.get("status"),
        )

    print(
        "\nHistory file location:"
    )

    print(
        tracker.FILE_PATH.resolve()
    )


if __name__ == "__main__":

    main()