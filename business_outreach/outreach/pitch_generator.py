from dataclasses import dataclass
from typing import Optional

from business_outreach.models.lead import (
    BusinessLead,
    SampleType,
)
from business_outreach.samples.sample_registry import (
    SampleRegistry,
    WebsiteSample,
)


############################################################
# PITCH RESULT
############################################################

@dataclass
class PitchResult:

    lead: BusinessLead

    message: str

    sample: Optional[WebsiteSample]

    success: bool

    reason: str = ""


############################################################
# PITCH GENERATOR
############################################################

class PitchGenerator:

    def __init__(
        self,
        sample_registry: Optional[
            SampleRegistry
        ] = None,
    ):

        self.samples = (
            sample_registry
            or SampleRegistry()
        )

    ########################################################
    # GENERATE
    ########################################################

    def generate(
        self,
        lead: BusinessLead,
    ) -> PitchResult:

        if not lead.name.strip():

            return PitchResult(
                lead=lead,
                message="",
                sample=None,
                success=False,
                reason=(
                    "Business name is required."
                ),
            )

        if not lead.phone.strip():

            return PitchResult(
                lead=lead,
                message="",
                sample=None,
                success=False,
                reason=(
                    "A public business phone number "
                    "is required before generating "
                    "an outreach draft."
                ),
            )

        ####################################################
        # WEBSITE SAFETY CHECK
        ####################################################

        if not lead.has_no_website_listed():

            return PitchResult(
                lead=lead,
                message="",
                sample=None,
                success=False,
                reason=(
                    "This lead has not been explicitly "
                    "qualified as having no website listed."
                ),
            )

        ####################################################
        # SAMPLE
        ####################################################

        sample = self.samples.find_for_business(
            category=lead.category,
            subcategory=lead.subcategory,
        )

        ####################################################
        # MESSAGE
        ####################################################

        message = self._build_message(
            lead=lead,
            sample=sample,
        )

        return PitchResult(
            lead=lead,
            message=message,
            sample=sample,
            success=True,
        )

    ########################################################
    # BUILD MESSAGE
    ########################################################

    def _build_message(
        self,
        lead: BusinessLead,
        sample: Optional[WebsiteSample],
    ) -> str:

        business_name = (
            lead.name.strip()
        )

        category = (
            lead.category.strip()
        )

        if self._is_dental(
            category,
            lead.subcategory,
        ):

            opening = (
                f"Hi, I came across "
                f"{business_name} and noticed "
                f"that your Google profile doesn't "
                f"currently list a website."
            )

            value = (
                "I create clean, professional websites "
                "for local businesses that help them "
                "look more established online and make "
                "it easier for customers to learn about "
                "their services."
            )

        elif self._is_paint_hardware(
            category,
            lead.subcategory,
        ):

            opening = (
                f"Hi, I came across "
                f"{business_name} and noticed "
                f"that your Google profile doesn't "
                f"currently list a website."
            )

            value = (
                "I create professional websites for "
                "local businesses so customers can "
                "quickly see what you offer, find "
                "your location and contact you easily."
            )

        else:

            opening = (
                f"Hi, I came across "
                f"{business_name} online and noticed "
                f"that your Google profile doesn't "
                f"currently list a website."
            )

            value = (
                "I create professional websites for "
                "local businesses to give them a "
                "stronger online presence and make it "
                "easier for potential customers to "
                "find and contact them."
            )

        lines = [
            opening,
            "",
            value,
        ]

        ####################################################
        # SAMPLE
        ####################################################

        if sample is not None:

            lines.extend(
                [
                    "",
                    (
                        "I've attached a sample of the "
                        "kind of website I can create "
                        "for a business like yours:"
                    ),
                    sample.url,
                ]
            )

        ####################################################
        # CTA
        ####################################################

        lines.extend(
            [
                "",
                (
                    "If you'd like, I can show you "
                    "what something similar could look "
                    "like for your business."
                ),
                "",
                "Would you be open to discussing it?",
            ]
        )

        return "\n".join(
            lines
        )

    ########################################################
    # DENTAL
    ########################################################

    @staticmethod
    def _is_dental(
        category: str,
        subcategory: str,
    ) -> bool:

        text = (
            f"{category} {subcategory}"
            .lower()
        )

        keywords = (
            "dentist",
            "dental",
            "orthodont",
            "tooth",
            "teeth",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    ########################################################
    # PAINT / HARDWARE
    ########################################################

    @staticmethod
    def _is_paint_hardware(
        category: str,
        subcategory: str,
    ) -> bool:

        text = (
            f"{category} {subcategory}"
            .lower()
        )

        keywords = (
            "paint",
            "hardware",
            "building material",
            "home improvement",
            "sanitary",
        )

        return any(
            keyword in text
            for keyword in keywords
        )