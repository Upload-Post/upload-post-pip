"""Commercial disclosure fields: paid_partnership, facebook_sponsor_id, pinterest_sponsor_id.

No network: helpers are called directly and the session is patched.
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
    last, lists = {}, {}
    for key, value in data:
        last[key] = value
        lists.setdefault(key, []).append(value)
    return last, lists


class TestHelpers(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")

    def test_paid_partnership_true_and_false_are_sent_lowercase(self):
        for value, expected in ((True, "true"), (False, "false")):
            with self.subTest(value=value):
                data = []
                self.client._add_common_params(data, "u", "t", ["tiktok"], paid_partnership=value)
                last, lists = _form(data)
                self.assertEqual(last["paid_partnership"], expected)
                self.assertEqual(lists["paid_partnership"], [expected])

    def test_paid_partnership_absent_is_not_sent(self):
        data = []
        self.client._add_common_params(data, "u", "t", ["tiktok"])
        last, _ = _form(data)
        self.assertNotIn("paid_partnership", last)

    def test_sponsor_ids_are_sent_as_strings(self):
        data = []
        self.client._add_facebook_params(data, facebook_page_id="1", facebook_sponsor_id=1234567890)
        self.client._add_pinterest_params(data, pinterest_board_id="b", pinterest_sponsor_id="42")
        last, _ = _form(data)
        self.assertEqual(last["facebook_sponsor_id"], "1234567890")
        self.assertEqual(last["pinterest_sponsor_id"], "42")

    def test_sponsor_ids_absent_or_empty_are_not_sent(self):
        data = []
        self.client._add_facebook_params(data, facebook_page_id="1", facebook_sponsor_id="")
        self.client._add_pinterest_params(data, pinterest_board_id="b")
        last, _ = _form(data)
        self.assertNotIn("facebook_sponsor_id", last)
        self.assertNotIn("pinterest_sponsor_id", last)

    def test_facebook_sponsor_id_is_sent_on_video_photo_and_text(self):
        for kwargs in ({"is_video": True}, {"is_video": False}, {"is_text": True}):
            with self.subTest(kwargs=kwargs):
                data = []
                self.client._add_facebook_params(
                    data, facebook_page_id="1", facebook_sponsor_id="99", **kwargs
                )
                last, _ = _form(data)
                self.assertEqual(last["facebook_sponsor_id"], "99")


class TestUploadsForwardTheFields(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(self.client.session, "post", return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def test_upload_video_forwards_all_three(self):
        self.client.upload_video(
            "https://example.com/v.mp4",
            title="t",
            user="u",
            platforms=["tiktok", "youtube", "facebook", "pinterest"],
            paid_partnership=True,
            facebook_page_id="1",
            facebook_sponsor_id="99",
            pinterest_board_id="b",
            pinterest_sponsor_id="42",
        )
        last, _ = _form(self.post.call_args[1]["data"])
        self.assertEqual(last["paid_partnership"], "true")
        self.assertEqual(last["facebook_sponsor_id"], "99")
        self.assertEqual(last["pinterest_sponsor_id"], "42")

    def test_upload_photos_forwards_all_three(self):
        self.client.upload_photos(
            ["https://example.com/p.jpg"],
            title="t",
            user="u",
            platforms=["tiktok", "facebook", "pinterest"],
            paid_partnership=True,
            facebook_page_id="1",
            facebook_sponsor_id="99",
            pinterest_board_id="b",
            pinterest_sponsor_id="42",
        )
        last, _ = _form(self.post.call_args[1]["data"])
        self.assertEqual(last["paid_partnership"], "true")
        self.assertEqual(last["facebook_sponsor_id"], "99")
        self.assertEqual(last["pinterest_sponsor_id"], "42")

    def test_upload_text_forwards_paid_partnership_and_facebook_sponsor(self):
        self.client.upload_text(
            title="hi",
            user="u",
            platforms=["x", "facebook"],
            paid_partnership=True,
            facebook_page_id="1",
            facebook_sponsor_id="99",
        )
        last, _ = _form(self.post.call_args[1]["data"])
        self.assertEqual(last["paid_partnership"], "true")
        self.assertEqual(last["facebook_sponsor_id"], "99")

    def test_nothing_new_is_sent_when_the_fields_are_not_used(self):
        self.client.upload_text(title="hi", user="u", platforms=["x", "facebook"], facebook_page_id="1")
        last, _ = _form(self.post.call_args[1]["data"])
        for key in ("paid_partnership", "facebook_sponsor_id", "pinterest_sponsor_id"):
            self.assertNotIn(key, last)


if __name__ == "__main__":
    unittest.main()
