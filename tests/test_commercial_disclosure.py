"""Paid partnership / branded content (TT-988).

``paid_partnership``, ``facebook_sponsor_id`` and ``pinterest_sponsor_id`` reach the
API with those names, and nothing is sent when the caller did not ask.

No network: the session's ``post`` is patched and the multipart data is read back.
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient

NEW_FIELDS = ("paid_partnership", "facebook_sponsor_id", "pinterest_sponsor_id")


def _response(payload=None, status=200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


def _fields(data):
    return {key: value for key, value in data}


class TestCommercialDisclosure(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(
            self.client.session, "post", return_value=_response()
        ).start()
        self.addCleanup(patch.stopall)

    def _sent(self):
        return _fields(self.post.call_args[1]["data"])

    def test_upload_text_sends_paid_partnership(self):
        self.client.upload_text(
            title="Sponsored", user="my-profile", platforms=["x"], paid_partnership=True
        )
        self.assertEqual(self._sent()["paid_partnership"], "true")

    def test_false_is_sent_so_it_can_switch_the_label_off(self):
        self.client.upload_text(
            title="Organic", user="my-profile", platforms=["x"], paid_partnership=False
        )
        self.assertEqual(self._sent()["paid_partnership"], "false")

    def test_upload_photos_sends_paid_partnership(self):
        self.client.upload_photos(
            ["https://example.com/a.jpg"], title="Sponsored", user="my-profile",
            platforms=["tiktok"], paid_partnership=True,
        )
        self.assertEqual(self._sent()["paid_partnership"], "true")

    def test_upload_video_sends_paid_partnership(self):
        self.client.upload_video(
            "https://example.com/v.mp4", title="Sponsored", user="my-profile",
            platforms=["tiktok", "youtube"], paid_partnership=True,
        )
        self.assertEqual(self._sent()["paid_partnership"], "true")

    def test_facebook_sponsor_id_on_text_photo_and_video(self):
        self.client.upload_text(
            title="Sponsored", user="my-profile", platforms=["facebook"],
            facebook_page_id="123", facebook_sponsor_id="1122334455",
        )
        self.assertEqual(self._sent()["facebook_sponsor_id"], "1122334455")

        self.client.upload_photos(
            ["https://example.com/a.jpg"], title="Sponsored", user="my-profile",
            platforms=["facebook"], facebook_page_id="123", facebook_sponsor_id="1122334455",
        )
        self.assertEqual(self._sent()["facebook_sponsor_id"], "1122334455")

        self.client.upload_video(
            "https://example.com/v.mp4", title="Sponsored", user="my-profile",
            platforms=["facebook"], facebook_page_id="123", facebook_media_type="VIDEO",
            facebook_sponsor_id="1122334455",
        )
        self.assertEqual(self._sent()["facebook_sponsor_id"], "1122334455")

    def test_pinterest_sponsor_id_on_pins(self):
        for is_video in (True, False):
            with self.subTest(is_video=is_video):
                data = []
                self.client._add_pinterest_params(
                    data, is_video=is_video, pinterest_board_id="b1", pinterest_sponsor_id="99"
                )
                self.assertEqual(_fields(data)["pinterest_sponsor_id"], "99")

    def test_nothing_is_sent_when_the_caller_did_not_ask(self):
        self.client.upload_text(
            title="Plain", user="my-profile", platforms=["x", "facebook"], facebook_page_id="123"
        )
        sent = self._sent()
        for key in NEW_FIELDS:
            self.assertNotIn(key, sent)

    def test_empty_sponsor_ids_are_not_sent(self):
        data = []
        self.client._add_facebook_params(data, facebook_sponsor_id="")
        self.client._add_pinterest_params(data, pinterest_sponsor_id="")
        sent = _fields(data)
        self.assertNotIn("facebook_sponsor_id", sent)
        self.assertNotIn("pinterest_sponsor_id", sent)


if __name__ == "__main__":
    unittest.main()
