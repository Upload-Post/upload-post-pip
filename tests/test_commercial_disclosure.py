"""Paid partnership / branded content fields (TT-988).

No network: the session's POST is patched and the multipart body is inspected.
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient


def _response(payload=None):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


def _form(data):
    last = {}
    for key, value in data:
        last[key] = value
    return last


class TestPaidPartnershipFields(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(self.client.session, "post", return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def form(self):
        return _form(self.post.call_args[1]["data"])

    def test_paid_partnership_is_sent_lowercase_on_video(self):
        self.client.upload_video(
            "https://example.com/v.mp4", title="t", user="u",
            platforms=["tiktok", "youtube"], paid_partnership=True,
        )
        self.assertEqual(self.form()["paid_partnership"], "true")

    def test_paid_partnership_false_is_sent_explicitly(self):
        self.client.upload_video(
            "https://example.com/v.mp4", title="t", user="u",
            platforms=["tiktok"], paid_partnership=False,
        )
        self.assertEqual(self.form()["paid_partnership"], "false")

    def test_paid_partnership_on_photos_and_text(self):
        self.client.upload_photos(
            ["https://example.com/a.jpg"], title="t", user="u",
            platforms=["tiktok"], paid_partnership=True,
        )
        self.assertEqual(self.form()["paid_partnership"], "true")
        self.client.upload_text(title="t", user="u", platforms=["x"], paid_partnership=True)
        self.assertEqual(self.form()["paid_partnership"], "true")

    def test_nothing_is_sent_when_not_asked(self):
        self.client.upload_video(
            "https://example.com/v.mp4", title="t", user="u",
            platforms=["tiktok", "facebook", "pinterest"],
        )
        form = self.form()
        for key in ("paid_partnership", "facebook_sponsor_id", "pinterest_sponsor_id"):
            self.assertNotIn(key, form)

    def test_sponsor_ids_follow_their_network(self):
        self.client.upload_video(
            "https://example.com/v.mp4", title="t", user="u",
            platforms=["facebook", "pinterest"],
            facebook_page_id="123", facebook_media_type="VIDEO",
            facebook_sponsor_id="9876543210", pinterest_board_id="b1",
            pinterest_sponsor_id=555,
        )
        form = self.form()
        self.assertEqual(form["facebook_sponsor_id"], "9876543210")
        self.assertEqual(form["pinterest_sponsor_id"], "555")

    def test_sponsor_id_is_dropped_for_a_network_that_is_not_targeted(self):
        self.client.upload_video(
            "https://example.com/v.mp4", title="t", user="u",
            platforms=["tiktok"], facebook_sponsor_id="1", pinterest_sponsor_id="2",
        )
        form = self.form()
        self.assertNotIn("facebook_sponsor_id", form)
        self.assertNotIn("pinterest_sponsor_id", form)

    def test_facebook_sponsor_id_on_text_and_photos(self):
        self.client.upload_text(
            title="t", user="u", platforms=["facebook"],
            facebook_page_id="123", facebook_sponsor_id="42",
        )
        self.assertEqual(self.form()["facebook_sponsor_id"], "42")
        self.client.upload_photos(
            ["https://example.com/a.jpg"], title="t", user="u", platforms=["facebook"],
            facebook_page_id="123", facebook_sponsor_id="42",
        )
        self.assertEqual(self.form()["facebook_sponsor_id"], "42")

    def test_pinterest_sponsor_id_on_photos(self):
        self.client.upload_photos(
            ["https://example.com/a.jpg"], title="t", user="u", platforms=["pinterest"],
            pinterest_board_id="b1", pinterest_sponsor_id="77",
        )
        self.assertEqual(self.form()["pinterest_sponsor_id"], "77")

    def test_youtube_flag_keeps_working(self):
        self.client.upload_video(
            "https://example.com/v.mp4", title="t", user="u",
            platforms=["youtube"], hasPaidProductPlacement=True,
        )
        form = self.form()
        self.assertEqual(form["hasPaidProductPlacement"], "true")
        self.assertNotIn("paid_partnership", form)


class TestEditPost(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(
            self.client.session, "post",
            return_value=_response({
                "success": True,
                "paidProductPlacementDetails": {"hasPaidProductPlacement": True},
            }),
        ).start()
        self.addCleanup(patch.stopall)

    def test_youtube_paid_promotion_goes_as_a_json_boolean(self):
        result = self.client.edit_post(
            user="u", platform="youtube", post_id="vid1", hasPaidProductPlacement=True,
        )
        call = self.post.call_args
        self.assertTrue(call.args[0].endswith("/uploadposts/posts/edit"))
        self.assertEqual(call.kwargs["json"], {
            "user": "u", "platform": "youtube", "post_id": "vid1",
            "hasPaidProductPlacement": True,
        })
        self.assertTrue(result["paidProductPlacementDetails"]["hasPaidProductPlacement"])

    def test_false_is_kept_and_none_is_dropped(self):
        self.client.edit_post(
            user="u", platform="youtube", post_id="vid1",
            hasPaidProductPlacement=False, title=None, description="d",
        )
        body = self.post.call_args.kwargs["json"]
        self.assertIs(body["hasPaidProductPlacement"], False)
        self.assertEqual(body["description"], "d")
        self.assertNotIn("title", body)

    def test_other_platforms_use_the_same_endpoint(self):
        self.client.edit_post(user="u", platform="facebook", post_id="p1", message="new")
        body = self.post.call_args.kwargs["json"]
        self.assertEqual(body, {"user": "u", "platform": "facebook", "post_id": "p1", "message": "new"})


if __name__ == "__main__":
    unittest.main()
