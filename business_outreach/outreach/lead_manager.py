from business_outreach.outreach.lead_tracker import (
    LeadTracker,
    LeadStatus,
)


############################################################
# DISPLAY LEADS
############################################################

def print_leads(
    tracker: LeadTracker,
    status=None,
):

    tracker.refresh()

    leads = tracker.get_all_records()

    found = False

    print(
        "\n" + "=" * 70
    )

    if status:

        print(
            f"{status} LEADS"
        )

    else:

        print(
            "ALL TRACKED LEADS"
        )

    print(
        "=" * 70
    )

    for lead in leads:

        lead_status = lead.get(
            "status",
            LeadStatus.NEW,
        )

        if (
            status
            and
            lead_status != status
        ):

            continue

        found = True

        print(
            f"\nBusiness: "
            f"{lead.get('name', 'Unknown')}"
        )

        print(
            "Phone:",
            lead.get(
                "phone",
                "Unknown",
            ),
        )

        print(
            "Category:",
            lead.get(
                "category",
                "Unknown",
            ),
        )

        print(
            "Status:",
            lead_status,
        )

        print(
            "Discovered:",
            lead.get(
                "discovered_at",
                "Not recorded",
            ),
        )

        print(
            "Contacted:",
            lead.get(
                "contacted_at",
                "Not contacted",
            ),
        )

        print(
            "Replied:",
            lead.get(
                "replied_at",
                "Not replied",
            ),
        )

        print(
            "Interested:",
            lead.get(
                "interested_at",
                "Not interested",
            ),
        )

        print(
            "Demo:",
            lead.get(
                "demo_sent_at",
                "Not sent",
            ),
        )

        print(
            "Client:",
            lead.get(
                "client_at",
                "Not a client",
            ),
        )

        print(
            "-" * 70
        )

    if not found:

        print(
            "\nNo leads found."
        )


############################################################
# UPDATE LEAD STATUS
############################################################

def update_lead_status(
    tracker: LeadTracker,
):

    tracker.refresh()

    leads = tracker.get_all_records()

    if not leads:

        print(
            "\nNo leads available."
        )

        return

    print(
        "\n" + "=" * 70
    )

    print(
        "SELECT LEAD"
    )

    print(
        "=" * 70
    )

    for index, lead in enumerate(
        leads,
        start=1,
    ):

        print(
            f"{index}. "
            f"{lead.get('name', 'Unknown')} "
            f"["
            f"{lead.get('status', LeadStatus.NEW)}"
            f"]"
        )

    choice = input(
        "\nSelect lead number: "
    ).strip()

    try:

        index = (
            int(choice)
            - 1
        )

        lead = leads[
            index
        ]

    except (
        ValueError,
        IndexError,
    ):

        print(
            "Invalid selection."
        )

        return

    ########################################################
    # AVAILABLE STATUSES
    ########################################################

    statuses = [

        LeadStatus.CONTACTED,

        LeadStatus.REPLIED,

        LeadStatus.INTERESTED,

        LeadStatus.DEMO_SENT,

        LeadStatus.CLIENT,

        LeadStatus.NOT_INTERESTED,

    ]

    print(
        "\nSELECT NEW STATUS"
    )

    for index, status in enumerate(
        statuses,
        start=1,
    ):

        print(
            f"{index}. {status}"
        )

    status_choice = input(
        "\nSelect status: "
    ).strip()

    try:

        status_index = (
            int(
                status_choice
            )
            - 1
        )

        new_status = (
            statuses[
                status_index
            ]
        )

    except (
        ValueError,
        IndexError,
    ):

        print(
            "Invalid status."
        )

        return

    ########################################################
    # UPDATE
    ########################################################

    success = (
        tracker.update_status_by_record(
            lead,
            new_status,
        )
    )

    if not success:

        print(
            "\nUnable to update lead."
        )

        return

    print(
        f"\nUpdated "
        f"{lead.get('name', 'Unknown')} "
        f"to {new_status}."
    )

    ########################################################
    # REFRESH
    ########################################################

    tracker.refresh()


############################################################
# SHOW SUMMARY
############################################################

def print_summary(
    tracker: LeadTracker,
):

    tracker.refresh()

    leads = tracker.get_all_records()

    counts = {}

    for lead in leads:

        status = lead.get(
            "status",
            LeadStatus.NEW,
        )

        counts[
            status
        ] = (
            counts.get(
                status,
                0,
            )
            + 1
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "LEAD DATABASE SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        f"TOTAL: {len(leads)}"
    )

    for status in (
        LeadStatus.DISCOVERED,
        LeadStatus.CONTACTED,
        LeadStatus.REPLIED,
        LeadStatus.INTERESTED,
        LeadStatus.DEMO_SENT,
        LeadStatus.CLIENT,
        LeadStatus.NOT_INTERESTED,
        LeadStatus.REJECTED_WEBSITE,
        LeadStatus.REJECTED_TOO_ESTABLISHED,
        LeadStatus.SKIPPED_NO_PHONE,
        LeadStatus.SKIPPED_MANUALLY,
        LeadStatus.SKIPPED_CONTACT_FAILED,
    ):

        print(
            f"{status}: "
            f"{counts.get(status, 0)}"
        )


############################################################
# MAIN MENU
############################################################

def main():

    tracker = LeadTracker()

    while True:

        print(
            "\n" + "=" * 70
        )

        print(
            "JARVIS BUSINESS OUTREACH"
        )

        print(
            "=" * 70
        )

        print(
            "\n1. Find new leads"
        )

        print(
            "2. View all leads"
        )

        print(
            "3. View contacted leads"
        )

        print(
            "4. View interested leads"
        )

        print(
            "5. View clients"
        )

        print(
            "6. Update lead status"
        )

        print(
            "7. Database summary"
        )

        print(
            "8. Refresh database"
        )

        print(
            "0. Exit"
        )

        choice = input(
            "\nChoose an option: "
        ).strip()

        ####################################################
        # FIND NEW LEADS
        ####################################################

        if choice == "1":

            try:

                from run_business_outreach import (
                    main as find_leads,
                )

                find_leads()

            except Exception as exc:

                print(
                    "\nUnable to run business "
                    f"outreach: {exc}"
                )

            tracker.refresh()

        ####################################################
        # VIEW ALL
        ####################################################

        elif choice == "2":

            print_leads(
                tracker
            )

        ####################################################
        # CONTACTED
        ####################################################

        elif choice == "3":

            print_leads(
                tracker,
                LeadStatus.CONTACTED,
            )

        ####################################################
        # INTERESTED
        ####################################################

        elif choice == "4":

            print_leads(
                tracker,
                LeadStatus.INTERESTED,
            )

        ####################################################
        # CLIENTS
        ####################################################

        elif choice == "5":

            print_leads(
                tracker,
                LeadStatus.CLIENT,
            )

        ####################################################
        # UPDATE STATUS
        ####################################################

        elif choice == "6":

            update_lead_status(
                tracker
            )

        ####################################################
        # SUMMARY
        ####################################################

        elif choice == "7":

            print_summary(
                tracker
            )

        ####################################################
        # REFRESH
        ####################################################

        elif choice == "8":

            tracker.refresh()

            print(
                "\nDatabase refreshed."
            )

            print(
                f"Tracked leads: "
                f"{tracker.count()}"
            )

        ####################################################
        # EXIT
        ####################################################

        elif choice == "0":

            print(
                "\nGoodbye."
            )

            break

        else:

            print(
                "\nInvalid option."
            )


############################################################
# ENTRY POINT
############################################################

if __name__ == "__main__":

    main()