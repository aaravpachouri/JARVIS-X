import re
import webbrowser
from urllib.parse import quote

from business_outreach.models.lead import (
    BusinessLead,
)


class WhatsAppSender:

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        dry_run: bool = True,
        country_code: str = "91",
    ):

        self.dry_run = dry_run

        self.country_code = (
            str(country_code)
            .strip()
            .lstrip("+")
        )

    ########################################################
    # SEND
    ########################################################

    def send(
        self,
        lead: BusinessLead,
        message: str,
    ) -> bool:

        phone = self._normalize_phone(
            lead.phone
        )

        if not phone:

            print(
                f"[WhatsApp] No valid phone number "
                f"for {lead.name}"
            )

            return False

        if not message.strip():

            print(
                "[WhatsApp] Message is empty."
            )

            return False

        ####################################################
        # BUILD WHATSAPP LINK
        ####################################################

        whatsapp_url = (
            f"https://wa.me/{phone}"
            f"?text={quote(message)}"
        )

        ####################################################
        # DRY RUN
        ####################################################

        if self.dry_run:

            print("\n[WhatsApp DRY RUN]")

            print(
                f"To: +{phone}"
            )

            print(
                f"Business: {lead.name}"
            )

            print(
                "\nMessage:"
            )

            print(
                message
            )

            print(
                "\nWhatsApp URL:"
            )

            print(
                whatsapp_url
            )

            return True

        ####################################################
        # OPEN WHATSAPP
        ####################################################

        try:

            webbrowser.open(
                whatsapp_url
            )

            print(
                f"\n[WhatsApp] Opened chat for "
                f"{lead.name}"
            )

            return True

        except Exception as exc:

            print(
                f"[WhatsApp] Failed to open chat: "
                f"{exc}"
            )

            return False

       ####################################################
    # NORMALIZE PHONE
    ####################################################

    def _normalize_phone(
        self,
        phone: str,
    ) -> str:

        if not phone:

            return ""

        digits = re.sub(
            r"\D",
            "",
            phone,
        )

        if not digits:

            return ""

        ####################################################
        # REMOVE LEADING ZERO
        ####################################################

        if (
            len(digits) == 11
            and digits.startswith("0")
        ):

            digits = digits[1:]

        ####################################################
        # ALREADY HAS COUNTRY CODE
        ####################################################

        if (
            digits.startswith(
                self.country_code
            )
            and len(digits) >= 12
        ):

            return digits

        ####################################################
        # STANDARD 10 DIGIT NUMBER
        ####################################################

        if len(digits) == 10:

            return (
                self.country_code
                + digits
            )

        return ""

        ####################################################
        # ALREADY HAS INDIA COUNTRY CODE
        ####################################################

        if digits.startswith(
            self.country_code
        ):

            return digits

        ####################################################
        # STANDARD 10 DIGIT INDIAN NUMBER
        ####################################################

        if len(digits) == 10:

            return (
                self.country_code
                + digits
            )

        ####################################################
        # UNKNOWN FORMAT
        ####################################################

        return ""