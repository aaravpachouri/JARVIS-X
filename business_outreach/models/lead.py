from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


############################################################
# WEBSITE STATUS
############################################################

class WebsiteStatus(Enum):

    UNKNOWN = "unknown"

    NO_WEBSITE_LISTED = "no_website_listed"

    WEBSITE_LISTED = "website_listed"

    WEBSITE_VERIFIED = "website_verified"

    VERIFICATION_FAILED = "verification_failed"


############################################################
# LEAD STATUS
############################################################

class LeadStatus(Enum):

    NEW = "new"

    DISCOVERED = "discovered"

    QUALIFIED = "qualified"

    REJECTED = "rejected"

    DUPLICATE = "duplicate"

    PITCH_READY = "pitch_ready"

    AWAITING_APPROVAL = "awaiting_approval"

    APPROVED = "approved"

    SKIPPED = "skipped"

    CONTACTED = "contacted"

    REPLIED = "replied"

    INTERESTED = "interested"

    NOT_INTERESTED = "not_interested"

    FAILED = "failed"


############################################################
# OUTREACH STATUS
############################################################

class OutreachStatus(Enum):

    NOT_STARTED = "not_started"

    DRAFTED = "drafted"

    AWAITING_APPROVAL = "awaiting_approval"

    APPROVED = "approved"

    PREPARED = "prepared"

    SENT = "sent"

    FAILED = "failed"

    SKIPPED = "skipped"


############################################################
# SOURCE TYPE
############################################################

class LeadSource(Enum):

    GOOGLE_BUSINESS_PROFILE = "google_business_profile"

    GOOGLE_SEARCH = "google_search"

    MANUAL = "manual"

    OTHER = "other"


############################################################
# SAMPLE TYPE
############################################################

class SampleType(Enum):

    DENTAL = "dental"

    PAINT_HARDWARE = "paint_hardware"

    RESTAURANT = "restaurant"

    CAFE = "cafe"

    GYM = "gym"

    SALON = "salon"

    REAL_ESTATE = "real_estate"

    RETAIL = "retail"

    GENERAL = "general"

    NONE = "none"


############################################################
# BUSINESS LEAD
############################################################

@dataclass
class BusinessLead:
    
        ########################################################
    # PROCESSING STATE
    ########################################################

    def has_been_processed(self) -> bool:

        return (
            self.status
            not in {
                LeadStatus.NEW,
                LeadStatus.DISCOVERED,
            }
        )

    ########################################################
    # IDENTITY
    ########################################################

    name: str

    category: str = ""

    subcategory: str = ""

    business_id: Optional[str] = None

    ########################################################
    # LOCATION
    ########################################################

    address: str = ""

    city: str = ""

    state: str = ""

    country: str = "India"

    postal_code: str = ""

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    ########################################################
    # PUBLIC BUSINESS CONTACT
    ########################################################

    phone: str = ""

    normalized_phone: str = ""

    whatsapp_number: str = ""

    ########################################################
    # BUSINESS PROFILE
    ########################################################

    profile_url: str = ""

    maps_url: str = ""

    social_url: str = ""

    ########################################################
    # WEBSITE
    ########################################################

    website_url: str = ""

    website_status: WebsiteStatus = (
        WebsiteStatus.UNKNOWN
    )

    website_checked_at: Optional[datetime] = None

    ########################################################
    # BUSINESS QUALITY
    ########################################################

    rating: Optional[float] = None

    review_count: Optional[int] = None

    ########################################################
    # QUALIFICATION
    ########################################################

    qualified: bool = False

    qualification_reason: str = ""

    qualification_confidence: float = 0.0

    ########################################################
    # LEAD STATE
    ########################################################

    status: LeadStatus = LeadStatus.NEW

    source: LeadSource = (
        LeadSource.GOOGLE_BUSINESS_PROFILE
    )

    ########################################################
    # OUTREACH
    ########################################################

    sample_type: SampleType = SampleType.NONE

    sample_name: str = ""

    sample_url: str = ""

    pitch_template: str = ""

    pitch_message: str = ""

    outreach_status: OutreachStatus = (
        OutreachStatus.NOT_STARTED
    )

    ########################################################
    # APPROVAL
    ########################################################

    approval_required: bool = True

    approved: bool = False

    approved_at: Optional[datetime] = None

    ########################################################
    # OUTREACH HISTORY
    ########################################################

    contacted_at: Optional[datetime] = None

    replied_at: Optional[datetime] = None

    response: str = ""

    ########################################################
    # DUPLICATE / TRACKING
    ########################################################

    duplicate_of: Optional[str] = None

    last_checked_at: Optional[datetime] = None

    created_at: datetime = field(
        default_factory=datetime.now
    )

    updated_at: datetime = field(
        default_factory=datetime.now
    )

    ########################################################
    # METADATA
    ########################################################

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    ########################################################
    # UPDATE TIMESTAMP
    ########################################################

    def touch(self):

        self.updated_at = datetime.now()

    ########################################################
    # WEBSITE HELPERS
    ########################################################

    def has_website_listed(self) -> bool:

        return (
            self.website_status
            in {
                WebsiteStatus.WEBSITE_LISTED,
                WebsiteStatus.WEBSITE_VERIFIED,
            }
        )

    def has_no_website_listed(self) -> bool:

        return (
            self.website_status
            ==
            WebsiteStatus.NO_WEBSITE_LISTED
        )

    ########################################################
    # QUALIFICATION HELPERS
    ########################################################

    def qualify(
        self,
        reason: str = "",
        confidence: float = 1.0,
    ):

        self.qualified = True

        self.status = (
            LeadStatus.QUALIFIED
        )

        self.qualification_reason = (
            reason
        )

        self.qualification_confidence = max(
            0.0,
            min(
                1.0,
                float(confidence)
            )
        )

        self.touch()

    def reject(
        self,
        reason: str = "",
    ):

        self.qualified = False

        self.status = (
            LeadStatus.REJECTED
        )

        self.qualification_reason = (
            reason
        )

        self.touch()

    ########################################################
    # WEBSITE STATUS
    ########################################################

    def mark_no_website(
        self,
        reason: str = "",
    ):

        self.website_status = (
            WebsiteStatus.NO_WEBSITE_LISTED
        )

        self.website_url = ""

        self.website_checked_at = (
            datetime.now()
        )

        if reason:

            self.qualification_reason = (
                reason
            )

        self.touch()

    def mark_website(
        self,
        url: str,
        verified: bool = False,
    ):

        self.website_url = (
            str(url or "").strip()
        )

        if verified:

            self.website_status = (
                WebsiteStatus.WEBSITE_VERIFIED
            )

        else:

            self.website_status = (
                WebsiteStatus.WEBSITE_LISTED
            )

        self.website_checked_at = (
            datetime.now()
        )

        self.touch()

    ########################################################
    # PITCH
    ########################################################

    def set_pitch(
        self,
        message: str,
        sample_type: SampleType = SampleType.NONE,
        sample_name: str = "",
        sample_url: str = "",
        template: str = "",
    ):

        self.pitch_message = (
            str(message or "").strip()
        )

        self.sample_type = (
            sample_type
        )

        self.sample_name = (
            str(sample_name or "").strip()
        )

        self.sample_url = (
            str(sample_url or "").strip()
        )

        self.pitch_template = (
            str(template or "").strip()
        )

        self.outreach_status = (
            OutreachStatus.DRAFTED
        )

        self.status = (
            LeadStatus.PITCH_READY
        )

        self.touch()

    ########################################################
    # APPROVAL
    ########################################################

    def approve(self):

        self.approved = True

        self.approved_at = (
            datetime.now()
        )

        self.outreach_status = (
            OutreachStatus.APPROVED
        )

        self.status = (
            LeadStatus.APPROVED
        )

        self.touch()

    def revoke_approval(self):

        self.approved = False

        self.approved_at = None

        self.outreach_status = (
            OutreachStatus.AWAITING_APPROVAL
        )

        self.status = (
            LeadStatus.AWAITING_APPROVAL
        )

        self.touch()

    ########################################################
    # OUTREACH
    ########################################################

    def mark_prepared(self):

        self.outreach_status = (
            OutreachStatus.PREPARED
        )

        self.touch()

    def mark_sent(self):

        self.outreach_status = (
            OutreachStatus.SENT
        )

        self.status = (
            LeadStatus.CONTACTED
        )

        self.contacted_at = (
            datetime.now()
        )

        self.touch()

    def mark_outreach_failed(
        self,
        reason: str = "",
    ):

        self.outreach_status = (
            OutreachStatus.FAILED
        )

        self.status = (
            LeadStatus.FAILED
        )

        if reason:

            self.metadata[
                "outreach_error"
            ] = reason

        self.touch()

    ########################################################
    # RESPONSE
    ########################################################

    def mark_replied(
        self,
        response: str = "",
    ):

        self.status = (
            LeadStatus.REPLIED
        )

        self.replied_at = (
            datetime.now()
        )

        self.response = (
            str(response or "").strip()
        )

        self.touch()

    def mark_interested(
        self,
        response: str = "",
    ):

        self.status = (
            LeadStatus.INTERESTED
        )

        self.replied_at = (
            datetime.now()
        )

        self.response = (
            str(response or "").strip()
        )

        self.touch()

    def mark_not_interested(
        self,
        response: str = "",
    ):

        self.status = (
            LeadStatus.NOT_INTERESTED
        )

        self.replied_at = (
            datetime.now()
        )

        self.response = (
            str(response or "").strip()
        )

        self.touch()

    ########################################################
    # DUPLICATE
    ########################################################

    def mark_duplicate(
        self,
        duplicate_of: str,
    ):

        self.duplicate_of = (
            str(duplicate_of or "").strip()
        )

        self.status = (
            LeadStatus.DUPLICATE
        )

        self.qualified = False

        self.touch()

    ########################################################
    # SERIALIZATION
    ########################################################

    def to_dict(self) -> dict[str, Any]:

        return {
            "name":
                self.name,

            "category":
                self.category,

            "subcategory":
                self.subcategory,

            "business_id":
                self.business_id,

            "address":
                self.address,

            "city":
                self.city,

            "state":
                self.state,

            "country":
                self.country,

            "postal_code":
                self.postal_code,

            "latitude":
                self.latitude,

            "longitude":
                self.longitude,

            "phone":
                self.phone,

            "normalized_phone":
                self.normalized_phone,

            "whatsapp_number":
                self.whatsapp_number,

            "profile_url":
                self.profile_url,

            "maps_url":
                self.maps_url,

            "social_url":
                self.social_url,

            "website_url":
                self.website_url,

            "website_status":
                self.website_status.value,

            "website_checked_at":
                (
                    self.website_checked_at.isoformat()
                    if self.website_checked_at
                    else None
                ),

            "rating":
                self.rating,

            "review_count":
                self.review_count,

            "qualified":
                self.qualified,

            "qualification_reason":
                self.qualification_reason,

            "qualification_confidence":
                self.qualification_confidence,

            "status":
                self.status.value,

            "source":
                self.source.value,

            "sample_type":
                self.sample_type.value,

            "sample_name":
                self.sample_name,

            "sample_url":
                self.sample_url,

            "pitch_template":
                self.pitch_template,

            "pitch_message":
                self.pitch_message,

            "outreach_status":
                self.outreach_status.value,

            "approval_required":
                self.approval_required,

            "approved":
                self.approved,

            "approved_at":
                (
                    self.approved_at.isoformat()
                    if self.approved_at
                    else None
                ),

            "contacted_at":
                (
                    self.contacted_at.isoformat()
                    if self.contacted_at
                    else None
                ),

            "replied_at":
                (
                    self.replied_at.isoformat()
                    if self.replied_at
                    else None
                ),

            "response":
                self.response,

            "duplicate_of":
                self.duplicate_of,

            "last_checked_at":
                (
                    self.last_checked_at.isoformat()
                    if self.last_checked_at
                    else None
                ),

            "created_at":
                self.created_at.isoformat(),

            "updated_at":
                self.updated_at.isoformat(),

            "metadata":
                dict(self.metadata),
        }

    ########################################################
    # REPRESENTATION
    ########################################################

    def __repr__(self):

        return (
            "BusinessLead("
            f"name={self.name!r}, "
            f"category={self.category!r}, "
            f"phone={self.phone!r}, "
            f"website_status="
            f"{self.website_status.value!r}, "
            f"status={self.status.value!r}"
            ")"
        )