import json
from pathlib import Path


class ContactedLeads:

    FILE_PATH = (
        Path(__file__).parent
        / "contacted_leads.json"
    )

    def __init__(self):

        self.contacted = (
            self._load()
        )

    ########################################################
    # LOAD
    ########################################################

    def _load(self) -> set[str]:

        if not self.FILE_PATH.exists():

            return set()

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

            return set()

        if not isinstance(
            data,
            list,
        ):

            return set()

        return {
            str(item).strip().lower()
            for item in data
            if str(item).strip()
        }

    ########################################################
    # SAVE
    ########################################################

    def _save(self):

        self.FILE_PATH.write_text(
            json.dumps(
                sorted(
                    self.contacted
                ),
                indent=4,
            ),
            encoding="utf-8",
        )

    ########################################################
    # CREATE IDENTITY
    ########################################################

    @staticmethod
    def _key(
        lead,
    ) -> str:

        if lead.business_id:

            return (
                "business:"
                + lead.business_id.strip().lower()
            )

        if lead.normalized_phone:

            return (
                "phone:"
                + lead.normalized_phone
            )

        return (
            "name:"
            + lead.name.strip().lower()
        )

    ########################################################
    # CHECK
    ########################################################

    def was_contacted(
        self,
        lead,
    ) -> bool:

        return (
            self._key(lead)
            in self.contacted
        )

    ########################################################
    # MARK CONTACTED
    ########################################################

    def mark_contacted(
        self,
        lead,
    ):

        self.contacted.add(
            self._key(lead)
        )

        self._save()