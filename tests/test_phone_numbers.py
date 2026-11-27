"""Phone numbers (buy a number for WhatsApp, SMS and calls).

Each method sends the request the API expects, and the public texts keep
internal names out. No network: the session is patched.

Run with: python -m unittest discover -s tests
"""

import inspect
import json
import os
import re
import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://api.upload-post.com/api/uploadposts/phone-numbers"
SHIPPED = ""
for name in ("upload_post/api_client.py", "README.md", "CHANGELOG.md"):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        SHIPPED += fh.read()
with open(os.path.join(ROOT, "codegen", "openapi.json"), encoding="utf-8") as fh:
    SPEC = json.load(fh)

PHONE_EVENTS = ["sms_received", "call_received", "voicemail_received", "phone_number_activated",
                "phone_number_declined", "phone_number_released", "phone_number_port_out",
                "phone_number_kyc_comment", "phone_number_kyc_resubmitted"]
METHODS = [
    "get_phone_numbers_config", "list_phone_number_countries", "search_available_phone_numbers",
    "purchase_phone_number", "get_phone_number_kyc_fields", "submit_phone_number_kyc", "list_phone_numbers",
    "get_phone_number", "release_phone_number", "update_phone_number_voice", "send_phone_number_sms",
    "list_phone_number_messages", "list_phone_number_calls", "list_phone_number_codes",
    "prepare_phone_number_whatsapp", "get_phone_number_port_out_info", "get_phone_numbers_usage",
    "get_phone_number_kyc_remediation", "remediate_phone_number_kyc", "reply_phone_number_kyc_reviewer",
    "create_phone_number_kyc_link", "list_phone_number_kyc_links", "revoke_phone_number_kyc_link",
]
END_USER = {
    "type": "business", "first_name": "Ana", "last_name": "Garcia", "business_name": "Acme SL",
    "phone": "+34600111222",
    "address": {"street_address": "Calle Mayor 1", "locality": "Madrid", "postal_code": "28013", "country_code": "ES"},
}


class TestPhoneNumbers(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("k")
        response = MagicMock()
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        self.request = patch.object(self.client.session, "request", return_value=response).start()
        self.addCleanup(patch.stopall)

    def sent(self, i=-1):
        args, kwargs = self.request.call_args_list[i]
        return args[0], args[1], kwargs

    def test_every_operation_has_a_method_none_marked_not_generally_available(self):
        for name in METHODS:
            with self.subTest(method=name):
                self.assertTrue(callable(getattr(UploadPostClient, name, None)), name)
        for op_id, (_, route, meta) in UploadPostClient._OPENAPI_OPERATIONS.items():
            if route.startswith("/uploadposts/phone-numbers"):
                self.assertNotIn("na", meta, op_id)

    def test_search_sends_the_filters_in_the_query(self):
        self.client.search_available_phone_numbers("ES", number_type="mobile", sms=True, limit=5)
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("GET", f"{BASE}/available"))
        self.assertEqual(kwargs["params"], {"country": "ES", "number_type": "mobile", "sms": "true", "limit": 5})

    def test_purchase_sends_a_json_body_with_end_user_as_given(self):
        self.client.purchase_phone_number("p", "ES", "mobile", "intent-123456", END_USER,
                                          accept_terms=True, terms_version="2026-11-28",
                                          phone_number="+34600000001")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("POST", f"{BASE}/purchase"))
        self.assertEqual(kwargs["json"], {
            "profile_username": "p", "country": "ES", "number_type": "mobile", "purchase_intent_id": "intent-123456",
            "end_user": END_USER, "accept_terms": True, "terms_version": "2026-11-28", "phone_number": "+34600000001",
        })

    def test_consumers_send_immediate_start_consent_on_purchase_and_kyc(self):
        individual = dict(END_USER, type="individual")
        self.client.purchase_phone_number("p", "ES", "mobile", "intent-1", individual, accept_terms=True,
                                          terms_version="2026-11-28", immediate_start_consent=True)
        self.assertIs(self.sent()[2]["json"]["immediate_start_consent"], True)
        self.client.submit_phone_number_kyc("p", "DE", "local", "intent-2", individual, True, "2026-11-28",
                                            immediate_start_consent=True)
        self.assertIs(self.sent()[2]["json"]["immediate_start_consent"], True)
        for name in ("purchase_phone_number", "submit_phone_number_kyc"):
            doc = " ".join(getattr(UploadPostClient, name).__doc__.split())
            self.assertRegex(doc, r"immediate_start_consent \(bool, optional\): Required \(true\) when `end_user.type` "
                                  r"is `individual` \(consumers\).*400 `immediate_start_consent_required`", name)
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            readme = fh.read()
        self.assertRegex(readme, r'immediate_start_consent=True, +# required when end_user\["type"\] is "individual"')
        self.assertIn('terms_version=config["terms_version"],  # e.g. "2026-11-28"', readme)

    def test_kyc_sends_values_and_base64_documents_in_json(self):
        documents = {"req_id": {"filename": "id.pdf", "content_base64": "JVBERg=="}}
        self.client.submit_phone_number_kyc("p", "DE", "local", "intent-123456", END_USER, True, "2026-11-28",
                                            values={"req_tax": "DE1"}, documents=documents)
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("POST", f"{BASE}/kyc"))
        self.assertEqual(kwargs["json"]["documents"], documents)
        self.assertEqual(kwargs["json"]["values"], {"req_tax": "DE1"})
        self.assertNotIn("files", kwargs)

    def test_release_needs_confirm_and_sends_it_in_the_query(self):
        params = inspect.signature(UploadPostClient.release_phone_number).parameters
        self.assertIs(params["confirm"].default, inspect.Parameter.empty)
        self.client.release_phone_number("pn_1", confirm=True)
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("DELETE", f"{BASE}/pn_1"))
        self.assertEqual(kwargs["params"], {"confirm": "true"})
        self.assertNotIn("json", kwargs)

    def test_sms_voice_codes_and_whatsapp_go_to_the_number(self):
        self.client.send_phone_number_sms("pn_1", "+34600999888", "hi")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url, kwargs["json"]), ("POST", f"{BASE}/pn_1/sms", {"to": "+34600999888", "text": "hi"}))

        self.client.update_phone_number_voice("pn_1", forward_to="", voicemail_enabled=True, transcription_language="es")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("PATCH", f"{BASE}/pn_1/voice"))
        self.assertEqual(kwargs["json"], {"forward_to": "", "voicemail_enabled": True, "transcription_language": "es"})

        self.client.list_phone_number_codes("pn_1", since="2026-11-27T10:00:00Z")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url, kwargs["params"]), ("GET", f"{BASE}/pn_1/codes", {"since": "2026-11-27T10:00:00Z"}))

        self.client.prepare_phone_number_whatsapp("pn_1", language="es")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url, kwargs["json"]), ("POST", f"{BASE}/pn_1/whatsapp/prepare", {"language": "es"}))

    def test_a_missing_number_id_fails_before_any_request(self):
        with self.assertRaises(Exception):
            self.client.get_phone_number("")
        self.request.assert_not_called()

    def test_the_phone_webhook_events_can_be_subscribed(self):
        enum = SPEC["components"]["schemas"]["WebhookEventName"]["enum"]
        for event in PHONE_EVENTS:
            with self.subTest(event=event):
                self.assertIn(event, enum)
                self.assertIn(event, SHIPPED)
        doc = " ".join(UploadPostClient.update_notification_config.__doc__.split())
        self.assertIn("phone_number_port_out, phone_number_kyc_comment, phone_number_kyc_resubmitted)", doc)

    def test_a_declined_review_read_it_send_only_the_corrections_answer_the_reviewer(self):
        self.client.get_phone_number_kyc_remediation("pn_1")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("GET", f"{BASE}/pn_1/remediate"))
        self.assertNotIn("json", kwargs)

        documents = {"req_id": {"filename": "id.pdf", "content_base64": "JVBERg=="}}
        self.client.remediate_phone_number_kyc("pn_1", values={"req_tax": "DE2"}, documents=documents,
                                               phone_number="+4930123")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("POST", f"{BASE}/pn_1/remediate"))
        self.assertEqual(kwargs["json"], {"values": {"req_tax": "DE2"}, "documents": documents,
                                          "phone_number": "+4930123"})
        self.assertNotIn("files", kwargs)

        self.client.remediate_phone_number_kyc("pn_1", end_user=END_USER)
        self.assertEqual(self.sent()[2]["json"], {"end_user": END_USER})

        attachments = [{"filename": "id.png", "content_base64": "iVBORw=="}]
        self.client.reply_phone_number_kyc_reviewer("pn_1", "New ID attached", attachments=attachments)
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("POST", f"{BASE}/pn_1/remediate/reply"))
        self.assertEqual(kwargs["json"], {"text": "New ID attached", "attachments": attachments})
        params = inspect.signature(UploadPostClient.reply_phone_number_kyc_reviewer).parameters
        self.assertIs(params["text"].default, inspect.Parameter.empty)

    def test_shareable_kyc_links_create_with_branding_and_redirect_list_revoke(self):
        branding = {"company_name": "Acme", "logo_url": "https://example.com/l.png", "brand_color": "#4F46E5"}
        self.client.create_phone_number_kyc_link("client-a", "ES", "local", "https://example.com/done",
                                                 branding=branding, language="es")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("POST", f"{BASE}/kyc/share"))
        self.assertEqual(kwargs["json"], {
            "profile_username": "client-a", "country": "ES", "number_type": "local",
            "redirect_url": "https://example.com/done", "branding": branding, "language": "es",
        })
        params = inspect.signature(UploadPostClient.create_phone_number_kyc_link).parameters
        for name in ("profile_username", "country", "number_type", "redirect_url"):
            self.assertIs(params[name].default, inspect.Parameter.empty, name)

        self.client.list_phone_number_kyc_links()
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("GET", f"{BASE}/kyc/share"))

        self.client.revoke_phone_number_kyc_link("kl_1")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("DELETE", f"{BASE}/kyc/share/kl_1"))
        self.assertNotIn("json", kwargs)
        calls = self.request.call_count
        with self.assertRaises(Exception):
            self.client.revoke_phone_number_kyc_link("")
        self.assertEqual(self.request.call_count, calls)

    def test_the_hosted_kyc_page_endpoints_are_not_sdk_methods(self):
        for op_id, (_, route, _meta) in UploadPostClient._OPENAPI_OPERATIONS.items():
            self.assertNotIn("phone-kyc", route, op_id)

    def test_a_declined_review_keeps_the_payment_no_text_says_it_is_refunded_at_once(self):
        self.assertNotIn("declined = refunded", SHIPPED)
        self.assertIsNone(re.search(r"declined[^.\n]{0,40}refunded at once",
                                    SHIPPED.replace("no longer refunds at once", ""), re.I))

        def doc(name):
            return " ".join(getattr(UploadPostClient, name).__doc__.split())
        self.assertRegex(doc("submit_phone_number_kyc"), r"the payment is kept, the monthly charge paused; fix it with "
                                                         r"POST .*remediate \(not fixed in 30 days, or released = refunded\)")
        self.assertIn("Never charges again", doc("remediate_phone_number_kyc"))
        self.assertIn("30 days unfixed = cancelled and refunded", doc("remediate_phone_number_kyc"))
        self.assertIn("409 `phone_number_remediation_in_progress` or 503 `phone_numbers_capacity` (payment kept)",
                      doc("remediate_phone_number_kyc"))
        self.assertIn("order_unknown", SPEC["paths"]["/uploadposts/phone-numbers/{number_id}/remediate"]["post"]
                      ["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["order"]["enum"])
        self.assertIn("declined (`regulatory_declined`) cancels the purchase and refunds it", doc("release_phone_number"))
        self.assertIn("billed to YOUR account", doc("create_phone_number_kyc_link"))
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
            readme = fh.read()
        self.assertIn("### Fix a declined identity review\n\nA declined review does not refund at once", readme)
        self.assertIn("### Let your customers verify their identity with a link", readme)
        self.assertIn("purchase is billed to **your** account", readme)
        self.assertIn("(https://docs.upload-post.com/guides/phone-number-kyc-link)", readme)

    def test_purchase_and_kyc_docs_explain_pending_payment_limits_are_integers(self):
        for name in ("purchase_phone_number", "submit_phone_number_kyc"):
            doc = " ".join(getattr(UploadPostClient, name).__doc__.split())
            self.assertIn("`pending_payment` (paid; our carrier is confirming the order", doc, name)
            self.assertIn("Repeating the same `purchase_intent_id` returns the same number", doc, name)
        for name in ("search_available_phone_numbers", "list_phone_number_messages", "list_phone_number_calls"):
            self.assertIn("limit (int, optional)", getattr(UploadPostClient, name).__doc__, name)

    def test_the_shipped_files_do_not_mention_internal_names(self):
        self.assertIsNone(re.search(r"tel[n]yx", SHIPPED, re.I), "the carrier is never named")
        for marker in ("PHONE_NUMBERS_", "UPLOADPOSTS_PHONE", "_ALLOWLIST"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, SHIPPED)


if __name__ == "__main__":
    unittest.main()
