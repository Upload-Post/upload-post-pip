"""Native commercial disclosure (TT-988): paid_partnership, the Facebook and
Pinterest sponsor ids, and edit_post for YouTube's paid-promotion declaration.

A field the SDK does not whitelist is dropped silently, so each one is pinned
here. No network: helpers are called directly and the session is patched.
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient


def _response(payload=None, status=200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


def _form(data):
    last = {}
    for key, value in data:
        last[key] = value
    return last


class TestPaidPartnershipCommonParam(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")

    def _common(self, **kwargs):
        data = []
        self.client._add_common_params(data, "my-profile", "T", ["tiktok"], **kwargs)
        return _form(data)

    def test_true_is_sent_lowercase(self):
        self.assertEqual(self._common(paid_partnership=True)["paid_partnership"], "true")

    def test_false_is_sent_it_is_a_value_not_unset(self):
        self.assertEqual(self._common(paid_partnership=False)["paid_partnership"], "false")

    def test_left_out_when_not_given(self):
        self.assertNotIn("paid_partnership", self._common())

    def test_network_specific_fields_travel_next_to_it_unchanged(self):
        data = []
        self.client._add_common_params(
            data, "my-profile", "T", ["tiktok", "youtube", "x"], paid_partnership=True
        )
        self.client._add_all_platform_params(
            data, ["tiktok", "youtube", "x"], is_video=True,
            brand_content_toggle=False,
            hasPaidProductPlacement=False,
            x_paid_partnership=False,
        )
        last = _form(data)
        self.assertEqual(last["paid_partnership"], "true")
        self.assertEqual(last["brand_content_toggle"], "false")
        self.assertEqual(last["hasPaidProductPlacement"], "false")
        self.assertEqual(last["x_paid_partnership"], "false")


class TestSponsorIds(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")

    def test_facebook_video_photo_and_text(self):
        for is_video, is_text in ((True, False), (False, False), (False, True)):
            with self.subTest(is_video=is_video, is_text=is_text):
                data = []
                self.client._add_facebook_params(
                    data, is_video=is_video, is_text=is_text,
                    facebook_page_id="1", facebook_sponsor_id="123456",
                )
                self.assertEqual(_form(data)["facebook_sponsor_id"], "123456")

    def test_facebook_omitted_when_absent(self):
        data = []
        self.client._add_facebook_params(data, is_video=True, facebook_page_id="1")
        self.assertNotIn("facebook_sponsor_id", _form(data))

    def test_pinterest_video_and_photo(self):
        for is_video in (True, False):
            with self.subTest(is_video=is_video):
                data = []
                self.client._add_pinterest_params(
                    data, is_video=is_video, pinterest_board_id="b",
                    pinterest_sponsor_id="999",
                )
                self.assertEqual(_form(data)["pinterest_sponsor_id"], "999")

    def test_pinterest_omitted_when_absent(self):
        data = []
        self.client._add_pinterest_params(data, is_video=True, pinterest_board_id="b")
        self.assertNotIn("pinterest_sponsor_id", _form(data))


class TestUploadMethodsForwardThem(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(
            self.client.session, "post", return_value=_response()
        ).start()
        self.addCleanup(patch.stopall)

    def test_upload_text(self):
        self.client.upload_text(
            title="hi", user="my-profile", platforms=["x", "facebook"],
            paid_partnership=True, facebook_page_id="1", facebook_sponsor_id="42",
        )
        last = _form(self.post.call_args[1]["data"])
        self.assertEqual(last["paid_partnership"], "true")
        self.assertEqual(last["facebook_sponsor_id"], "42")

    def test_upload_photos(self):
        with patch("upload_post.api_client.Path.exists", return_value=False):
            self.client.upload_photos(
                photos=["https://example.com/a.jpg"], title="hi", user="my-profile",
                platforms=["facebook", "pinterest"], paid_partnership=True,
                facebook_page_id="1", facebook_sponsor_id="42",
                pinterest_board_id="b", pinterest_sponsor_id="77",
            )
        last = _form(self.post.call_args[1]["data"])
        self.assertEqual(last["paid_partnership"], "true")
        self.assertEqual(last["facebook_sponsor_id"], "42")
        self.assertEqual(last["pinterest_sponsor_id"], "77")


class TestEditPost(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(
            self.client.session, "post", return_value=_response()
        ).start()
        self.addCleanup(patch.stopall)

    def _sent(self):
        args, kwargs = self.post.call_args
        return args[0], kwargs["json"]

    def test_declares_youtube_paid_promotion(self):
        self.client.edit_post(
            user="my-profile", platform="youtube", post_id="VID",
            has_paid_product_placement=True,
        )
        url, body = self._sent()
        self.assertTrue(url.endswith("/uploadposts/posts/edit"))
        self.assertEqual(body, {
            "platform": "youtube", "user": "my-profile", "post_id": "VID",
            "hasPaidProductPlacement": True,
        })

    def test_false_removes_it(self):
        self.client.edit_post(
            user="p", platform="youtube", post_id="VID", has_paid_product_placement=False,
        )
        self.assertIs(self._sent()[1]["hasPaidProductPlacement"], False)

    def test_cross_network_alias(self):
        self.client.edit_post(user="p", platform="youtube", post_id="VID", paid_partnership=True)
        self.assertEqual(self._sent()[1], {
            "platform": "youtube", "user": "p", "post_id": "VID", "paid_partnership": True,
        })

    def test_fields_travel_and_cannot_override_the_identifiers(self):
        self.client.edit_post(
            user="p", platform="facebook", post_id="POST",
            fields={"message": "Updated", "platform": "x", "post_id": "other"},
        )
        self.assertEqual(self._sent()[1], {
            "message": "Updated", "platform": "facebook", "user": "p", "post_id": "POST",
        })


if __name__ == "__main__":
    unittest.main()
