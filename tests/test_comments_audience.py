"""Tests for the question-shaped endpoints.

Comments (list, replies, moderate), audience and suggestions are all one
endpoint each with a `platform` parameter, not a method per network. TikTok is
the platform used here because it is the one that answers all of them today.

No network: the session's HTTP verbs are patched, so every assertion is about
what the client would have sent.

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


class ClientTestCase(unittest.TestCase):
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


class TestComments(ClientTestCase):
    """One /comments endpoint, told who to ask with platform."""

    def test_get_post_comments(self):
        self.client.get_post_comments(
            user="my-profile", platform="tiktok",
            post_id="7412345678901234567", limit=20,
        )
        self.assertGet(self.get, "/uploadposts/comments", {
            "platform": "tiktok", "user": "my-profile",
            "post_id": "7412345678901234567", "limit": 20,
        })

    def test_comment_id_asks_for_the_replies(self):
        self.client.get_post_comments(
            user="my-profile", platform="tiktok",
            post_id="741", comment_id="99", limit=20,
        )
        self.assertGet(self.get, "/uploadposts/comments", {
            "platform": "tiktok", "user": "my-profile",
            "post_id": "741", "comment_id": "99", "limit": 20,
        })

    def test_comment_id_is_omitted_when_not_asked_for(self):
        self.client.get_post_comments(
            user="my-profile", platform="tiktok", post_id="741"
        )
        self.assertGet(self.get, "/uploadposts/comments", {
            "platform": "tiktok", "user": "my-profile", "post_id": "741",
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


class TestFirstComment(ClientTestCase):
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


class TestCommentAction(ClientTestCase):
    def test_hide_and_pin_carry_the_post(self):
        for action in ("hide", "unhide", "pin", "unpin"):
            with self.subTest(action=action):
                self.client.comment_action(
                    user="my-profile", platform="tiktok", action=action,
                    comment_id="99", post_id="741",
                )
                self.assertEqual(self.post.call_args[0][0],
                                 "https://api.upload-post.com/api"
                                 "/uploadposts/comments/action")
                self.assertEqual(self.post.call_args[1]["json"], {
                    "platform": "tiktok", "user": "my-profile",
                    "comment_id": "99", "action": action, "post_id": "741",
                })

    def test_like_never_carries_the_post(self):
        for action in ("like", "unlike"):
            with self.subTest(action=action):
                self.client.comment_action(
                    user="my-profile", platform="tiktok", action=action,
                    comment_id="99", post_id="741",
                )
                self.assertEqual(self.post.call_args[1]["json"], {
                    "platform": "tiktok", "user": "my-profile",
                    "comment_id": "99", "action": action,
                })


class TestAudience(ClientTestCase):
    def test_window_travels_as_snake_case(self):
        self.client.get_audience(
            user="my-profile", platform="tiktok",
            start_date="2026-07-01", end_date="2026-07-30",
        )
        self.assertGet(self.get, "/uploadposts/audience", {
            "user": "my-profile", "platform": "tiktok",
            "start_date": "2026-07-01", "end_date": "2026-07-30",
        })

    def test_default_window_is_left_to_the_api(self):
        self.client.get_audience(user="my-profile", platform="tiktok")
        self.assertGet(self.get, "/uploadposts/audience",
                       {"user": "my-profile", "platform": "tiktok"})

    def test_benchmark_category_rides_along(self):
        self.client.get_audience(
            user="my-profile", platform="tiktok",
            benchmark_category="SOFTWARE_AND_APPS",
        )
        self.assertGet(self.get, "/uploadposts/audience", {
            "user": "my-profile", "platform": "tiktok",
            "benchmark_category": "SOFTWARE_AND_APPS",
        })


class TestSuggestions(ClientTestCase):
    def test_hashtags_take_country_and_language(self):
        self.client.get_suggestions(
            user="my-profile", platform="tiktok", type="hashtags",
            q="pilates", country_code="ES", language="es",
        )
        self.assertGet(self.get, "/uploadposts/suggestions", {
            "user": "my-profile", "platform": "tiktok", "type": "hashtags",
            "q": "pilates", "country_code": "ES", "language": "es",
        })

    def test_keywords_use_the_same_call(self):
        self.client.get_suggestions(
            user="my-profile", platform="tiktok", type="keywords", q="pilates"
        )
        self.assertGet(self.get, "/uploadposts/suggestions", {
            "user": "my-profile", "platform": "tiktok",
            "type": "keywords", "q": "pilates",
        })


class TestTheOldPerNetworkMethodsAreGone(ClientTestCase):
    def test_nothing_answers_the_old_names(self):
        for name in (
            "get_tiktok_comment_replies", "tiktok_comment_action",
            "search_tiktok_keywords", "get_tiktok_insights",
            "get_tiktok_video_insights", "get_tiktok_hashtags",
            "get_tiktok_benchmark",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(self.client, name))

    def test_the_composer_helpers_stay(self):
        for name in (
            "get_tiktok_trending_music", "search_tiktok_music",
            "get_tiktok_locations", "get_tiktok_publishing_settings",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(self.client, name))


class TestErrors(ClientTestCase):
    def test_api_error_keeps_the_message_the_api_sent(self):
        import requests

        failed = _response({"message": "platform_not_supported"}, status=400)
        error = requests.exceptions.HTTPError("400 Client Error")
        error.response = failed
        failed.raise_for_status.side_effect = error
        self.get.return_value = failed

        with self.assertRaises(UploadPostError) as caught:
            self.client.get_suggestions(
                user="my-profile", platform="x", type="hashtags"
            )
        self.assertIn("platform_not_supported", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
