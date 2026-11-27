"""The client offers only what is switched on in production.

Features that are built but off there (codegen/sdk-map.json "excluded",
test_upload_fields NOT_SENT) must not reach the client: customers ask for them
and they cannot be turned on for them. The ones switched on on 2026-11-25 are
sent here.

Run with: python -m unittest discover -s tests
"""

import json
import os
import re
import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "codegen", "sdk-map.json"), encoding="utf-8") as fh:
    MAP = json.load(fh)
SHIPPED = ""
for name in ("upload_post/api_client.py", "README.md"):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        SHIPPED += fh.read()

OFF_MARKERS = [
    "/ads/meta", "spark/authorize-post", "tiktok_spark_scope_missing", "authorization_days", "Spark Ads permission", "instagram_mention_received", "message_reactions", "messaging_seen", "messaging_referral", "instagram_connection", "instagram/audio", "business-discovery",
    "collaboration-invites", "threads/locations", "threads/mentions", "threads/search", "threads/profiles",
    "pending-replies", "geo-gating", "linkedin/reactions", "member-analytics", "tiktok/mentions", "ad-authorization",
    "visitor-posts", "whatsapp/flows", "participant_ids", "include_users", "instagram_paid_partnership",
    "threads_location_id", "facebook_tags", "| /catalogs", "terms/related", "trends/keywords",
]

SWITCHED_ON = [
    "getFacebookInsights", "listFacebookPageRatings", "listFacebookPageTaggedPosts", "listFacebookVideoCaptions",
    "updateFacebookVideoCaptions", "readPinterestApi", "postPinterestApi", "patchPinterestApi", "deletePinterestApi",
    "listThreadsGhostPosts", "listInstagramStories", "listInstagramTaggedMedia", "editWhatsappTemplate",
    "listWhatsappBlockedUsers", "blockWhatsappUsers", "unblockWhatsappUsers", "getWhatsappAutomation",
    "setWhatsappAutomation", "getWhatsappNumber", "updateWhatsappNumber", "getWhatsappAnalytics",
    "enableWhatsappTemplateInsights", "listWhatsappTemplateLibrary", "getInstagramMessagingProfile",
    "setInstagramMessagingProfile", "deleteInstagramMessagingProfile", "getXMentions", "readX", "manageXLists",
]


def snake(name):
    for a, b in (("LinkedIn", "Linkedin"), ("OAuth", "Oauth")):
        name = name.replace(a, b)
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


class TestOffIsNotInTheClient(unittest.TestCase):
    def test_no_method_for_an_excluded_operation(self):
        for op_id in MAP["excluded"]:
            with self.subTest(operation=op_id):
                self.assertNotIn(op_id, UploadPostClient._OPENAPI_OPERATIONS)
                self.assertFalse(hasattr(UploadPostClient, snake(op_id)))

    def test_no_mention_of_what_is_off(self):
        for marker in OFF_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, SHIPPED)


class TestSwitchedOn(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("k")
        response = MagicMock()
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        self.post = patch.object(self.client.session, "post", return_value=response).start()
        self.get = patch.object(self.client.session, "get", return_value=response).start()
        # Generated methods go through session.request: never reach the real API.
        self.request = patch.object(self.client.session, "request", return_value=response).start()
        self.addCleanup(patch.stopall)

    def form(self):
        out = {}
        for key, value in self.post.call_args[1].get("data") or []:
            out.setdefault(key, []).append(value)
        return out

    def test_generated_methods(self):
        for op_id in SWITCHED_ON:
            with self.subTest(operation=op_id):
                self.assertTrue(callable(getattr(self.client, snake(op_id))))
                self.assertFalse(UploadPostClient._OPENAPI_OPERATIONS[op_id][2].get("na"))

    def test_threads_text_post(self):
        self.client.upload_text(title="t", user="u", platforms=["threads"], threads_gif_id="g1",
                                threads_text_spoilers=[{"offset": 0, "length": 4}], threads_ghost_post=True)
        f = self.form()
        self.assertEqual(f["threads_gif_id"], ["g1"])
        self.assertEqual(f["threads_text_spoilers"], ['[{"offset": 0, "length": 4}]'])
        self.assertEqual(f["threads_ghost_post"], ["true"])

    def test_threads_spoiler_media(self):
        self.client.upload_photos(["https://example.com/a.jpg"], title="t", user="u", platforms=["threads"],
                                  threads_spoiler_media=True)
        self.assertEqual(self.form()["threads_spoiler_media"], ["true"])

    def test_facebook_backdating(self):
        self.client.upload_text(title="t", user="u", platforms=["facebook"], facebook_backdated_time="2024-01-02",
                                facebook_backdated_time_granularity="day")
        f = self.form()
        self.assertEqual(f["facebook_backdated_time"], ["2024-01-02"])
        self.assertEqual(f["facebook_backdated_time_granularity"], ["day"])

    def test_x_video_card_and_clip(self):
        self.client.upload_video("https://example.com/v.mp4", title="t", user="u", platforms=["x"],
                                 x_video_title="T", x_video_cta="visit_site", x_video_cta_url="https://example.com")
        f = self.form()
        self.assertEqual(f["x_video_title"], ["T"])
        self.assertEqual(f["x_video_cta"], ["visit_site"])
        self.client.upload_text(title="t", user="u", platforms=["x"], x_clip_post_id="9", x_clip_start_seconds=10,
                                x_clip_end_seconds=30)
        f = self.form()
        self.assertEqual(f["x_clip_post_id"], ["9"])
        self.assertEqual(f["x_clip_start_seconds"], ["10"])

    def test_instagram_video_through_upload_photos(self):
        self.client.upload_photos(["https://example.com/v.mp4"], title="t", user="u", platforms=["instagram"],
                                  cover_url="https://example.com/c.jpg", thumb_offset=1500, share_to_feed=False,
                                  audio_name="Song")
        f = self.form()
        self.assertEqual(f["cover_url"], ["https://example.com/c.jpg"])
        self.assertEqual(f["thumb_offset"], ["1500"])
        self.assertEqual(f["share_to_feed"], ["false"])
        self.assertEqual(f["audio_name"], ["Song"])

    def test_create_comment_image_url(self):
        self.client.create_comment(user="u", platform="tiktok", message="hi", post_id="1",
                                   image_url="https://example.com/a.jpg")
        self.assertEqual(self.post.call_args[1]["json"]["image_url"], "https://example.com/a.jpg")

    def test_suggestions_trending(self):
        self.client.get_suggestions(user="u", platform="tiktok", type="trending", personalized=True)
        params = self.get.call_args[1]["params"]
        self.assertEqual(params["type"], "trending")
        self.assertEqual(params["personalized"], "true")

    def test_send_dm_whatsapp_extras(self):
        self.client.send_dm(user="u", platform="whatsapp", recipient_id="34600000000", message="Hi",
                            flow={"flow_id": "f1", "cta": "Open"}, location_request=True,
                            carousel=[{"media_url": "https://example.com/a.jpg", "media_type": "image"}],
                            call_button={"display_text": "Call"})
        body = self.post.call_args[1]["json"]
        self.assertEqual(body["flow"], {"flow_id": "f1", "cta": "Open"})
        self.assertIs(body["location_request"], True)
        self.assertEqual(len(body["carousel"]), 1)
        self.assertEqual(body["call_button"], {"display_text": "Call"})

    def test_read_x(self):
        self.client.read_x("search_recent", "u", query="upload")
        args, kwargs = self.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith("/uploadposts/x/read/search_recent"))
        self.assertEqual(kwargs["params"]["query"], "upload")

    def test_instagram_top_level_comment(self):
        self.client.create_comment(user="u", platform="instagram", message="hi", post_id="1789")
        body = self.post.call_args[1]["json"]
        self.assertEqual(body["post_id"], "1789")
        self.assertNotIn("comment_id", body)

    def test_instagram_messaging_profile(self):
        self.client.set_instagram_messaging_profile(user="u", ice_breakers=[{"question": "Hours?", "payload": "HOURS"}])
        args, kwargs = self.request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/uploadposts/dms/instagram/profile"))
        self.assertEqual(kwargs["json"]["ice_breakers"], [{"question": "Hours?", "payload": "HOURS"}])
        self.client.delete_instagram_messaging_profile(user="u", fields=["persistent_menu"], confirm=True)
        self.assertEqual(self.request.call_args[0][0], "DELETE")
        self.client.get_instagram_messaging_profile(user="u")
        self.assertEqual(self.request.call_args[0][0], "GET")

    def test_read_x_reposts_of_me(self):
        self.client.read_x("reposts_of_me", "u")
        self.assertTrue(self.request.call_args[0][1].endswith("/uploadposts/x/read/reposts_of_me"))


if __name__ == "__main__":
    unittest.main()
