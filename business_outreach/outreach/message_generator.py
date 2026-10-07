from business_outreach.models.lead import (
    BusinessLead,
)


class MessageGenerator:

    ########################################################
    # GENERATE MESSAGE
    ########################################################

    def generate(
        self,
        lead: BusinessLead,
    ) -> str:

        name = (
            lead.name
            or "your business"
        ).strip()

        category = (
            lead.category
            or "business"
        ).strip().lower()

        review_count = (
            lead.review_count
            or 0
        )

        ####################################################
        # PERSONALIZATION
        ####################################################

        opportunity = (
            self._get_opportunity(
                review_count
            )
        )

        benefit = (
            self._get_benefit(
                category
            )
        )

        ####################################################
        # FINAL MESSAGE
        ####################################################

        return (
            f"Hi! 👋\n\n"

            f"I came across {name} while looking at "
            f"local businesses in the area.\n\n"

            f"I noticed that {opportunity}.\n\n"

            f"I had an idea for a modern website designed "
            f"specifically for {name}, where customers could "
            f"{benefit}.\n\n"

            f"I actually have a few ideas for how it could "
            f"look for your business. Would you be open to "
            f"seeing a quick concept? 🙂"
        )

    ########################################################
    # REVIEW-BASED OPPORTUNITY
    ########################################################

    @staticmethod
    def _get_opportunity(
        review_count: int,
    ) -> str:

        if review_count >= 1000:

            return (
                "you already have a very strong local "
                "presence with a large number of reviews"
            )

        if review_count >= 300:

            return (
                "you have already built a strong reputation "
                "among local customers"
            )

        if review_count >= 100:

            return (
                "your business has built a good reputation "
                "among local customers"
            )

        if review_count > 0:

            return (
                "your business is building a presence among "
                "local customers"
            )

        return (
            "there seems to be a good opportunity to "
            "strengthen your online presence"
        )

    ########################################################
    # CATEGORY-SPECIFIC BENEFIT
    ########################################################

    @staticmethod
    def _get_benefit(
        category: str,
    ) -> str:

        category = (
            category
            or ""
        ).lower()

        if (
            "eye" in category
            or "optical" in category
            or "ophthalm" in category
        ):

            return (
                "explore eye-care services, book appointments, "
                "find the location, or contact you directly"
            )

        if (
            "dental" in category
            or "dentist" in category
        ):

            return (
                "explore treatments, book appointments, "
                "find your location, or contact you directly"
            )

        if (
            "salon" in category
            or "beauty" in category
            or "hair" in category
        ):

            return (
                "explore your services, see your work, "
                "and contact you easily"
            )

        if (
            "gym" in category
            or "fitness" in category
        ):

            return (
                "explore your facilities, services, "
                "and membership options"
            )

        if (
            "restaurant" in category
            or "food" in category
            or "dhaba" in category
        ):

            return (
                "explore your menu, find your location, "
                "and contact you easily"
            )

        if (
            "cafe" in category
            or "coffee" in category
        ):

            return (
                "explore your menu, find your location, "
                "and discover what makes your place unique"
            )

        if (
            "clinic" in category
            or "medical" in category
            or "doctor" in category
            or "physio" in category
        ):

            return (
                "explore your services, book appointments, "
                "find your location, or contact you directly"
            )

        if (
            "vet" in category
            or "veterinary" in category
            or "pet" in category
        ):

            return (
                "explore your services and easily contact "
                "you when they need help"
            )

        return (
            "learn about your services, understand what "
            "you offer, and contact you easily"
        )