from __future__ import annotations

import json
import re

from datetime import datetime
from pathlib import Path
from typing import Any


############################################################
# LEAD STATUS
############################################################

class LeadStatus:

    NEW = "NEW"

    DISCOVERED = "DISCOVERED"

    CONTACTED = "CONTACTED"

    REPLIED = "REPLIED"

    INTERESTED = "INTERESTED"

    DEMO_SENT = "DEMO_SENT"

    CLIENT = "CLIENT"

    NOT_INTERESTED = "NOT_INTERESTED"

    SKIPPED_NO_PHONE = (
        "SKIPPED_NO_PHONE"
    )

    SKIPPED_MANUALLY = (
        "SKIPPED_MANUALLY"
    )

    SKIPPED_CONTACT_FAILED = (
        "SKIPPED_CONTACT_FAILED"
    )

    REJECTED_WEBSITE = (
        "REJECTED_WEBSITE"
    )

    REJECTED_TOO_ESTABLISHED = (
        "REJECTED_TOO_ESTABLISHED"
    )


############################################################
# LEAD TRACKER
############################################################

class LeadTracker:

    """
    Persistent lead database.

    Source of truth:

        lead_history.json

    Used by:

        - discovery
        - qualification
        - outreach
        - lead manager
        - analytics dashboard
    """

    FILE_PATH = (
        Path(__file__).parent
        / "lead_history.json"
    )

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
    ):

        self.leads = (
            self._load()
        )

    ########################################################
    # LOAD
    ########################################################

    def _load(
        self,
    ) -> dict[str, dict[str, Any]]:

        if not self.FILE_PATH.exists():

            return {}

        try:

            data = json.loads(
                self.FILE_PATH.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):

            return {}

        if not isinstance(
            data,
            dict,
        ):

            return {}

        cleaned = {}

        for key, value in data.items():

            if isinstance(
                value,
                dict,
            ):

                cleaned[
                    str(key)
                ] = value

        return cleaned

    ########################################################
    # REFRESH
    ########################################################

    def refresh(
        self,
    ) -> dict[str, dict[str, Any]]:

        self.leads = (
            self._load()
        )

        return self.leads

    ########################################################
    # SAVE
    ########################################################

    def _save(
        self,
    ) -> bool:

        try:

            self.FILE_PATH.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.FILE_PATH.write_text(
                json.dumps(
                    self.leads,
                    indent=4,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            return True

        except OSError as exc:

            print(
                "[LeadTracker] Save failed:",
                exc,
            )

            return False

    ########################################################
    # PUBLIC RECORD ACCESS
    ########################################################

    def get_all_records(
        self,
    ) -> list[dict[str, Any]]:

        return [
            dict(record)
            for record in self.leads.values()
            if isinstance(
                record,
                dict,
            )
        ]

    ########################################################
    # SNAPSHOT
    ########################################################

    def get_snapshot(
        self,
    ) -> dict[str, dict[str, Any]]:

        return {
            key: dict(record)
            for key, record
            in self.leads.items()
            if isinstance(
                record,
                dict,
            )
        }

    ########################################################
    # COUNT
    ########################################################

    def count(
        self,
    ) -> int:

        return len(
            self.leads
        )

    ########################################################
    # NORMALIZE TEXT
    ########################################################

    @staticmethod
    def _normalize_text(
        value,
    ) -> str:

        if value is None:

            return ""

        text = str(
            value
        ).lower()

        words = re.findall(
            r"[a-z0-9]+",
            text,
        )

        return " ".join(
            words
        )

    ########################################################
    # NORMALIZE PHONE
    ########################################################

    @staticmethod
    def _normalize_phone(
        value,
    ) -> str:

        if value is None:

            return ""

        return "".join(
            re.findall(
                r"\d+",
                str(value),
            )
        )

    ########################################################
    # POSSIBLE KEYS
    ########################################################

    def _possible_keys(
        self,
        lead,
    ) -> list[str]:

        keys = []

        ####################################################
        # BUSINESS ID
        ####################################################

        business_id = str(
            getattr(
                lead,
                "business_id",
                "",
            )
            or ""
        ).strip()

        if business_id:

            keys.append(
                "business:"
                + business_id.lower()
            )

        ####################################################
        # PHONE
        ####################################################

        phone = (
            getattr(
                lead,
                "normalized_phone",
                "",
            )
            or ""
        )

        if not phone:

            phone = (
                getattr(
                    lead,
                    "phone",
                    "",
                )
                or ""
            )

        normalized_phone = (
            self._normalize_phone(
                phone
            )
        )

        if normalized_phone:

            keys.append(
                "phone:"
                + normalized_phone
            )

        ####################################################
        # NAME
        ####################################################

        name = (
            getattr(
                lead,
                "name",
                "",
            )
            or ""
        )

        normalized_name = (
            self._normalize_text(
                name
            )
        )

        if normalized_name:

            keys.append(
                "name:"
                + normalized_name
            )

        return keys

    ########################################################
    # RECORD MATCHING
    ########################################################

    def _record_matches(
        self,
        record,
        lead,
    ) -> bool:

        if not isinstance(
            record,
            dict,
        ):

            return False

        ####################################################
        # BUSINESS ID
        ####################################################

        lead_business_id = str(
            getattr(
                lead,
                "business_id",
                "",
            )
            or ""
        ).strip().lower()

        record_business_id = str(
            record.get(
                "business_id",
                "",
            )
            or ""
        ).strip().lower()

        if (
            lead_business_id
            and record_business_id
            and lead_business_id
            == record_business_id
        ):

            return True

        ####################################################
        # PHONE
        ####################################################

        lead_phone = (
            self._normalize_phone(
                getattr(
                    lead,
                    "normalized_phone",
                    "",
                )
                or getattr(
                    lead,
                    "phone",
                    "",
                )
            )
        )

        record_phone = (
            self._normalize_phone(
                record.get(
                    "normalized_phone",
                    "",
                )
                or record.get(
                    "phone",
                    "",
                )
            )
        )

        if (
            lead_phone
            and record_phone
            and lead_phone
            == record_phone
        ):

            return True

        ####################################################
        # NAME
        ####################################################

        lead_name = (
            self._normalize_text(
                getattr(
                    lead,
                    "name",
                    "",
                )
            )
        )

        record_name = (
            self._normalize_text(
                record.get(
                    "name",
                    "",
                )
            )
        )

        if (
            lead_name
            and record_name
            and lead_name
            == record_name
        ):

            return True

        return False

    ########################################################
    # GET RECORD
    ########################################################

    def get_record(
        self,
        lead,
    ):

        ####################################################
        # FAST LOOKUP
        ####################################################

        for key in self._possible_keys(
            lead
        ):

            record = self.leads.get(
                key
            )

            if isinstance(
                record,
                dict,
            ):

                return record

        ####################################################
        # DEEP LOOKUP
        ####################################################

        for record in self.leads.values():

            if self._record_matches(
                record,
                lead,
            ):

                return record

        return None

    ########################################################
    # GET EXISTING KEY
    ########################################################

    def _get_existing_key(
        self,
        lead,
    ) -> str | None:

        for key in self._possible_keys(
            lead
        ):

            if key in self.leads:

                return key

        for key, record in self.leads.items():

            if self._record_matches(
                record,
                lead,
            ):

                return key

        return None

    ########################################################
    # EXISTS
    ########################################################

    def exists(
        self,
        lead,
    ) -> bool:

        return (
            self.get_record(
                lead
            )
            is not None
        )

    ########################################################
    # GET STATUS
    ########################################################

    def get_status(
        self,
        lead,
    ) -> str:

        record = self.get_record(
            lead
        )

        if not record:

            return LeadStatus.NEW

        return str(
            record.get(
                "status",
                LeadStatus.NEW,
            )
            or LeadStatus.NEW
        )

    ########################################################
    # BUILD RECORD
    ########################################################

    def _build_record(
        self,
        lead,
        status: str,
    ) -> dict[str, Any]:

        existing = self.get_record(
            lead
        )

        if isinstance(
            existing,
            dict,
        ):

            record = dict(
                existing
            )

        else:

            record = {}

        ####################################################
        # IDENTITY
        ####################################################

        record[
            "name"
        ] = getattr(
            lead,
            "name",
            "",
        )

        record[
            "business_id"
        ] = getattr(
            lead,
            "business_id",
            None,
        )

        record[
            "phone"
        ] = getattr(
            lead,
            "phone",
            "",
        )

        record[
            "normalized_phone"
        ] = self._normalize_phone(
            getattr(
                lead,
                "normalized_phone",
                "",
            )
            or getattr(
                lead,
                "phone",
                "",
            )
        )

        record[
            "category"
        ] = getattr(
            lead,
            "category",
            "",
        )

        ####################################################
        # STATUS
        ####################################################

        record[
            "status"
        ] = str(
            status
        )

        record[
            "updated_at"
        ] = datetime.now().isoformat()

        if not record.get(
            "created_at"
        ):

            record[
                "created_at"
            ] = datetime.now().isoformat()

        return record

    ########################################################
    # SAVE RECORD
    ########################################################

    def _save_record(
        self,
        lead,
        record,
    ) -> bool:

        existing_key = (
            self._get_existing_key(
                lead
            )
        )

        if existing_key:

            self.leads[
                existing_key
            ] = record

        else:

            keys = self._possible_keys(
                lead
            )

            if not keys:

                return False

            self.leads[
                keys[0]
            ] = record

        return self._save()

    ########################################################
    # MARK DISCOVERED
    ########################################################

    def mark_discovered(
        self,
        lead,
    ) -> bool:

        record = self._build_record(
            lead,
            LeadStatus.DISCOVERED,
        )

        if not record.get(
            "discovered_at"
        ):

            record[
                "discovered_at"
            ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # MARK CONTACTED
    ########################################################

    def mark_contacted(
        self,
        lead,
        message: str = "",
    ) -> bool:

        record = self._build_record(
            lead,
            LeadStatus.CONTACTED,
        )

        record[
            "message"
        ] = str(
            message or ""
        )

        record[
            "contacted_at"
        ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # MARK REPLIED
    ########################################################

    def mark_replied(
        self,
        lead,
        response: str = "",
    ) -> bool:

        record = self._build_record(
            lead,
            LeadStatus.REPLIED,
        )

        record[
            "response"
        ] = str(
            response or ""
        )

        record[
            "replied_at"
        ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # MARK INTERESTED
    ########################################################

    def mark_interested(
        self,
        lead,
        response: str = "",
    ) -> bool:

        record = self._build_record(
            lead,
            LeadStatus.INTERESTED,
        )

        record[
            "response"
        ] = str(
            response or ""
        )

        record[
            "interested_at"
        ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # MARK DEMO SENT
    ########################################################

    def mark_demo_sent(
        self,
        lead,
        demo_url: str = "",
    ) -> bool:

        record = self._build_record(
            lead,
            LeadStatus.DEMO_SENT,
        )

        record[
            "demo_url"
        ] = str(
            demo_url or ""
        ).strip()

        record[
            "demo_sent_at"
        ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # MARK CLIENT
    ########################################################

    def mark_client(
        self,
        lead,
    ) -> bool:

        record = self._build_record(
            lead,
            LeadStatus.CLIENT,
        )

        record[
            "client_at"
        ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # MARK NOT INTERESTED
    ########################################################

    def mark_not_interested(
        self,
        lead,
        response: str = "",
    ) -> bool:

        record = self._build_record(
            lead,
            LeadStatus.NOT_INTERESTED,
        )

        record[
            "response"
        ] = str(
            response or ""
        )

        record[
            "not_interested_at"
        ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # MARK REJECTED
    ########################################################

    def mark_rejected(
        self,
        lead,
        status: str,
        reason: str,
    ) -> bool:

        record = self._build_record(
            lead,
            status,
        )

        record[
            "reason"
        ] = str(
            reason or ""
        )

        record[
            "rejected_at"
        ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # MARK SKIPPED
    ########################################################

    def mark_skipped(
        self,
        lead,
        reason: str,
        status: str = (
            LeadStatus.SKIPPED_NO_PHONE
        ),
    ) -> bool:

        record = self._build_record(
            lead,
            status,
        )

        record[
            "reason"
        ] = str(
            reason or ""
        )

        record[
            "skipped_at"
        ] = datetime.now().isoformat()

        return self._save_record(
            lead,
            record,
        )

    ########################################################
    # UPDATE STATUS FROM BUSINESS LEAD
    ########################################################

    def update_status(
        self,
        lead,
        status: str,
    ) -> bool:

        existing_key = (
            self._get_existing_key(
                lead
            )
        )

        if existing_key is None:

            return False

        record = self.leads.get(
            existing_key
        )

        if not isinstance(
            record,
            dict,
        ):

            return False

        record[
            "status"
        ] = str(
            status
        )

        record[
            "updated_at"
        ] = datetime.now().isoformat()

        return self._save()

    ########################################################
    # UPDATE STATUS FROM STORED RECORD
    #
    # Used by lead_manager.py.
    ########################################################

    def update_status_by_record(
        self,
        record: dict[str, Any],
        status: str,
    ) -> bool:

        if not isinstance(
            record,
            dict,
        ):

            return False

        ####################################################
        # FIND RECORD BY IDENTITY
        ####################################################

        target_key = None

        business_id = str(
            record.get(
                "business_id",
                "",
            )
            or ""
        ).strip().lower()

        if business_id:

            candidate_key = (
                "business:"
                + business_id
            )

            if candidate_key in self.leads:

                target_key = (
                    candidate_key
                )

        ####################################################
        # PHONE FALLBACK
        ####################################################

        if target_key is None:

            phone = (
                record.get(
                    "normalized_phone",
                    "",
                )
                or record.get(
                    "phone",
                    "",
                )
            )

            normalized_phone = (
                self._normalize_phone(
                    phone
                )
            )

            if normalized_phone:

                candidate_key = (
                    "phone:"
                    + normalized_phone
                )

                if candidate_key in self.leads:

                    target_key = (
                        candidate_key
                    )

        ####################################################
        # NAME FALLBACK
        ####################################################

        if target_key is None:

            name = self._normalize_text(
                record.get(
                    "name",
                    "",
                )
            )

            if name:

                candidate_key = (
                    "name:"
                    + name
                )

                if candidate_key in self.leads:

                    target_key = (
                        candidate_key
                    )

        ####################################################
        # DEEP FALLBACK
        ####################################################

        if target_key is None:

            for key, existing in (
                self.leads.items()
            ):

                if not isinstance(
                    existing,
                    dict,
                ):

                    continue

                same_business_id = (
                    business_id
                    and
                    str(
                        existing.get(
                            "business_id",
                            "",
                        )
                        or ""
                    ).strip().lower()
                    == business_id
                )

                same_phone = (
                    normalized_phone
                    and
                    self._normalize_phone(
                        existing.get(
                            "normalized_phone",
                            "",
                        )
                        or existing.get(
                            "phone",
                            "",
                        )
                    )
                    == normalized_phone
                )

                same_name = (
                    name
                    and
                    self._normalize_text(
                        existing.get(
                            "name",
                            "",
                        )
                    )
                    == name
                )

                if (
                    same_business_id
                    or
                    same_phone
                    or
                    same_name
                ):

                    target_key = key
                    break

        ####################################################
        # NOT FOUND
        ####################################################

        if target_key is None:

            return False

        ####################################################
        # UPDATE
        ####################################################

        self.leads[
            target_key
        ][
            "status"
        ] = str(
            status
        )

        self.leads[
            target_key
        ][
            "updated_at"
        ] = datetime.now().isoformat()

        ####################################################
        # STATUS-SPECIFIC TIMESTAMPS
        ####################################################

        now = datetime.now().isoformat()

        if status == LeadStatus.CONTACTED:

            self.leads[
                target_key
            ][
                "contacted_at"
            ] = now

        elif status == LeadStatus.REPLIED:

            self.leads[
                target_key
            ][
                "replied_at"
            ] = now

        elif status == LeadStatus.INTERESTED:

            self.leads[
                target_key
            ][
                "interested_at"
            ] = now

        elif status == LeadStatus.DEMO_SENT:

            self.leads[
                target_key
            ][
                "demo_sent_at"
            ] = now

        elif status == LeadStatus.CLIENT:

            self.leads[
                target_key
            ][
                "client_at"
            ] = now

        elif status == LeadStatus.NOT_INTERESTED:

            self.leads[
                target_key
            ][
                "not_interested_at"
            ] = now

        return self._save()