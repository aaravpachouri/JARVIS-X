from dataclasses import dataclass, field

from business_outreach.workflow.lead_discovery_workflow import (
    LeadDiscoveryWorkflow,
)

from business_outreach.workflow.lead_converter import (
    LeadConverter,
)

from business_outreach.database.lead_database import (
    LeadDatabase,
)

from business_outreach.qualification.website_qualifier import (
    WebsiteQualifier,
)


############################################################
# PIPELINE RESULT
############################################################

@dataclass
class LeadPipelineResult:

    discovered_count: int = 0

    converted_count: int = 0

    qualified_count: int = 0

    saved_count: int = 0

    skipped_count: int = 0

    leads: list = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )


############################################################
# LEAD PIPELINE
############################################################

class LeadPipeline:

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        discovery: LeadDiscoveryWorkflow,
        database: LeadDatabase,
        qualifier: WebsiteQualifier,
    ):

        self.discovery = discovery

        self.database = database

        self.qualifier = qualifier

        self.converter = LeadConverter()

    ########################################################
    # RUN
    ########################################################

    def run(
        self,
        location: str,
        category: str,
        keywords=None,
        limit: int = 20,
        radius_km: float | None = None,
    ) -> LeadPipelineResult:

        result = LeadPipelineResult()

        ####################################################
        # DISCOVERY
        ####################################################

        try:

            discovery_result = (
                self.discovery.discover(
                    location=location,
                    category=category,
                    keywords=keywords or [],
                    limit=limit,
                    radius_km=radius_km,
                )
            )

        except Exception as exc:

            result.errors.append(
                f"Discovery failed: {exc}"
            )

            return result

        ####################################################
        # DISCOVERY ERRORS
        ####################################################

        result.errors.extend(
            discovery_result.errors
        )

        result.discovered_count = len(
            discovery_result.discovered
        )

        ####################################################
        # CONVERSION
        ####################################################

        leads = self.converter.convert_many(
            discovery_result.discovered
        )

        result.converted_count = len(
            leads
        )

        ####################################################
        # QUALIFICATION
        ####################################################

        for lead in leads:

            try:

                qualification = (
                    self.qualifier.qualify(
                        lead
                    )
                )

            except Exception as exc:

                result.errors.append(
                    f"{lead.name}: "
                    f"qualification failed: {exc}"
                )

                result.skipped_count += 1

                continue

            ################################################
            # ONLY QUALIFIED LEADS CONTINUE
            ################################################

            if not qualification.qualified_for_outreach:

                result.skipped_count += 1

                continue

            result.qualified_count += 1

            ################################################
            # DATABASE
            ################################################

            try:

                saved = self.database.save(
                    lead
                )

            except Exception as exc:

                result.errors.append(
                    f"{lead.name}: "
                    f"database save failed: {exc}"
                )

                continue

            if saved:

                result.saved_count += 1

                result.leads.append(
                    lead
                )

            else:

                result.skipped_count += 1

        return result