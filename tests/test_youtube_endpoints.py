"""YouTube resource endpoints (2.17.0): videos, quota, thumbnail, playlists,
captions, comments, search and catalogs, subscriptions/ratings/reports, channel
settings, live broadcasts and streams, live chat; plus the new upload and edit
fields.

No network: the session's HTTP verbs are patched.

Run with: python -m unittest discover -s tests
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient

BASE = "https://api.upload-post.com/api"

# [method, HTTP verb, path, required args, defaults], one row per endpoint.
ROWS = json.loads(r"""[["get_youtube_videos", "GET", "/uploadposts/youtube/videos", ["user"], {}], ["get_youtube_quota", "GET", "/uploadposts/youtube/quota", [], {}], ["set_youtube_thumbnail", "POST", "/uploadposts/youtube/thumbnail", ["user", "video_id"], {}], ["list_youtube_playlists", "GET", "/uploadposts/youtube/playlists", ["user"], {}], ["create_youtube_playlist", "POST", "/uploadposts/youtube/playlists", ["user"], {}], ["update_youtube_playlist", "PATCH", "/uploadposts/youtube/playlists/{playlist_id}", ["user", "playlist_id"], {}], ["delete_youtube_playlist", "DELETE", "/uploadposts/youtube/playlists/{playlist_id}", ["user", "playlist_id"], {}], ["list_youtube_playlist_items", "GET", "/uploadposts/youtube/playlists/{playlist_id}/items", ["user", "playlist_id"], {}], ["add_youtube_playlist_item", "POST", "/uploadposts/youtube/playlists/{playlist_id}/items", ["user", "playlist_id"], {}], ["update_youtube_playlist_item", "PATCH", "/uploadposts/youtube/playlists/{playlist_id}/items/{item_id}", ["user", "playlist_id", "item_id"], {}], ["delete_youtube_playlist_item", "DELETE", "/uploadposts/youtube/playlists/{playlist_id}/items/{item_id}", ["user", "playlist_id", "item_id"], {}], ["get_youtube_playlist_image", "GET", "/uploadposts/youtube/playlists/{playlist_id}/image", ["user", "playlist_id"], {}], ["set_youtube_playlist_image", "POST", "/uploadposts/youtube/playlists/{playlist_id}/image", ["user", "playlist_id"], {}], ["replace_youtube_playlist_image", "PUT", "/uploadposts/youtube/playlists/{playlist_id}/image", ["user", "playlist_id"], {}], ["delete_youtube_playlist_image", "DELETE", "/uploadposts/youtube/playlists/{playlist_id}/image", ["user", "playlist_id"], {}], ["list_youtube_captions", "GET", "/uploadposts/youtube/captions", ["user", "video_id"], {}], ["upload_youtube_caption", "POST", "/uploadposts/youtube/captions", ["user", "video_id"], {}], ["update_youtube_caption", "PUT", "/uploadposts/youtube/captions/{caption_id}", ["user", "caption_id"], {}], ["download_youtube_caption", "GET", "/uploadposts/youtube/captions/{caption_id}/download", ["user", "caption_id"], {}], ["delete_youtube_caption", "DELETE", "/uploadposts/youtube/captions/{caption_id}", ["user", "caption_id"], {}], ["list_youtube_comments", "GET", "/uploadposts/youtube/comments", ["user"], {}], ["list_youtube_comment_replies", "GET", "/uploadposts/youtube/comments/replies", ["user"], {}], ["create_youtube_comment", "POST", "/uploadposts/youtube/comments", ["user", "text"], {}], ["update_youtube_comment", "PATCH", "/uploadposts/youtube/comments/{comment_id}", ["user", "comment_id"], {}], ["delete_youtube_comment", "DELETE", "/uploadposts/youtube/comments/{comment_id}", ["user", "comment_id"], {}], ["moderate_youtube_comments", "POST", "/uploadposts/youtube/comments/moderate", ["user", "comment_ids", "status"], {}], ["search_youtube", "GET", "/uploadposts/youtube/search", ["user"], {}], ["get_youtube_categories", "GET", "/uploadposts/youtube/categories", [], {}], ["get_youtube_languages", "GET", "/uploadposts/youtube/languages", [], {}], ["get_youtube_regions", "GET", "/uploadposts/youtube/regions", [], {}], ["get_youtube_abuse_reasons", "GET", "/uploadposts/youtube/abuse-reasons", [], {}], ["list_youtube_subscriptions", "GET", "/uploadposts/youtube/subscriptions", ["user"], {}], ["subscribe_youtube_channel", "POST", "/uploadposts/youtube/subscriptions", ["user"], {}], ["unsubscribe_youtube_channel", "DELETE", "/uploadposts/youtube/subscriptions/{subscription_id}", ["user", "subscription_id"], {}], ["rate_youtube_video", "POST", "/uploadposts/youtube/videos/{video_id}/rate", ["user", "video_id"], {}], ["get_youtube_rating", "GET", "/uploadposts/youtube/videos/rating", ["user", "ids"], {}], ["report_youtube_video_abuse", "POST", "/uploadposts/youtube/videos/{video_id}/report-abuse", ["user", "video_id", "reason_id"], {}], ["get_youtube_activities", "GET", "/uploadposts/youtube/activities", ["user"], {}], ["get_youtube_channel", "GET", "/uploadposts/youtube/channel", ["user"], {}], ["update_youtube_channel", "PATCH", "/uploadposts/youtube/channel", ["user"], {}], ["lookup_youtube_channel", "GET", "/uploadposts/youtube/channel/lookup", ["user"], {}], ["set_youtube_channel_banner", "POST", "/uploadposts/youtube/channel/banner", ["user"], {}], ["list_youtube_channel_sections", "GET", "/uploadposts/youtube/channel/sections", ["user"], {}], ["create_youtube_channel_section", "POST", "/uploadposts/youtube/channel/sections", ["user"], {}], ["update_youtube_channel_section", "PATCH", "/uploadposts/youtube/channel/sections/{section_id}", ["user", "section_id"], {}], ["delete_youtube_channel_section", "DELETE", "/uploadposts/youtube/channel/sections/{section_id}", ["user", "section_id"], {}], ["set_youtube_watermark", "POST", "/uploadposts/youtube/channel/watermark", ["user"], {}], ["remove_youtube_watermark", "DELETE", "/uploadposts/youtube/channel/watermark", ["user"], {}], ["list_youtube_broadcasts", "GET", "/uploadposts/youtube/live/broadcasts", ["user"], {}], ["create_youtube_broadcast", "POST", "/uploadposts/youtube/live/broadcasts", ["user"], {}], ["get_youtube_broadcast", "GET", "/uploadposts/youtube/live/broadcasts/{broadcast_id}", ["user", "broadcast_id"], {}], ["update_youtube_broadcast", "PATCH", "/uploadposts/youtube/live/broadcasts/{broadcast_id}", ["user", "broadcast_id"], {}], ["delete_youtube_broadcast", "DELETE", "/uploadposts/youtube/live/broadcasts/{broadcast_id}", ["user", "broadcast_id"], {}], ["bind_youtube_broadcast", "POST", "/uploadposts/youtube/live/broadcasts/{broadcast_id}/bind", ["user", "broadcast_id"], {}], ["transition_youtube_broadcast", "POST", "/uploadposts/youtube/live/broadcasts/{broadcast_id}/transition", ["user", "broadcast_id", "status"], {}], ["insert_youtube_cuepoint", "POST", "/uploadposts/youtube/live/broadcasts/{broadcast_id}/cuepoint", ["user", "broadcast_id"], {}], ["list_youtube_streams", "GET", "/uploadposts/youtube/live/streams", ["user"], {}], ["create_youtube_stream", "POST", "/uploadposts/youtube/live/streams", ["user"], {}], ["get_youtube_stream", "GET", "/uploadposts/youtube/live/streams/{stream_id}", ["user", "stream_id"], {}], ["update_youtube_stream", "PATCH", "/uploadposts/youtube/live/streams/{stream_id}", ["user", "stream_id"], {}], ["delete_youtube_stream", "DELETE", "/uploadposts/youtube/live/streams/{stream_id}", ["user", "stream_id"], {}], ["get_youtube_live_chat", "GET", "/uploadposts/youtube/live/chat", ["user"], {}], ["send_youtube_live_chat_message", "POST", "/uploadposts/youtube/live/chat", ["user"], {}], ["close_youtube_live_chat_poll", "POST", "/uploadposts/youtube/live/chat/polls/{message_id}/close", ["user", "message_id"], {}], ["delete_youtube_live_chat_message", "DELETE", "/uploadposts/youtube/live/chat/messages/{message_id}", ["user", "message_id"], {}], ["list_youtube_live_moderators", "GET", "/uploadposts/youtube/live/moderators", ["user"], {}], ["add_youtube_live_moderator", "POST", "/uploadposts/youtube/live/moderators", ["user"], {}], ["remove_youtube_live_moderator", "DELETE", "/uploadposts/youtube/live/moderators/{moderator_id}", ["user", "moderator_id"], {}], ["ban_youtube_live_chat_user", "POST", "/uploadposts/youtube/live/bans", ["user", "channel_id", "type"], {}], ["unban_youtube_live_chat_user", "DELETE", "/uploadposts/youtube/live/bans/{ban_id}", ["user", "ban_id"], {}], ["list_youtube_super_chats", "GET", "/uploadposts/youtube/live/super-chats", ["user"], {}]]""")


def _response(payload=None, text=""):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload if payload is not None else {"success": True}
    response.text = text
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


class TestEveryYoutubeEndpoint(ClientTestCase):
    def test_every_youtube_method_hits_its_endpoint(self):
        for name, verb, route, args, defaults in ROWS:
            with self.subTest(name=name):
                for mock in self.verbs.values():
                    mock.reset_mock()
                getattr(self.client, name)(max_results=5, confirm=True, **{a: f"v_{a}" for a in args})
                path, call = self.sent(verb)
                expected_path = route
                for arg in args:
                    expected_path = expected_path.replace("{%s}" % arg, f"v_{arg}")
                self.assertEqual(path, expected_path)
                expected = dict(defaults, max_results=5, confirm="true" if verb == "GET" else True)
                for arg in args:
                    if "{%s}" % arg not in route:
                        expected[arg] = f"v_{arg}"
                self.assertEqual(call["params"] if verb == "GET" else call["json"], expected)


class TestYoutubeSpecifics(ClientTestCase):
    def test_confirm_is_never_added(self):
        self.client.delete_youtube_playlist("p", "PL1")
        _, call = self.sent("DELETE")
        self.assertEqual(call["json"], {"user": "p"})

    def test_caption_download_returns_text(self):
        self.verbs["get"].return_value = _response(text="1\n00:00:00,000 --> 00:00:01,000\nHola\n")
        text = self.client.download_youtube_caption("p", "AUie", tfmt="srt")
        path, call = self.sent("GET")
        self.assertEqual(path, "/uploadposts/youtube/captions/AUie/download")
        self.assertEqual(call["params"], {"user": "p", "tfmt": "srt"})
        self.assertIn("Hola", text)

    def test_caption_and_images_go_multipart(self):
        self.client.upload_youtube_caption("p", "v1", language="es", file=b"WEBVTT")
        path, call = self.sent("POST")
        self.assertEqual(path, "/uploadposts/youtube/captions")
        self.assertEqual(dict(call["data"]), {"user": "p", "video_id": "v1", "language": "es"})
        self.assertEqual(call["files"], [("file", ("file", b"WEBVTT"))])
        with tempfile.TemporaryDirectory() as tmp:
            image = os.path.join(tmp, "banner.png")
            with open(image, "wb") as fh:
                fh.write(b"png")
            self.client.replace_youtube_playlist_image("p", "PL1", image=image, confirm=True)
            _, call = self.sent("PUT")
        self.assertEqual(dict(call["data"]), {"user": "p", "confirm": "true"})
        self.assertEqual(call["files"][0][1][0], "banner.png")

    def test_message_ids_with_slashes_are_encoded(self):
        self.client.delete_youtube_live_chat_message("p", "a/b", confirm=True)
        path, _ = self.sent("DELETE")
        self.assertEqual(path, "/uploadposts/youtube/live/chat/messages/a%2Fb")

    def test_upload_video_sends_localizations_and_brand_partner(self):
        self.client.upload_video("https://example.com/v.mp4", title="t", user="p", platforms=["youtube"],
                                 youtube_localizations={"es": {"title": "Hola"}},
                                 youtube_brand_partner="UCxxxxxxxxxxxxxxxxxxxxxx")
        _, call = self.sent("POST")
        data = dict(call["data"])
        self.assertEqual(data["youtube_localizations"], '{"es": {"title": "Hola"}}')
        self.assertEqual(data["youtube_brand_partner"], "UCxxxxxxxxxxxxxxxxxxxxxx")


if __name__ == "__main__":
    unittest.main()
