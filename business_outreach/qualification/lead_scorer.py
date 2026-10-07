from business_outreach.models.lead import (
    BusinessLead,
    WebsiteStatus,
)


class LeadScorer:

    ########################################################
    # SCORE
    ########################################################

    def score(
        self,
        lead: BusinessLead,
        qualification,
    ) -> int:

        score = 0

        ####################################################
        # WEBSITE OPPORTUNITY
        ####################################################

        if qualification.status == WebsiteStatus.UNKNOWN:

            score += 40

        ####################################################
        # PHONE AVAILABLE
        ####################################################

        if lead.phone:

            score += 25

        ####################################################
        # REVIEW COUNT
        ####################################################

        reviews = lead.review_count or 0

        if reviews >= 500:

            score += 20

        elif reviews >= 100:

            score += 15

        elif reviews >= 20:

            score += 10

        elif reviews > 0:

            score += 5

        ####################################################
        # RATING
        ####################################################

        rating = lead.rating or 0

        if rating >= 4.5:

            score += 15

        elif rating >= 4.0:

            score += 10

        elif rating >= 3.5:

            score += 5

        ####################################################
        # LIMIT SCORE
        ####################################################

        return min(
            score,
            100,
        )

    ########################################################
    # PRIORITY
    ########################################################

    @staticmethod
    def priority(
        score: int,
    ) -> str:

        if score >= 80:

            return "HIGH PRIORITY"

        if score >= 60:

            return "GOOD LEAD"

        return "LOW PRIORITY"