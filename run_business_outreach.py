from dotenv import load_dotenv

from business_outreach.discovery.business_discovery import (
    DiscoveryRequest,
)

from business_outreach.outreach.message_generator import (
    MessageGenerator,
)

from business_outreach.outreach.whatsapp_sender import (
    WhatsAppSender,
)

from business_outreach.outreach.lead_tracker import (
    LeadTracker,
    LeadStatus,
)

from business_outreach.outreach_factory import (
    BusinessOutreachPipeline,
)


########################################################
# DISPLAY LEAD
########################################################

def display_lead(
    lead,
    qualification,
    index,
    total,
):

    print(
        "\n" + "=" * 60
    )

    print(
        f"LEAD {index} / {total}"
    )

    print(
        "=" * 60
    )

    print(
        "\nBusiness:",
        lead.name,
    )

    print(
        "Category:",
        lead.category or "Unknown",
    )

    print(
        "Phone:",
        lead.phone or "Not available",
    )

    print(
        "Address:",
        lead.address or "Not available",
    )

    print(
        "Rating:",
        lead.rating
        if lead.rating is not None
        else "Not available",
    )

    print(
        "Reviews:",
        lead.review_count
        if lead.review_count is not None
        else "Not available",
    )

    print(
        "Qualification:",
        qualification.reason,
    )


########################################################
# GET USER DECISION
########################################################

def get_user_decision():

    while True:

        choice = input(
            "\n[y] Open WhatsApp  "
            "[n] Skip  "
            "[q] Quit: "
        ).strip().lower()

        if choice in {
            "y",
            "n",
            "q",
        }:

            return choice

        print(
            "\nInvalid choice."
        )


########################################################
# MAIN
########################################################

def main():

    ####################################################
    # LOAD ENVIRONMENT
    ####################################################

    load_dotenv()

    ####################################################
    # CREATE COMPONENTS
    ####################################################

    pipeline = (
        BusinessOutreachPipeline()
    )

    message_generator = (
        MessageGenerator()
    )

    whatsapp_sender = (
        WhatsAppSender(
            dry_run=False,
        )
    )

    lead_tracker = (
        LeadTracker()
    )

    ####################################################
    # GET DISCOVERY INPUT
    ####################################################

    location = input(
        "\nEnter location: "
    ).strip()

    category = input(
        "Enter business category: "
    ).strip()

    keyword_text = input(
        "Enter additional keyword "
        "(optional): "
    ).strip()

    limit_text = input(
        "How many businesses should I check? "
    ).strip()

    ####################################################
    # CREATE KEYWORD LIST
    ####################################################

    keywords = []

    if keyword_text:

        keywords.append(
            keyword_text
        )

    ####################################################
    # CONVERT LIMIT TO INTEGER
    ####################################################

    try:

        limit = int(
            limit_text
        )

    except ValueError:

        limit = 10

        print(
            "\nInvalid number."
        )

        print(
            "Using default limit: 10"
        )

    ####################################################
    # CREATE DISCOVERY REQUEST
    ####################################################

    request = DiscoveryRequest(
        location=location,
        category=category,
        keywords=keywords,
        limit=limit,
    )

    print(
        "\nSearching for businesses...\n"
    )

    ####################################################
    # RUN PIPELINE
    ####################################################

    result = (
        pipeline.find_candidates(
            request
        )
    )

    discovery_result = (
        result["discovery_result"]
    )

    candidates = (
        result["candidates"]
    )

    rejected = (
        result["rejected"]
    )

    ####################################################
    # DISPLAY SUMMARY
    ####################################################

    print(
        "\n" + "=" * 60
    )

    print(
        "DISCOVERY SUMMARY"
    )

    print(
        "=" * 60
    )

    print(
        "Businesses discovered:",
        len(
            discovery_result.leads
        ),
    )

    print(
        "Rejected:",
        len(
            rejected
        ),
    )

    print(
        "Candidates:",
        len(
            candidates
        ),
    )

    ####################################################
    # STOP IF NO CANDIDATES
    ####################################################

    if not candidates:

        print(
            "\nNo outreach candidates found."
        )

        return

    ####################################################
    # PROCESS CANDIDATES
    ####################################################

    total = len(
        candidates
    )

    for index, qualification in enumerate(
        candidates,
        start=1,
    ):

        lead = qualification.lead

        ################################################
        # DISPLAY BUSINESS
        ################################################

        display_lead(
            lead=lead,
            qualification=qualification,
            index=index,
            total=total,
        )

        ################################################
        # GENERATE MESSAGE
        ################################################

        message = (
            message_generator.generate(
                lead
            )
        )

        print(
            "\nPERSONALIZED MESSAGE:"
        )

        print(
            "-" * 60
        )

        print(
            message
        )

        print(
            "-" * 60
        )

        ################################################
        # GET USER DECISION
        ################################################

        choice = (
            get_user_decision()
        )

        ################################################
        # QUIT SESSION
        ################################################

        if choice == "q":

            print(
                "\nStopping outreach."
            )

            break

        ################################################
        # OPEN WHATSAPP
        ################################################

        if choice == "y":

            print(
                "\nOpening WhatsApp..."
            )

            opened = (
                whatsapp_sender.send(
                    lead=lead,
                    message=message,
                )
            )

            print(
                "WhatsApp opened:",
                opened,
            )

            if opened:

                lead_tracker.mark_contacted(
                    lead=lead,
                    message=message,
                )

                print(
                    "Lead saved as CONTACTED."
                )

            else:

                lead_tracker.mark_skipped(
                    lead=lead,
                    reason=(
                        "WhatsApp could not "
                        "be opened."
                    ),
                    status=(
                        LeadStatus
                        .SKIPPED_CONTACT_FAILED
                    ),
                )

                print(
                    "Could not open WhatsApp."
                )

                print(
                    "Lead saved for tracking."
                )

        ################################################
        # SKIP LEAD MANUALLY
        ################################################

        elif choice == "n":

            lead_tracker.mark_skipped(
                lead=lead,
                reason=(
                    "Skipped manually "
                    "by user."
                ),
                status=(
                    LeadStatus
                    .SKIPPED_MANUALLY
                ),
            )

            print(
                "\nLead saved as skipped."
            )

    ####################################################
    # FINISHED
    ####################################################

    print(
        "\n" + "=" * 60
    )

    print(
        "OUTREACH SESSION FINISHED"
    )

    print(
        "=" * 60
    )


########################################################
# START PROGRAM
########################################################

if __name__ == "__main__":

    main()