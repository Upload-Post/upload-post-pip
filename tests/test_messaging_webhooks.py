"""Tests for direct messages, AutoDM rules, webhook deliveries, LinkedIn Page
resolution, team act-as and the error details carried by UploadPostError.

No network: the session's HTTP verbs are patched, so every assertion is about
what the client would have sent (or how it reads what came back).

Run with: python -m unittest discover -s tests
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

from upload_post import UploadPostClient, UploadPostError

BASE = "https://api.upload-post.com/api"


def _response(payload=None, status=200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


def _error_response(payload, status, headers=None):
    """A response whose raise_for_status raises like requests does."""
    response = MagicMock()
    response.status_code = status
    response.headers = headers or {}
    if isinstance(payload, Exception):
        response.json.side_effect = payload
    else:
        response.json.return_value = payload
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        f"{status} Error", response=response
    )
    return response


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.get = patch.object(self.client.session, "get",
                                return_value=_response()).start()
        self.post = patch.object(self.client.session, "post",
                                 return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def assertGet(self, endpoint, params):
        url, kwargs = self.get.call_args[0][0], self.get.call_args[1]
        self.assertEqual(url, f"{BASE}{endpoint}")
        self.assertEqual(kwargs["params"], params)

    def assertPostJson(self, endpoint, body):
        url, kwargs = self.post.call_args[0][0], self.post.call_args[1]
        self.assertEqual(url, f"{BASE}{endpoint}")
        self.assertEqual(kwargs["json"], body)


class TestWebhookDeliveries(ClientTestCase):
    def test_list_sends_only_the_filters_given(self):
        self.client.list_webhook_deliveries()
        self.assertGet("/uploadposts/webhooks/deliveries", {})

    def test_list_with_every_filter(self):
        self.client.list_webhook_deliveries(
            event="dm_received", status="failed", request_id="r1", job_id="j1",
            profile_username="my-profile", limit=50, page=2, include_payload=True,
        )
        self.assertGet("/uploadposts/webhooks/deliveries", {
            "event": "dm_received", "status": "failed", "request_id": "r1",
            "job_id": "j1", "profile_username": "my-profile", "limit": 50,
            "page": 2, "include_payload": "true",
        })

    def test_include_payload_false_is_explicit(self):
        self.client.list_webhook_deliveries(include_payload=False)
        self.assertGet("/uploadposts/webhooks/deliveries", {"include_payload": "false"})

    def test_get_one_delivery(self):
        self.client.get_webhook_delivery("3f1c9a0e")
        self.assertEqual(self.get.call_args[0][0],
                         f"{BASE}/uploadposts/webhooks/deliveries/3f1c9a0e")

    def test_redeliver_posts_to_the_delivery(self):
        self.client.redeliver_webhook("3f1c9a0e")
        self.assertEqual(self.post.call_args[0][0],
                         f"{BASE}/uploadposts/webhooks/deliveries/3f1c9a0e/redeliver")

    def test_delivery_id_cannot_escape_its_path_segment(self):
        self.client.redeliver_webhook("../../users")
        self.assertEqual(
            self.post.call_args[0][0],
            f"{BASE}/uploadposts/webhooks/deliveries/..%2F..%2Fusers/redeliver",
        )


class TestNotificationConfig(ClientTestCase):
    """The config lives at /users/notifications (there is no /notification-config)."""

    def test_get_reads_users_notifications(self):
        self.client.get_notification_config()
        self.assertEqual(self.get.call_args[0][0], f"{BASE}/uploadposts/users/notifications")

    def test_update_writes_users_notifications(self):
        self.client.update_notification_config(
            webhook_events=["upload_completed", "dm_received"],
            webhook_url="https://example.com/hook",
            channels={"webhook": True},
        )
        self.assertPostJson("/uploadposts/users/notifications", {
            "webhook_events": ["upload_completed", "dm_received"],
            "webhook_url": "https://example.com/hook",
            "channels": {"webhook": True},
        })


class TestDirectMessages(ClientTestCase):
    def test_bluesky_text_dm(self):
        self.client.send_dm("my-profile", "bluesky",
                            recipient_id="alice.bsky.social", message="hola")
        self.assertPostJson("/uploadposts/dms/send", {
            "platform": "bluesky", "user": "my-profile",
            "recipient_id": "alice.bsky.social", "message": "hola",
        })

    def test_bluesky_action_without_message(self):
        self.client.send_dm("my-profile", "bluesky", conversation_id="c1",
                            sender_action="react", message_id="m1", reaction="🔥")
        self.assertPostJson("/uploadposts/dms/send", {
            "platform": "bluesky", "user": "my-profile", "conversation_id": "c1",
            "sender_action": "react", "message_id": "m1", "reaction": "🔥",
        })

    def test_shared_post_and_reply_to(self):
        post = {"type": "post", "url": "https://bsky.app/profile/a/post/b"}
        self.client.send_dm("my-profile", "bluesky", recipient_id="a",
                            message="look", attachments=post, reply_to="m0")
        body = self.post.call_args[1]["json"]
        self.assertEqual(body["attachments"], post)
        self.assertEqual(body["reply_to"], "m0")

    def test_other_platform_fields_pass_through_and_none_is_dropped(self):
        template = {"name": "hello", "language": "en_US"}
        self.client.send_dm("my-profile", "whatsapp", recipient_id="34600000000",
                            template=template, location=None)
        self.assertPostJson("/uploadposts/dms/send", {
            "platform": "whatsapp", "user": "my-profile",
            "recipient_id": "34600000000", "template": template,
        })

    def test_conversations_with_bluesky_filters(self):
        self.client.get_dm_conversations(
            "my-profile", "bluesky", limit=25, messages_limit=5,
            conversation_id="c1", messages_cursor="mc", status="request",
            read_state="unread",
        )
        self.assertGet("/uploadposts/dms/conversations", {
            "platform": "bluesky", "user": "my-profile", "limit": 25,
            "messages_limit": 5, "conversation_id": "c1",
            "messages_cursor": "mc", "status": "request", "read_state": "unread",
        })

    def test_conversations_minimal_and_extra_params(self):
        self.client.get_dm_conversations("my-profile", "facebook",
                                         facebook_page_id="123", cursor=None)
        self.assertGet("/uploadposts/dms/conversations", {
            "platform": "facebook", "user": "my-profile", "facebook_page_id": "123",
        })


class TestWhatsappDms(ClientTestCase):
    def setUp(self):
        super().setUp()
        self.delete = patch.object(self.client.session, "delete",
                                   return_value=_response()).start()

    def test_send_dm_sends_every_whatsapp_field_as_json(self):
        template = {"name": "order_update", "language": "en_US",
                    "components": [{"type": "body", "parameters": [{"type": "text", "text": "42"}]}]}
        fields = {
            "attachments": [{"type": "image", "media_id": "m1", "caption": "c"},
                            {"type": "document", "url": "https://e.com/a.pdf", "filename": "a.pdf"}],
            "template": template, "reply_to": "wamid.A",
            "location": {"latitude": 40.4, "longitude": -3.7, "name": "Shop"},
            "contacts": [{"name": {"formatted_name": "Ana"}, "phones": [{"phone": "+34600000001"}]}],
            "buttons": [{"title": "Yes", "id": "y"}, "No"],
            "list": {"button": "Options", "sections": [{"rows": [{"id": "r1", "title": "One"}]}]},
            "cta_url": {"display_text": "Open", "url": "https://e.com"},
            "header": "Hi", "footer": "Bye",
            "reaction": {"message_id": "wamid.B", "emoji": "👍"},
            "sender_action": "mark_read", "message_id": "wamid.C", "typing": True,
            "attachment": {"type": "sticker", "media_id": "s1"},
        }
        self.client.send_dm("my-profile", "whatsapp", recipient_id="+34600000000",
                            message="Pick one", **fields)
        self.assertPostJson("/uploadposts/dms/send", dict(
            fields, platform="whatsapp", user="my-profile",
            recipient_id="+34600000000", message="Pick one"))

    def test_upload_dm_media_sends_a_local_file_with_its_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "photo.jpg")
            with open(path, "wb") as fh:
                fh.write(b"JPEGDATA")
            self.client.upload_dm_media("my-profile", path, platform="whatsapp",
                                        type="image", extra_field="kept")
        url, kwargs = self.post.call_args[0][0], self.post.call_args[1]
        self.assertEqual(url, f"{BASE}/uploadposts/dms/media")
        self.assertEqual(dict(kwargs["data"]), {
            "platform": "whatsapp", "user": "my-profile", "type": "image", "extra_field": "kept"})
        name, part = kwargs["files"][0]
        self.assertEqual(name, "file")
        self.assertEqual((part[0], part[2]), ("photo.jpg", "image/jpeg"))
        self.assertTrue(part[1].closed)
        self.assertEqual(kwargs["timeout"], self.client.upload_timeout)

    def test_upload_dm_media_bytes_take_filename_or_content_type(self):
        self.client.upload_dm_media("my-profile", b"PNG", filename="a.png",
                                    platform="facebook", page_id="123")
        kwargs = self.post.call_args[1]
        self.assertEqual(dict(kwargs["data"]), {"platform": "facebook", "user": "my-profile",
                                                "page_id": "123"})
        self.assertEqual(kwargs["files"], [("file", ("a.png", b"PNG", "image/png"))])

        self.client.upload_dm_media("my-profile", b"X", content_type="video/mp4")
        self.assertEqual(self.post.call_args[1]["files"], [("file", ("file", b"X", "video/mp4"))])

    def test_upload_dm_media_refuses_urls_and_missing_files(self):
        for bad in ("https://e.com/a.jpg", "/nope/missing.jpg", None):
            with self.assertRaises(UploadPostError):
                self.client.upload_dm_media("my-profile", bad)
        self.post.assert_not_called()

    def test_templates_query_for_get_and_delete_json_for_create(self):
        self.client.list_dm_templates("my-profile", platform="whatsapp",
                                      status="APPROVED", limit=50)
        self.assertGet("/uploadposts/dms/templates", {
            "platform": "whatsapp", "user": "my-profile", "status": "APPROVED", "limit": 50})

        buttons = [{"text": "Track", "url": "https://e.com/t"},
                   {"text": "Call", "phone_number": "+34600000000"}]
        self.client.create_dm_template("my-profile", "order_update", platform="whatsapp",
                                       category="UTILITY", language="es",
                                       body="Order {{1}} is ready", examples=["42"],
                                       footer="Thanks", buttons=buttons)
        self.assertPostJson("/uploadposts/dms/templates", {
            "platform": "whatsapp", "user": "my-profile", "name": "order_update",
            "category": "UTILITY", "language": "es", "body": "Order {{1}} is ready",
            "examples": ["42"], "footer": "Thanks", "buttons": buttons})

        self.client.delete_dm_template("my-profile", "order_update", platform="whatsapp")
        url, kwargs = self.delete.call_args[0][0], self.delete.call_args[1]
        self.assertEqual(url, f"{BASE}/uploadposts/dms/templates")
        self.assertEqual(kwargs["params"], {
            "platform": "whatsapp", "user": "my-profile", "name": "order_update"})
        self.assertNotIn("json", kwargs)

    def test_business_profile_get_json_update_and_photo_multipart(self):
        self.client.get_whatsapp_business_profile("my-profile")
        self.assertGet("/uploadposts/dms/whatsapp/profile", {"user": "my-profile"})

        self.client.update_whatsapp_business_profile(
            "my-profile", about="Open 9-5", websites=["https://a.com", "https://b.com"],
            vertical="RETAIL")
        self.assertPostJson("/uploadposts/dms/whatsapp/profile", {
            "user": "my-profile", "about": "Open 9-5",
            "websites": ["https://a.com", "https://b.com"], "vertical": "RETAIL"})

        self.client.update_whatsapp_business_profile(
            "my-profile", websites=["https://a.com", "https://b.com"],
            file=b"IMG", filename="logo.png")
        kwargs = self.post.call_args[1]
        self.assertEqual(dict(kwargs["data"]), {
            "user": "my-profile", "websites": "https://a.com,https://b.com"})
        self.assertEqual(kwargs["files"], [("file", ("logo.png", b"IMG", "image/png"))])

    def test_qr_codes_list_create_delete(self):
        self.client.list_whatsapp_qr_codes("my-profile")
        self.assertGet("/uploadposts/dms/whatsapp/qr", {"user": "my-profile"})

        self.client.create_whatsapp_qr_code("my-profile", "Hi!", code="ABC")
        self.assertPostJson("/uploadposts/dms/whatsapp/qr", {
            "user": "my-profile", "prefilled_message": "Hi!", "code": "ABC"})

        self.client.delete_whatsapp_qr_code("my-profile", "ABC")
        url, kwargs = self.delete.call_args[0][0], self.delete.call_args[1]
        self.assertEqual(url, f"{BASE}/uploadposts/dms/whatsapp/qr")
        self.assertEqual(kwargs["params"], {"user": "my-profile", "code": "ABC"})


class TestAutodmRules(ClientTestCase):
    def test_create_minimal(self):
        self.client.create_autodm_rule("my-profile", "Here you go")
        self.assertPostJson("/uploadposts/autodms/rules", {
            "profile_username": "my-profile", "reply_message": "Here you go",
        })

    def test_create_full(self):
        buttons = [{"title": "Guide", "url": "https://example.com"}]
        self.client.create_autodm_rule(
            "my-profile", "Here you go",
            triggers=["comment", "dm_keyword"], trigger_keywords=["guide"],
            buttons=buttons, per_user_cooldown_hours=0,
        )
        self.assertPostJson("/uploadposts/autodms/rules", {
            "profile_username": "my-profile", "reply_message": "Here you go",
            "triggers": ["comment", "dm_keyword"], "trigger_keywords": ["guide"],
            "buttons": buttons, "per_user_cooldown_hours": 0,
        })

    def test_list(self):
        self.client.list_autodm_rules()
        self.assertGet("/uploadposts/autodms/rules", None)
        self.client.list_autodm_rules("my-profile")
        self.assertGet("/uploadposts/autodms/rules", {"profile_username": "my-profile"})

    def test_pause_resume_delete(self):
        for action in ("pause", "resume", "delete"):
            with self.subTest(action=action):
                getattr(self.client, f"{action}_autodm_rule")("rule_1")
                self.assertPostJson(f"/uploadposts/autodms/rules/{action}",
                                    {"rule_id": "rule_1"})


class TestLinkedinAndAnalytics(ClientTestCase):
    def test_resolve_linkedin_organization(self):
        self.client.resolve_linkedin_organization(
            "my-profile", "https://www.linkedin.com/company/linkedin/")
        self.assertGet("/uploadposts/linkedin/resolve-organization", {
            "user": "my-profile", "url": "https://www.linkedin.com/company/linkedin/",
        })

    def test_post_analytics_platform_filter(self):
        self.client.get_post_analytics("req1", platform="tiktok")
        self.assertGet("/uploadposts/post-analytics/req1", {"platform": "tiktok"})

    def test_post_analytics_without_filter(self):
        self.client.get_post_analytics("req1")
        self.assertGet("/uploadposts/post-analytics/req1", None)


class TestActAsUser(unittest.TestCase):
    def test_header_only_when_asked(self):
        self.assertNotIn("X-Act-As-User", UploadPostClient("k").session.headers)
        client = UploadPostClient("k", act_as_user="owner@example.com")
        self.assertEqual(client.session.headers["X-Act-As-User"], "owner@example.com")
        self.assertEqual(client.act_as_user, "owner@example.com")


class TestErrorDetails(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("k")
        self.addCleanup(patch.stopall)

    def _raise(self, response):
        patch.object(self.client.session, "get", return_value=response).start()
        with self.assertRaises(UploadPostError) as ctx:
            self.client.list_autodm_rules()
        return ctx.exception

    def test_team_seat_suspended(self):
        err = self._raise(_error_response({
            "success": False, "code": "TEAM_SEAT_SUSPENDED", "reason": "owner_plan_limit",
            "message": "The account owner's current plan no longer covers your team seat.",
        }, 403))
        self.assertEqual(err.status_code, 403)
        self.assertEqual(err.error_code, "TEAM_SEAT_SUSPENDED")
        self.assertIn("no longer covers", str(err))
        self.assertEqual(err.response["reason"], "owner_plan_limit")

    def test_error_code_and_error_text(self):
        err = self._raise(_error_response({
            "success": False, "error": "This Bluesky app password cannot access direct messages.",
            "error_code": "bluesky_dm_scope_missing",
        }, 403))
        self.assertEqual(err.error_code, "bluesky_dm_scope_missing")
        self.assertEqual(str(err), "API request failed: This Bluesky app password "
                                   "cannot access direct messages.")

    def test_reason_and_retry_after(self):
        err = self._raise(_error_response(
            {"success": False, "message": "This webhook is no longer configured",
             "reason": "webhook_removed"}, 409, headers={"Retry-After": "30"}))
        self.assertEqual(err.error_code, "webhook_removed")
        self.assertEqual(err.retry_after, 30.0)

    def test_non_json_body(self):
        err = self._raise(_error_response(ValueError("no json"), 502))
        self.assertEqual(err.status_code, 502)
        self.assertIsNone(err.error_code)
        self.assertIsNone(err.response)
        self.assertIn("502", str(err))

    def test_no_answer_at_all(self):
        patch.object(self.client.session, "get",
                     side_effect=requests.exceptions.ConnectionError("down")).start()
        with self.assertRaises(UploadPostError) as ctx:
            self.client.list_autodm_rules()
        self.assertIsNone(ctx.exception.status_code)
        self.assertIn("down", str(ctx.exception))

    def test_still_constructible_with_a_message_only(self):
        err = UploadPostError("boom")
        self.assertEqual(str(err), "boom")
        self.assertIsNone(err.error_code)


if __name__ == "__main__":
    unittest.main()
