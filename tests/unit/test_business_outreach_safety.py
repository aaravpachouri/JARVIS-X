from unittest.mock import Mock, patch

from business_outreach.models.lead import BusinessLead, WebsiteStatus
from business_outreach.outreach.whatsapp_sender import WhatsAppSender
from business_outreach.qualification.search_website_verifier import SearchWebsiteVerifier
from business_outreach.qualification.website_qualifier import WebsiteQualifier


class EmptySearchProvider:
    def search(self, query, limit=10):
        return []


class NonMatchingSearchProvider:
    def search(self, query, limit=10):
        return [{"title": "Unrelated result", "url": "https://example.org", "snippet": ""}]


class UnmatchedWebsiteMatcher:
    def match(self, business_name, results):
        return {
            "matched": False,
            "reason": "No convincing official website match.",
            "confidence": 0.0,
        }


def make_lead(**kwargs):
    return BusinessLead(name="Test Cafe", phone="9876543210", **kwargs)


def test_empty_website_search_is_unknown_not_no_website():
    verifier = SearchWebsiteVerifier(EmptySearchProvider())
    result = verifier.verify(make_lead())

    assert result["status"] == WebsiteStatus.UNKNOWN
    assert result["confidence"] == 0.0


def test_unmatched_search_is_unknown_not_no_website():
    verifier = SearchWebsiteVerifier(
        NonMatchingSearchProvider(),
        matcher=UnmatchedWebsiteMatcher(),
    )
    result = verifier.verify(make_lead())

    assert result["status"] == WebsiteStatus.UNKNOWN
    assert result["confidence"] == 0.0


def test_unknown_web_search_does_not_qualify_for_outreach():
    class Provider:
        def check(self, lead):
            return {
                "status": WebsiteStatus.UNKNOWN,
                "source": "web_search",
                "reason": "No convincing match.",
                "confidence": 0.0,
            }

    qualifier = WebsiteQualifier()
    qualifier.register_provider(Provider())
    result = qualifier.qualify(make_lead())

    assert result.status == WebsiteStatus.UNKNOWN
    assert result.qualified_for_outreach is False


def test_whatsapp_sender_blocks_unapproved_lead():
    lead = make_lead(approval_required=True, approved=False)
    sender = WhatsAppSender(dry_run=False)

    with patch("business_outreach.outreach.whatsapp_sender.webbrowser.open") as open_browser:
        assert sender.send(lead, "Hello") is False

    open_browser.assert_not_called()


def test_whatsapp_sender_opens_chat_only_after_approval():
    lead = make_lead(approval_required=True, approved=True)
    sender = WhatsAppSender(dry_run=False)

    with patch("business_outreach.outreach.whatsapp_sender.webbrowser.open", return_value=True) as open_browser:
        assert sender.send(lead, "Hello") is True

    open_browser.assert_called_once()
    assert "wa.me/919876543210" in open_browser.call_args.args[0]


def test_phone_normalizer_rejects_unsupported_lengths():
    sender = WhatsAppSender()
    assert sender._normalize_phone("12345") == ""
