"""Tests for the TikTok surface.

Comments now go through the multi-platform endpoints, and TikTok has its own
insight and discovery calls. No network: the session's HTTP verbs are patched,
so every assertion is about what the client would have sent.

Run with: python -m unittest discover -s tests
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient, UploadPostError


def _response(payload=None, status=200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


class TikTokTestCase(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.get = patch.object(self.client.session, "get",
                                return_value=_response()).start()
        self.post = patch.object(self.client.session, "post",
                                 return_value=_response()).start()
        self.delete = patch.object(self.client.session, "delete",
                                   return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def assertGet(self, mock, endpoint, params):
        url, kwargs = mock.call_args[0][0], mock.call_args[1]
        self.assertEqual(url, f"https://api.upload-post.com/api{endpoint}")
        self.assertEqual(kwargs["params"], params)


class TestCommentsAcceptTikTok(TikTokTestCase):
    """The generic /comments endpoints now take platform="tiktok"."""

    def test_get_post_comments(self):
        self.client.get_post_comments(
            user="my-profile", platform="tiktok",
            post_id="7412345678901234567", limit=20,
        )
        self.assertGet(self.get, "/uploadposts/comments", {
            "platform": "tiktok", "user": "my-profile",
            "post_id": "7412345678901234567", "limit": 20,
        })

    def test_create_comment(self):
        self.client.create_comment(
            user="my-profile", platform="tiktok", post_id="741", message="hola"
        )
        self.assertEqual(self.post.call_args[1]["json"], {
            "platform": "tiktok", "user": "my-profile",
            "message": "hola", "post_id": "741",
        })

    def test_delete_comment(self):
        self.client.delete_comment(
            user="my-profile", platform="tiktok", comment_id="99"
        )
        self.assertEqual(self.delete.call_args[1]["json"], {
            "platform": "tiktok", "user": "my-profile", "comment_id": "99",
        })


class TestFirstComment(TikTokTestCase):
    def test_tiktok_first_comment_is_forwarded_like_the_rest(self):
        data = []
        self.client._add_common_params(
            data, user="my-profile", title="hi", platforms=["tiktok"],
            first_comment="shared",
            tiktok_first_comment="solo TikTok",
            instagram_first_comment="solo IG",
        )
        fields = dict(data)
        self.assertEqual(fields["first_comment"], "shared")
        self.assertEqual(fields["tiktok_first_comment"], "solo TikTok")
        self.assertEqual(fields["instagram_first_comment"], "solo IG")

    def test_tiktok_is_not_filtered_out_of_the_upload(self):
        self.client.upload_text(
            user="my-profile", platforms=["tiktok"], title="hi",
            tiktok_first_comment="primero",
        )
        fields = dict(self.post.call_args[1]["data"])
        self.assertEqual(fields["tiktok_first_comment"], "primero")


class TestCommentRepliesAndActions(TikTokTestCase):
    def test_replies_send_video_comment_and_cursor(self):
        self.client.get_tiktok_comment_replies(
            "my-profile", "741", "99", limit=20, cursor="abc"
        )
        self.assertGet(self.get, "/uploadposts/tiktok/comments/replies", {
            "profile": "my-profile", "post_id": "741", "comment_id": "99",
            "limit": 20, "cursor": "abc",
        })

    def test_replies_omit_the_optional_params(self):
        self.client.get_tiktok_comment_replies("my-profile", "741", "99")
        self.assertGet(self.get, "/uploadposts/tiktok/comments/replies", {
            "profile": "my-profile", "post_id": "741", "comment_id": "99",
        })

    def test_hide_and_pin_carry_the_video(self):
        for action_type, action in (("hide", "HIDE"), ("pin", "UNPIN")):
            with self.subTest(action_type=action_type):
                self.client.tiktok_comment_action(
                    "my-profile", action_type=action_type, action=action,
                    comment_id="99", post_id="741",
                )
                self.assertEqual(self.post.call_args[0][0],
                                 "https://api.upload-post.com/api"
                                 "/uploadposts/tiktok/comments/action")
                self.assertEqual(self.post.call_args[1]["json"], {
                    "profile": "my-profile", "type": action_type,
                    "comment_id": "99", "action": action, "post_id": "741",
                })

    def test_like_never_carries_the_video(self):
        self.client.tiktok_comment_action(
            "my-profile", action_type="like", action="LIKE",
            comment_id="99", post_id="741",
        )
        self.assertEqual(self.post.call_args[1]["json"], {
            "profile": "my-profile", "type": "like",
            "comment_id": "99", "action": "LIKE",
        })


class TestInsightsAndDiscovery(TikTokTestCase):
    def test_search_keywords(self):
        self.client.search_tiktok_keywords("my-profile", "pilates")
        self.assertGet(self.get, "/uploadposts/tiktok/search/keywords", {
            "profile": "my-profile", "q": "pilates",
        })

    def test_insights_window(self):
        self.client.get_tiktok_insights(
            "my-profile", start_date="2026-07-01", end_date="2026-07-30"
        )
        self.assertGet(self.get, "/uploadposts/tiktok/insights", {
            "profile": "my-profile",
            "start_date": "2026-07-01", "end_date": "2026-07-30",
        })

    def test_insights_default_window_is_left_to_the_api(self):
        self.client.get_tiktok_insights("my-profile")
        self.assertGet(self.get, "/uploadposts/tiktok/insights",
                       {"profile": "my-profile"})

    def test_video_insights_paginate(self):
        self.client.get_tiktok_video_insights("my-profile", limit=20, cursor="xyz")
        self.assertGet(self.get, "/uploadposts/tiktok/videos/insights", {
            "profile": "my-profile", "limit": 20, "cursor": "xyz",
        })

    def test_hashtags_take_country_and_language(self):
        self.client.get_tiktok_hashtags(
            "my-profile", "pilates", country_code="ES", language="es"
        )
        self.assertGet(self.get, "/uploadposts/tiktok/hashtags", {
            "profile": "my-profile", "q": "pilates",
            "country_code": "ES", "language": "es",
        })

    def test_benchmark_without_category_lists_the_categories(self):
        self.client.get_tiktok_benchmark("my-profile")
        self.assertGet(self.get, "/uploadposts/tiktok/benchmark",
                       {"profile": "my-profile"})

    def test_benchmark_with_category_compares(self):
        self.client.get_tiktok_benchmark("my-profile", "SOFTWARE_AND_APPS")
        self.assertGet(self.get, "/uploadposts/tiktok/benchmark", {
            "profile": "my-profile", "category": "SOFTWARE_AND_APPS",
        })


class TestErrors(TikTokTestCase):
    def test_api_error_keeps_the_message_the_api_sent(self):
        import requests

        failed = _response({"message": "tiktok_reconnect_required"}, status=400)
        error = requests.exceptions.HTTPError("400 Client Error")
        error.response = failed
        failed.raise_for_status.side_effect = error
        self.get.return_value = failed

        with self.assertRaises(UploadPostError) as caught:
            self.client.search_tiktok_keywords("my-profile", "pilates")
        self.assertIn("tiktok_reconnect_required", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
