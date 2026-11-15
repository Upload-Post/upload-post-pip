"""Resource endpoints (2.16.0): post actions, best times, the queue, and the
Telegram, Bluesky and Google Business management endpoints; the new publish
fields (Telegram, Bluesky, Google Business, paid partnership); per-post AutoDM
monitors, profile webhooks and teams.

No network: the session's HTTP verbs are patched, so every assertion is about
what the client would have sent.

Run with: python -m unittest discover -s tests
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient, UploadPostError

BASE = "https://api.upload-post.com/api"

# [method, HTTP verb, path, required args, defaults], one row per endpoint.
ROWS = json.loads(r"""[["edit_post", "POST", "/uploadposts/posts/edit", ["user", "platform", "post_id"], {}], ["repost_post", "POST", "/uploadposts/posts/repost", ["user", "platform"], {}], ["post_action", "POST", "/uploadposts/posts/action", ["user", "platform", "action"], {}], ["save_post", "POST", "/uploadposts/posts/save", ["user", "post_id"], {}], ["get_best_times", "GET", "/uploadposts/best-times", ["profile_username", "platform"], {}], ["get_queue_settings", "GET", "/uploadposts/queue/settings", ["profile_username"], {}], ["update_queue_settings", "POST", "/uploadposts/queue/settings", ["profile_username"], {}], ["get_queue_preview", "GET", "/uploadposts/queue/preview", ["profile_username"], {}], ["get_next_queue_slot", "GET", "/uploadposts/queue/next-slot", ["profile_username"], {}], ["mark_queue_slot_full", "POST", "/uploadposts/queue/slot-full", ["profile_username", "slot_datetime"], {}], ["unmark_queue_slot_full", "DELETE", "/uploadposts/queue/slot-full", ["profile_username", "slot_datetime"], {}], ["get_telegram_chat_info", "GET", "/uploadposts/telegram/chat-info", ["user"], {}], ["update_telegram_chat_info", "PATCH", "/uploadposts/telegram/chat-info", ["user"], {}], ["get_telegram_boosts", "GET", "/uploadposts/telegram/boosts", ["user"], {}], ["get_telegram_member", "GET", "/uploadposts/telegram/members", ["user"], {}], ["moderate_telegram_member", "POST", "/uploadposts/telegram/members", ["user"], {}], ["create_telegram_invite_link", "POST", "/uploadposts/telegram/invite-links", ["user"], {}], ["edit_telegram_invite_link", "PATCH", "/uploadposts/telegram/invite-links", ["user"], {}], ["revoke_telegram_invite_link", "DELETE", "/uploadposts/telegram/invite-links", ["user"], {}], ["create_telegram_primary_invite_link", "POST", "/uploadposts/telegram/invite-links/primary", ["user"], {}], ["answer_telegram_join_request", "POST", "/uploadposts/telegram/join-requests", ["user"], {}], ["get_telegram_topic_icons", "GET", "/uploadposts/telegram/topics/icons", ["user"], {}], ["create_telegram_topic", "POST", "/uploadposts/telegram/topics", ["user"], {}], ["edit_telegram_topic", "PATCH", "/uploadposts/telegram/topics", ["user"], {}], ["delete_telegram_topic", "DELETE", "/uploadposts/telegram/topics", ["user"], {}], ["unpin_all_telegram_messages", "POST", "/uploadposts/telegram/unpin-all", ["user"], {}], ["leave_telegram_chat", "POST", "/uploadposts/telegram/leave", ["user"], {}], ["answer_telegram_suggested_post", "POST", "/uploadposts/telegram/suggested-posts", ["user"], {}], ["get_telegram_user_personal_chat_messages", "GET", "/uploadposts/telegram/users/{user_id}/personal-chat-messages", ["user", "user_id"], {}], ["get_telegram_user_profile_audios", "GET", "/uploadposts/telegram/users/{user_id}/profile-audios", ["user", "user_id"], {}], ["get_telegram_share_theme_backdrops", "GET", "/uploadposts/telegram/share-theme-backdrops", ["user"], {}], ["get_telegram_updates_status", "GET", "/uploadposts/telegram/updates", ["user"], {}], ["get_telegram_bot_profile", "GET", "/uploadposts/telegram/bot-profile", ["user"], {}], ["update_telegram_bot_profile", "PATCH", "/uploadposts/telegram/bot-profile", ["user"], {}], ["get_telegram_bot_commands", "GET", "/uploadposts/telegram/bot-commands", ["user"], {}], ["set_telegram_bot_commands", "POST", "/uploadposts/telegram/bot-commands", ["user"], {}], ["delete_telegram_bot_commands", "DELETE", "/uploadposts/telegram/bot-commands", ["user"], {}], ["get_telegram_sticker_set", "GET", "/uploadposts/telegram/sticker-sets", ["user"], {}], ["create_telegram_sticker_set", "POST", "/uploadposts/telegram/sticker-sets", ["user"], {}], ["edit_telegram_sticker_set", "PATCH", "/uploadposts/telegram/sticker-sets", ["user"], {}], ["delete_telegram_sticker_set", "DELETE", "/uploadposts/telegram/sticker-sets", ["user"], {}], ["upload_telegram_sticker_file", "POST", "/uploadposts/telegram/sticker-sets/upload", ["user"], {}], ["get_telegram_stars", "GET", "/uploadposts/telegram/stars", ["user"], {}], ["get_telegram_star_transactions", "GET", "/uploadposts/telegram/stars/transactions", ["user"], {}], ["send_telegram_invoice", "POST", "/uploadposts/telegram/invoices", ["user"], {}], ["create_telegram_invoice_link", "POST", "/uploadposts/telegram/invoice-links", ["user"], {}], ["refund_telegram_star_payment", "POST", "/uploadposts/telegram/stars/refund", ["user"], {}], ["edit_telegram_star_subscription", "POST", "/uploadposts/telegram/stars/subscription", ["user"], {}], ["get_telegram_available_gifts", "GET", "/uploadposts/telegram/gifts", ["user"], {}], ["get_telegram_owned_gifts", "GET", "/uploadposts/telegram/gifts/owned", ["user"], {}], ["get_telegram_unique_gift", "GET", "/uploadposts/telegram/gifts/unique", ["user"], {}], ["get_telegram_unanswered_payments", "GET", "/uploadposts/telegram/payments/unanswered", ["user"], {}], ["get_post_engagement", "GET", "/uploadposts/post-engagement", ["post_id"], {"platform": "bluesky"}], ["get_bluesky_profiles", "GET", "/uploadposts/bluesky/profile", [], {}], ["search_bluesky_posts", "GET", "/uploadposts/bluesky/search/posts", ["user", "q"], {}], ["search_bluesky_actors", "GET", "/uploadposts/bluesky/search/actors", ["q"], {}], ["get_bluesky_followers", "GET", "/uploadposts/bluesky/followers", [], {}], ["get_bluesky_follows", "GET", "/uploadposts/bluesky/follows", [], {}], ["bluesky_xrpc", "GET", "/uploadposts/bluesky/xrpc/{nsid}", ["nsid"], {}], ["get_bluesky_labels", "GET", "/uploadposts/bluesky/labels", ["user"], {}], ["get_bluesky_notifications", "GET", "/uploadposts/bluesky/notifications", ["user"], {}], ["get_bluesky_unread_count", "GET", "/uploadposts/bluesky/notifications/unread-count", ["user"], {}], ["mark_bluesky_notifications_seen", "POST", "/uploadposts/bluesky/notifications/seen", ["user"], {}], ["get_bluesky_notification_preferences", "GET", "/uploadposts/bluesky/notification-preferences", ["user"], {}], ["update_bluesky_notification_preferences", "POST", "/uploadposts/bluesky/notification-preferences", ["user"], {}], ["get_bluesky_activity_subscriptions", "GET", "/uploadposts/bluesky/activity-subscriptions", ["user"], {}], ["set_bluesky_activity_subscription", "POST", "/uploadposts/bluesky/activity-subscriptions", ["user"], {}], ["get_bluesky_own_profile", "GET", "/uploadposts/bluesky/profile/self", ["user"], {}], ["update_bluesky_profile", "POST", "/uploadposts/bluesky/profile/self", ["user"], {}], ["get_bluesky_status", "GET", "/uploadposts/bluesky/status", ["user"], {}], ["set_bluesky_status", "POST", "/uploadposts/bluesky/status", ["user"], {}], ["clear_bluesky_status", "DELETE", "/uploadposts/bluesky/status", ["user"], {}], ["get_bluesky_settings", "GET", "/uploadposts/bluesky/settings", ["user"], {}], ["update_bluesky_settings", "POST", "/uploadposts/bluesky/settings", ["user"], {}], ["get_bluesky_preferences", "GET", "/uploadposts/bluesky/preferences", ["user"], {}], ["update_bluesky_preferences", "PUT", "/uploadposts/bluesky/preferences", ["user"], {}], ["list_bluesky_drafts", "GET", "/uploadposts/bluesky/drafts", ["user"], {}], ["create_bluesky_draft", "POST", "/uploadposts/bluesky/drafts", ["user"], {}], ["update_bluesky_draft", "PATCH", "/uploadposts/bluesky/drafts/{draft_id}", ["user", "draft_id"], {}], ["delete_bluesky_draft", "DELETE", "/uploadposts/bluesky/drafts/{draft_id}", ["user", "draft_id"], {}], ["get_bluesky_chat_status", "GET", "/uploadposts/dms/bluesky/status", ["user"], {}], ["get_bluesky_chat_preferences", "GET", "/uploadposts/dms/bluesky/preferences", ["user"], {}], ["update_bluesky_chat_preferences", "POST", "/uploadposts/dms/bluesky/preferences", ["user"], {}], ["export_bluesky_chat", "GET", "/uploadposts/dms/bluesky/export", ["user"], {}], ["list_google_business_posts", "GET", "/uploadposts/google-business/posts", ["user"], {}], ["get_google_business_post", "GET", "/uploadposts/google-business/posts/get", ["user"], {}], ["list_google_business_reviews", "GET", "/uploadposts/google-business/reviews", ["user"], {}], ["get_google_business_review", "GET", "/uploadposts/google-business/reviews/get", ["user"], {}], ["batch_get_google_business_reviews", "GET", "/uploadposts/google-business/reviews/batch", ["user"], {}], ["reply_to_google_business_review", "PUT", "/uploadposts/google-business/reviews/reply", ["user", "comment"], {}], ["delete_google_business_review_reply", "DELETE", "/uploadposts/google-business/reviews/reply", ["user"], {}], ["list_google_business_media", "GET", "/uploadposts/google-business/media", ["user"], {}], ["get_google_business_media", "GET", "/uploadposts/google-business/media/get", ["user"], {}], ["upload_google_business_media", "POST", "/uploadposts/google-business/media", ["user"], {}], ["update_google_business_media", "PATCH", "/uploadposts/google-business/media", ["user"], {}], ["delete_google_business_media", "DELETE", "/uploadposts/google-business/media", ["user"], {}], ["list_google_business_customer_media", "GET", "/uploadposts/google-business/media/customers", ["user"], {}], ["get_google_business_customer_media", "GET", "/uploadposts/google-business/media/customers/get", ["user"], {}], ["get_google_business_performance", "GET", "/uploadposts/google-business/performance", ["user"], {}], ["get_google_business_search_keywords", "GET", "/uploadposts/google-business/performance/keywords", ["user"], {}], ["get_google_business_location_info", "GET", "/uploadposts/google-business/location-info", ["user"], {}], ["update_google_business_location_info", "PATCH", "/uploadposts/google-business/location-info", ["user"], {}], ["get_google_business_google_updates", "GET", "/uploadposts/google-business/location-info/google-updated", ["user"], {}], ["answer_google_business_google_updates", "POST", "/uploadposts/google-business/location-info/google-updates", ["user", "decision", "fields"], {}], ["get_google_business_location_info_extended", "GET", "/uploadposts/google-business/location-info/extended", ["user"], {}], ["list_google_business_locations", "GET", "/uploadposts/google-business/locations/list", ["user"], {}], ["get_google_business_pinned_location", "GET", "/uploadposts/users/google-business-location", ["profile_username"], {}], ["pin_google_business_location", "POST", "/uploadposts/users/google-business-location", ["profile_username", "gbp_location_id"], {}], ["clear_google_business_location_pin", "DELETE", "/uploadposts/users/google-business-location", ["profile_username"], {}], ["search_google_business_categories", "GET", "/uploadposts/google-business/categories", [], {}], ["batch_get_google_business_categories", "GET", "/uploadposts/google-business/categories/batch", [], {}], ["search_google_business_chains", "GET", "/uploadposts/google-business/chains", [], {}], ["get_google_business_chain", "GET", "/uploadposts/google-business/chains/get", [], {}], ["search_google_business_google_locations", "POST", "/uploadposts/google-business/google-locations/search", ["user"], {}], ["get_google_business_recommended_locations", "GET", "/uploadposts/google-business/google-locations/recommended", ["user"], {}], ["report_google_business_google_location", "POST", "/uploadposts/google-business/google-locations/report", ["user"], {}], ["get_google_business_available_attributes", "GET", "/uploadposts/google-business/attributes/available", ["user"], {}], ["get_google_business_attributes", "GET", "/uploadposts/google-business/attributes", ["user"], {}], ["update_google_business_attributes", "PATCH", "/uploadposts/google-business/attributes", ["user"], {}], ["get_google_business_attributes_google_updated", "GET", "/uploadposts/google-business/attributes/google-updated", ["user"], {}], ["get_google_business_attributes_extended", "GET", "/uploadposts/google-business/attributes/extended", ["user"], {}], ["get_google_business_place_action_types", "GET", "/uploadposts/google-business/place-actions/types", ["user"], {}], ["list_google_business_place_actions", "GET", "/uploadposts/google-business/place-actions", ["user"], {}], ["get_google_business_place_action", "GET", "/uploadposts/google-business/place-actions/get", ["user"], {}], ["create_google_business_place_action", "POST", "/uploadposts/google-business/place-actions", ["user"], {}], ["update_google_business_place_action", "PATCH", "/uploadposts/google-business/place-actions", ["user"], {}], ["delete_google_business_place_action", "DELETE", "/uploadposts/google-business/place-actions", ["user"], {}], ["get_google_business_food_menus", "GET", "/uploadposts/google-business/food-menus", ["user"], {}], ["update_google_business_food_menus", "PUT", "/uploadposts/google-business/food-menus", ["user"], {}], ["get_google_business_services", "GET", "/uploadposts/google-business/services", ["user"], {}], ["update_google_business_services", "PUT", "/uploadposts/google-business/services", ["user"], {}], ["get_google_business_lodging", "GET", "/uploadposts/google-business/lodging", ["user"], {}], ["update_google_business_lodging", "PATCH", "/uploadposts/google-business/lodging", ["user"], {}], ["get_google_business_lodging_google_updated", "GET", "/uploadposts/google-business/lodging/google-updated", ["user"], {}], ["list_google_business_accounts", "GET", "/uploadposts/google-business/accounts", ["user"], {}], ["get_google_business_account", "GET", "/uploadposts/google-business/accounts/get", ["user"], {}], ["create_google_business_account", "POST", "/uploadposts/google-business/accounts", ["user"], {}], ["list_google_business_admins", "GET", "/uploadposts/google-business/admins", ["user"], {}], ["list_google_business_invitations", "GET", "/uploadposts/google-business/invitations", ["user"], {}], ["get_google_business_verification_state", "GET", "/uploadposts/google-business/verification/state", ["user"], {}], ["get_google_business_verification_options", "POST", "/uploadposts/google-business/verification/options", ["user"], {}], ["list_google_business_verifications", "GET", "/uploadposts/google-business/verifications", ["user"], {}]]""")


def _response(payload=None):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.verbs = {}
        for verb in ("get", "post", "patch", "put", "delete"):
            self.verbs[verb] = patch.object(self.client.session, verb, return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def sent(self, verb):
        mock = self.verbs[verb.lower()]
        self.assertTrue(mock.called, f"{verb} was not called")
        return mock.call_args[0][0].replace(BASE, ""), mock.call_args[1]


class TestEveryEndpoint(ClientTestCase):
    def test_every_resource_method_hits_its_endpoint(self):
        for name, verb, route, args, defaults in ROWS:
            with self.subTest(name=name):
                for mock in self.verbs.values():
                    mock.reset_mock()
                kwargs = {arg: f"v_{arg}" for arg in args}
                getattr(self.client, name)(page_size=5, include_extra=True, **kwargs)
                path, call = self.sent(verb)
                expected_path = route
                for arg in args:
                    expected_path = expected_path.replace("{%s}" % arg, f"v_{arg}")
                self.assertEqual(path, expected_path)
                expected = dict(defaults, page_size=5)
                expected["include_extra"] = "true" if verb == "GET" else True
                for arg in args:
                    if "{%s}" % arg not in route:
                        expected[arg] = f"v_{arg}"
                self.assertEqual(call["params"] if verb == "GET" else call["json"], expected)


class TestResourceHelper(ClientTestCase):
    def test_get_joins_lists_and_lowercases_booleans(self):
        self.client.get_google_business_performance(
            "shop", metrics=["call_clicks", "website_clicks"], daily_range={"a": 1}, refresh=False, skip=None)
        _, call = self.sent("GET")
        self.assertEqual(call["params"], {
            "user": "shop", "metrics": "call_clicks,website_clicks", "daily_range": '{"a": 1}', "refresh": "false"})

    def test_path_parameter_is_required_and_encoded(self):
        with self.assertRaises(UploadPostError):
            self.client.update_bluesky_draft("p", "")
        self.client.bluesky_xrpc("app.bsky.feed.getAuthorFeed", actor="alice.bsky.social")
        path, call = self.sent("GET")
        self.assertEqual(path, "/uploadposts/bluesky/xrpc/app.bsky.feed.getAuthorFeed")
        self.assertEqual(call["params"], {"actor": "alice.bsky.social"})

    def test_local_file_goes_multipart_and_is_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "front.jpg")
            with open(path, "wb") as fh:
                fh.write(b"jpeg")
            self.client.upload_google_business_media("shop", file=path, category="EXTERIOR", dry_run=False)
            url, call = self.sent("POST")
        self.assertEqual(url, "/uploadposts/google-business/media")
        self.assertEqual(dict(call["data"]), {"user": "shop", "category": "EXTERIOR", "dry_run": "false"})
        name, (filename, handle) = call["files"][0]
        self.assertEqual((name, filename), ("file", "front.jpg"))
        self.assertTrue(handle.closed)

    def test_bytes_on_patch_go_multipart(self):
        self.client.update_telegram_chat_info("p", photo=b"img", permissions={"can_send_messages": True})
        _, call = self.sent("PATCH")
        self.assertEqual(dict(call["data"]), {"user": "p", "permissions": '{"can_send_messages": true}'})
        self.assertEqual(call["files"], [("photo", ("photo", b"img"))])

    def test_url_in_file_field_stays_json(self):
        self.client.upload_google_business_media("shop", file="https://example.com/a.jpg")
        _, call = self.sent("POST")
        self.assertEqual(call["json"], {"user": "shop", "file": "https://example.com/a.jpg"})

    def test_put_sends_json(self):
        self.client.reply_to_google_business_review("shop", "Thanks!", review_name="accounts/1/locations/2/reviews/3")
        path, call = self.sent("PUT")
        self.assertEqual(path, "/uploadposts/google-business/reviews/reply")
        self.assertEqual(call["json"], {"user": "shop", "comment": "Thanks!", "review_name": "accounts/1/locations/2/reviews/3"})

    def test_post_engagement_defaults_to_bluesky(self):
        self.client.get_post_engagement("at://x")
        _, call = self.sent("GET")
        self.assertEqual(call["params"], {"platform": "bluesky", "post_id": "at://x"})

    def test_queue_auto_slots(self):
        self.client.update_queue_settings("p", slots="auto", auto_slots_count=3, auto_platforms=["instagram"])
        _, call = self.sent("POST")
        self.assertEqual(call["json"], {"profile_username": "p", "slots": "auto", "auto_slots_count": 3,
                                        "auto_platforms": ["instagram"]})

    def test_unpublish_passes_extra_fields(self):
        self.client.unpublish_post("p", "telegram", "42", delete_all_messages=True)
        _, call = self.sent("POST")
        self.assertEqual(call["json"], {"user": "p", "platform": "telegram", "post_id": "42",
                                        "delete_all_messages": True})

    def test_select_location_pins_it(self):
        self.client.select_google_business_location("locations/1", "acme")
        path, call = self.sent("POST")
        self.assertEqual(path, "/uploadposts/users/google-business-location")
        self.assertEqual(call["json"], {"profile_username": "acme", "gbp_location_id": "locations/1"})


class TestAutodmMonitorsWebhooksTeams(ClientTestCase):
    def test_start_autodm(self):
        self.client.start_autodm("p", "Thanks!", platform="tiktok", post_id="7", trigger_keywords=["info"])
        path, call = self.sent("POST")
        self.assertEqual(path, "/uploadposts/autodms/start")
        self.assertEqual(call["json"], {"profile_username": "p", "reply_message": "Thanks!", "platform": "tiktok",
                                        "post_id": "7", "trigger_keywords": ["info"]})

    def test_monitor_actions(self):
        for action in ("stop", "pause", "resume", "delete"):
            getattr(self.client, f"{action}_autodm")("m1")
            path, call = self.sent("POST")
            self.assertEqual(path, f"/uploadposts/autodms/{action}")
            self.assertEqual(call["json"], {"monitor_id": "m1"})

    def test_status_and_logs(self):
        self.client.get_autodm_status(include_inactive=True)
        path, call = self.sent("GET")
        self.assertEqual((path, call["params"]), ("/uploadposts/autodms/status", {"include_inactive": "true"}))
        self.client.get_autodm_logs("m1")
        path, call = self.sent("GET")
        self.assertEqual((path, call["params"]), ("/uploadposts/autodms/logs", {"monitor_id": "m1"}))

    def test_profile_webhooks_and_teams(self):
        self.client.set_profile_webhook("p", "https://hook", webhook_events=["upload_completed"])
        path, call = self.sent("POST")
        self.assertEqual(path, "/uploadposts/users/profile-webhook")
        self.assertEqual(call["json"], {"profile_username": "p", "webhook_url": "https://hook",
                                        "webhook_events": ["upload_completed"]})
        self.client.delete_profile_webhook("p")
        path, call = self.sent("DELETE")
        self.assertEqual((path, call["json"]), ("/uploadposts/users/profile-webhook", {"profile_username": "p"}))
        self.client.rotate_webhook_secret()
        self.assertEqual(self.sent("POST")[0], "/uploadposts/users/webhook-secret")
        self.client.list_team_members()
        self.assertEqual(self.sent("GET")[0], "/uploadposts/teams/members")
        self.client.list_shared_accounts()
        self.assertEqual(self.sent("GET")[0], "/uploadposts/teams/shared-with-me")


class TestPublishFields(ClientTestCase):
    def _text(self, platforms, **kwargs):
        self.client.upload_text(title="hi", user="p", platforms=platforms, **kwargs)
        _, call = self.sent("POST")
        last, lists = {}, {}
        for key, value in call["data"]:
            last[key] = value
            lists.setdefault(key, []).append(value)
        return last, lists

    def test_telegram(self):
        last, _ = self._text(
            ["telegram"], telegram_poll={"question": "Q?", "options": ["a", "b"]}, telegram_dice=True,
            telegram_pin=True, telegram_reply_to_message_id=7, telegram_title="Texto", telegram_first_comment="c",
            telegram_link_preview_options={"is_disabled": True})
        self.assertEqual(last["telegram_poll"], '{"question": "Q?", "options": ["a", "b"]}')
        self.assertEqual(last["telegram_dice"], "true")
        self.assertEqual(last["telegram_pin"], "true")
        self.assertEqual(last["telegram_reply_to_message_id"], "7")
        self.assertEqual(last["telegram_title"], "Texto")
        self.assertEqual(last["telegram_first_comment"], "c")
        self.assertEqual(last["telegram_link_preview_options"], '{"is_disabled": true}')

    def test_telegram_fields_only_with_telegram(self):
        last, _ = self._text(["x"], telegram_poll={"question": "Q?"})
        self.assertNotIn("telegram_poll", last)

    def test_bluesky(self):
        last, _ = self._text(["bluesky"], bluesky_tags=["a", "b"], bluesky_created_at="2024-05-01T10:30:00Z",
                             bluesky_thread_overflow=True, bluesky_video_presentation="gif")
        self.assertEqual(last["bluesky_tags"], '["a", "b"]')
        self.assertEqual(last["bluesky_created_at"], "2024-05-01T10:30:00Z")
        self.assertEqual(last["bluesky_thread_overflow"], "true")
        self.assertEqual(last["bluesky_video_presentation"], "gif")

    def test_google_business(self):
        last, lists = self._text(
            ["google_business"], gbp_topic_type="EVENT", gbp_recurrence="WEEKLY", gbp_recurrence_days="MON,THU",
            gbp_recurrence_end="2027-01-01", gbp_scheduled_time="2026-12-01T10:00:00+01:00", gbp_multi_media=True,
            gbp_media_url=["https://a/1.jpg", "https://a/2.jpg"], gbp_alert_type="COVID_19")
        self.assertEqual(last["gbp_recurrence"], "WEEKLY")
        self.assertEqual(last["gbp_recurrence_days"], "MON,THU")
        self.assertEqual(last["gbp_recurrence_end"], "2027-01-01")
        self.assertEqual(last["gbp_scheduled_time"], "2026-12-01T10:00:00+01:00")
        self.assertEqual(last["gbp_multi_media"], "true")
        self.assertEqual(lists["gbp_media_url[]"], ["https://a/1.jpg", "https://a/2.jpg"])
        self.assertEqual(last["gbp_alert_type"], "COVID_19")

    def test_paid_partnership(self):
        last, _ = self._text(["facebook", "x"], paid_partnership=True, facebook_sponsor_id="123")
        self.assertEqual(last["paid_partnership"], "true")
        self.assertEqual(last["facebook_sponsor_id"], "123")

    def test_tiktok_disclosure_and_pinterest_sponsor_on_photos(self):
        self.client.upload_photos(["https://example.com/a.jpg"], user="p", platforms=["tiktok", "pinterest"],
                                  disclose_commercial=True, branded_content=True, pinterest_sponsor_id="9")
        _, call = self.sent("POST")
        last = dict(call["data"])
        self.assertEqual(last["disclose_commercial"], "true")
        self.assertEqual(last["branded_content"], "true")
        self.assertEqual(last["pinterest_sponsor_id"], "9")


if __name__ == "__main__":
    unittest.main()
