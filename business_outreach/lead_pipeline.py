from business_outreach.models.lead import (
    BusinessLead,
    WebsiteStatus,
)

from business_outreach.qualification.website_qualifier import (
    WebsiteQualifier,
)

from business_outreach.qualification.search_website_verifier import (
    SearchWebsiteVerifier,
)

from business_outreach.qualification.duckduckgo_search_provider import (
    DuckDuckGoSearchProvider,
)

from business_outreach.outreach.lead_tracker import (
    LeadTracker,
    LeadStatus,
)


############################################################
# LEAD PIPELINE
############################################################

class LeadPipeline:

    """
    Website qualification pipeline.

    Rules:

        WEBSITE_LISTED / WEBSITE_VERIFIED
            -> confirmed website
            -> reject

        NO_WEBSITE_LISTED
            -> outreach opportunity
            -> record as discovered

        UNKNOWN
            -> treat as candidate
            -> do not permanently reject

        VERIFICATION_FAILED
            -> treat as candidate
            -> do not permanently reject

    LeadTracker remains the persistence layer.
    """

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
    ):

        ####################################################
        # WEBSITE QUALIFIER
        ####################################################

        self.website_qualifier = (
            WebsiteQualifier()
        )

        ####################################################
        # SEARCH PROVIDER
        ####################################################

        self.search_provider = (
            DuckDuckGoSearchProvider()
        )

        ####################################################
        # WEBSITE SEARCH VERIFIER
        ####################################################

        self.search_website_verifier = (
            SearchWebsiteVerifier(
                search_provider=self.search_provider
            )
        )

        ####################################################
        # REGISTER PROVIDER
        ####################################################

        self.website_qualifier.register_provider(
            self.search_website_verifier
        )

        ####################################################
        # LEAD TRACKER
        ####################################################

        self.lead_tracker = (
            LeadTracker()
        )

    ########################################################
    # CHECK IF ALREADY PROCESSED
    ########################################################

    def is_already_processed(
        self,
        lead: BusinessLead,
    ) -> bool:

        return self.lead_tracker.exists(
            lead
        )

    ########################################################
    # QUALIFY LEAD
    ########################################################

    def qualify(
        self,
        lead: BusinessLead,
    ):

        ####################################################
        # INVALID
        ####################################################

        if lead is None:

            return None

        ####################################################
        # HISTORY
        ####################################################

        if self.is_already_processed(
            lead
        ):

            print(
                "[Lead Pipeline] Skipping already "
                f"processed business: {lead.name}"
            )

            return None

        ####################################################
        # WEBSITE QUALIFICATION
        ####################################################

        try:

            result = (
                self.website_qualifier.qualify(
                    lead
                )
            )

        except Exception as exc:

            ################################################
            # Qualification failure must not destroy a
            # potentially useful outreach opportunity.
            ################################################

            print(
                "[Lead Pipeline] Website "
                f"qualification failed: {exc}"
            )

            print(
                "[Lead Pipeline] Treating as candidate:"
                f" {lead.name}"
            )

            self.lead_tracker.mark_discovered(
                lead
            )

            return lead

        ####################################################
        # NO RESULT
        ####################################################

        if result is None:

            print(
                "[Lead Pipeline] No qualification result."
            )

            print(
                "[Lead Pipeline] Treating as candidate:"
                f" {lead.name}"
            )

            self.lead_tracker.mark_discovered(
                lead
            )

            return lead

        ####################################################
        # CONFIRMED WEBSITE
        ####################################################

        if result.status in {
            WebsiteStatus.WEBSITE_LISTED,
            WebsiteStatus.WEBSITE_VERIFIED,
        }:

            reason = (
                result.reason
                or
                "Website found."
            )

            print(
                "[Lead Pipeline] Rejected: "
                f"{lead.name} — {reason}"
            )

            self.lead_tracker.mark_rejected(
                lead=lead,
                status=(
                    LeadStatus.REJECTED_WEBSITE
                ),
                reason=reason,
            )

            return result

        ####################################################
        # CONFIRMED NO WEBSITE
        ####################################################

        if (
            result.status
            ==
            WebsiteStatus.NO_WEBSITE_LISTED
        ):

            print(
                "[Lead Pipeline] Opportunity found: "
                f"{lead.name}"
            )

            self.lead_tracker.mark_discovered(
                lead
            )

            return result

        ####################################################
        # UNKNOWN
        #
        # IMPORTANT:
        #
        # UNKNOWN does NOT mean the business has a website.
        # Therefore it remains a usable candidate.
        ####################################################

        if (
            result.status
            ==
            WebsiteStatus.UNKNOWN
        ):

            print(
                "[Lead Pipeline] Website status "
                f"unresolved: {lead.name}"
            )

            print(
                "[Lead Pipeline] Candidate found."
            )

            self.lead_tracker.mark_discovered(
                lead
            )

            return result

        ####################################################
        # VERIFICATION FAILED
        #
        # Also keep it as an opportunity rather than
        # throwing it away.
        ####################################################

        if (
            result.status
            ==
            WebsiteStatus.VERIFICATION_FAILED
        ):

            print(
                "[Lead Pipeline] Website verification "
                f"failed: {lead.name}"
            )

            print(
                "[Lead Pipeline] Candidate found."
            )

            self.lead_tracker.mark_discovered(
                lead
            )

            return result

        ####################################################
        # SAFETY FALLBACK
        ####################################################

        print(
            "[Lead Pipeline] Unhandled website status: "
            f"{result.status}"
        )

        print(
            "[Lead Pipeline] Treating as candidate."
        )

        self.lead_tracker.mark_discovered(
            lead
        )

        return result