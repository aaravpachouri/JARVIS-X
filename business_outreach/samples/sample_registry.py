from dataclasses import dataclass
from typing import Optional

from business_outreach.models.lead import SampleType


@dataclass(frozen=True)
class WebsiteSample:

    name: str

    sample_type: SampleType

    url: str

    description: str = ""

    keywords: tuple[str, ...] = ()


class SampleRegistry:

    def __init__(self):

        self._samples: dict[
            SampleType,
            WebsiteSample
        ] = {

            SampleType.DENTAL:
                WebsiteSample(
                    name="Bhardwaj Dental",
                    sample_type=SampleType.DENTAL,
                    url=(
                        "https://bhardwaj-dental."
                        "preview.emergentagent.com/"
                    ),
                    description=(
                        "Website sample for dental "
                        "clinics and dentists."
                    ),
                    keywords=(
                        "dentist",
                        "dental",
                        "dentist clinic",
                        "dental clinic",
                        "orthodontist",
                        "orthodontics",
                        "tooth",
                        "teeth",
                    ),
                ),

            SampleType.PAINT_HARDWARE:
                WebsiteSample(
                    name="Trusted Paint Store",
                    sample_type=(
                        SampleType.PAINT_HARDWARE
                    ),
                    url=(
                        "https://trusted-paint-store."
                        "preview.emergentagent.com/"
                    ),
                    description=(
                        "Website sample for paint, "
                        "hardware and home-improvement "
                        "businesses."
                    ),
                    keywords=(
                        "paint",
                        "hardware",
                        "paint store",
                        "hardware store",
                        "home improvement",
                        "sanitary",
                        "building materials",
                    ),
                ),
        }

    ########################################################
    # REGISTER
    ########################################################

    def register(
        self,
        sample: WebsiteSample,
    ):

        self._samples[
            sample.sample_type
        ] = sample

    ########################################################
    # GET
    ########################################################

    def get(
        self,
        sample_type: SampleType,
    ) -> Optional[WebsiteSample]:

        return self._samples.get(
            sample_type
        )

    ########################################################
    # ALL
    ########################################################

    def all(self) -> list[WebsiteSample]:

        return list(
            self._samples.values()
        )

    ########################################################
    # FIND BY CATEGORY
    ########################################################

    def find_for_business(
        self,
        category: str,
        subcategory: str = "",
    ) -> Optional[WebsiteSample]:

        text = (
            f"{category} {subcategory}"
            .lower()
            .strip()
        )

        if not text:
            return None

        for sample in self._samples.values():

            for keyword in sample.keywords:

                if keyword.lower() in text:

                    return sample

        return self.get(
            SampleType.GENERAL
        )

    ########################################################
    # FIND BY SAMPLE TYPE
    ########################################################

    def find_by_type(
        self,
        sample_type: SampleType,
    ) -> Optional[WebsiteSample]:

        return self.get(
            sample_type
        )