from business_outreach.discovery.discovery_factory import (
    create_business_discovery,
)

from business_outreach.qualification.qualification_factory import (
    create_website_qualifier,
)

from business_outreach.models.lead import (
    WebsiteStatus,
)

from business_outreach.outreach.lead_tracker import (
    LeadTracker,
    LeadStatus,
)


############################################################
# BUSINESS OUTREACH PIPELINE
############################################################

class BusinessOutreachPipeline:

    ########################################################
    # SETTINGS
    ########################################################

    MAX_REVIEW_COUNT = 200000

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
    ):

        self.discovery = (
            create_business_discovery()
        )

        self.qualifier = (
            create_website_qualifier()
        )

        self.lead_tracker = (
            LeadTracker()
        )

    ########################################################
    # FIND CANDIDATES
    ########################################################

    def find_candidates(
        self,
        request,
    ):

        candidate_limit = max(
            1,
            int(
                request.limit
            ),
        )

        discovery_result = (
            self.discovery.search(
                request
            )
        )

        candidates = []

        rejected = []

        print(
            "\nProcessing businesses...\n"
        )

        ####################################################
        # PROCESS BUSINESSES
        ####################################################

        for lead in discovery_result.leads:

            if (
                len(candidates)
                >= candidate_limit
            ):

                print(
                    "\nCandidate limit reached."
                )

                break

            print(
                f"Checking: {lead.name}"
            )

            ################################################
            # LEAD HISTORY
            ################################################

            current_status = (
                self.lead_tracker.get_status(
                    lead
                )
            )

            if current_status != LeadStatus.NEW:

                print(
                    "  Skipped: "
                    f"Already processed "
                    f"({current_status})."
                )

                continue

            ################################################
            # PHONE
            ################################################

            if not lead.phone:

                reason = (
                    "No phone number available."
                )

                print(
                    f"  Skipped: {reason}"
                )

                self.lead_tracker.mark_skipped(
                    lead=lead,
                    reason=reason,
                )

                continue

            ################################################
            # ESTABLISHED BUSINESS
            ################################################

            if (
                lead.review_count is not None
                and
                lead.review_count
                > self.MAX_REVIEW_COUNT
            ):

                reason = (
                    f"{lead.review_count} reviews "
                    f"(too established)"
                )

                print(
                    f"  Rejected: {reason}."
                )

                self.lead_tracker.mark_rejected(
                    lead=lead,
                    status=(
                        LeadStatus
                        .REJECTED_TOO_ESTABLISHED
                    ),
                    reason=reason,
                )

                rejected.append(
                    lead
                )

                continue

            ################################################
            # WEBSITE QUALIFICATION
            ################################################

            result = (
                self.qualifier.qualify(
                    lead
                )
            )

            ################################################
            # WEBSITE FOUND
            ################################################

            if result.status in {
                WebsiteStatus.WEBSITE_LISTED,
                WebsiteStatus.WEBSITE_VERIFIED,
            }:

                reason = (
                    "Website found."
                )

                print(
                    f"  Rejected: {reason}"
                )

                self.lead_tracker.mark_rejected(
                    lead=lead,
                    status=(
                        LeadStatus
                        .REJECTED_WEBSITE
                    ),
                    reason=reason,
                )

                rejected.append(
                    lead
                )

                continue

            ################################################
            # EXPLICIT NO-WEBSITE
            ################################################

            if (
                result.status
                ==
                WebsiteStatus.NO_WEBSITE_LISTED
                and
                result.qualified_for_outreach
            ):

                print(
                    "  Candidate found."
                )

                ################################################
                # IMPORTANT:
                #
                # A valid candidate now enters the tracker.
                # This is what makes the live analytics dashboard
                # aware of newly discovered opportunities.
                ################################################

                self.lead_tracker.mark_discovered(
                    lead
                )

                candidates.append(
                    result
                )

                continue

            ################################################
            # UNKNOWN
            ################################################

            if (
                result.status
                ==
                WebsiteStatus.UNKNOWN
            ):

                print(
                    "  Not qualified: "
                    "Website status unresolved."
                )

                continue

            ################################################
            # VERIFICATION FAILED
            ################################################

            if (
                result.status
                ==
                WebsiteStatus.VERIFICATION_FAILED
            ):

                print(
                    "  Not qualified: "
                    "Website verification failed."
                )

                continue

            ################################################
            # FALLBACK
            ################################################

            print(
                "  Not qualified: "
                f"Website status = "
                f"{result.status.value}"
            )

        ####################################################
        # RETURN
        ####################################################

        return {
            "discovery_result":
                discovery_result,

            "candidates":
                candidates,

            "rejected":
                rejected,
        }


############################################################
# FACTORY
############################################################

def create_business_outreach_pipeline(
) -> BusinessOutreachPipeline:

    """
    Create the configured business-outreach pipeline.

    This is the public construction point used by
    JARVIS and other application layers.
    """

    return BusinessOutreachPipeline()