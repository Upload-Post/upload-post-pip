"""Phone numbers (buy a number for WhatsApp, SMS and calls).

Each method sends the request the API expects, and the public texts keep
internal names out. No network: the session is patched.

Run with: python -m unittest discover -s tests
"""

import inspect
import json
import os
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
                "phone_number_declined", "phone_number_released", "phone_number_port_out"]
METHODS = [
    "get_phone_numbers_config", "list_phone_number_countries", "search_available_phone_numbers",
    "purchase_phone_number", "get_phone_number_kyc_fields", "submit_phone_number_kyc", "list_phone_numbers",
    "get_phone_number", "release_phone_number", "update_phone_number_voice", "send_phone_number_sms",
    "list_phone_number_messages", "list_phone_number_calls", "list_phone_number_codes",
    "prepare_phone_number_whatsapp", "get_phone_number_port_out_info", "get_phone_numbers_usage",
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
                                          accept_terms=True, terms_version="2026-11-27",
                                          phone_number="+34600000001")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("POST", f"{BASE}/purchase"))
        self.assertEqual(kwargs["json"], {
            "profile_username": "p", "country": "ES", "number_type": "mobile", "purchase_intent_id": "intent-123456",
            "end_user": END_USER, "accept_terms": True, "terms_version": "2026-11-27", "phone_number": "+34600000001",
        })

    def test_kyc_sends_values_and_base64_documents_in_json(self):
        documents = {"req_id": {"filename": "id.pdf", "content_base64": "JVBERg=="}}
        self.client.submit_phone_number_kyc("p", "DE", "local", "intent-123456", END_USER, True, "2026-11-27",
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

    def test_the_shipped_files_do_not_mention_internal_names(self):
        for marker in ("Telnyx", "telnyx", "PHONE_NUMBERS_", "TELNYX_", "UPLOADPOSTS_PHONE", "_ALLOWLIST"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, SHIPPED)


if __name__ == "__main__":
    unittest.main()
