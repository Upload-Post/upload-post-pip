"""Paid partnership / branded content fields (TT-988).

The API gained a cross-network ``paid_partnership`` switch and two sponsor ids.
The SDK must carry them and must stay silent when they are not asked for, so
existing callers send exactly what they sent before.

No network: the session is patched and every assertion is about the form the
SDK would have sent.
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


def _form(data):
    last = {}
    for key, value in data:
        last[key] = value
    return last


class TestPaidPartnership(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(self.client.session, "post", return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def _sent(self):
        return _form(self.post.call_args[1]["data"])

    def test_upload_text_sends_paid_partnership(self):
        self.client.upload_text(title="Sponsored", user="p", platforms=["x"], paid_partnership=True)
        self.assertEqual(self._sent()["paid_partnership"], "true")

    def test_upload_photos_sends_paid_partnership(self):
        self.client.upload_photos(
            photos=["https://example.com/a.jpg"], title="Sponsored", user="p",
            platforms=["tiktok"], paid_partnership=True,
        )
        self.assertEqual(self._sent()["paid_partnership"], "true")

    def test_upload_video_sends_paid_partnership(self):
        self.client.upload_video(
            video_path="https://example.com/v.mp4", title="Sponsored", user="p",
            platforms=["youtube"], paid_partnership=True,
        )
        self.assertEqual(self._sent()["paid_partnership"], "true")

    def test_false_is_sent_too(self):
        # An explicit "no" is not the same as "not asked".
        data = []
        self.client._add_common_params(data, "p", "t", ["x"], paid_partnership=False)
        self.assertEqual(_form(data)["paid_partnership"], "false")

    def test_network_specific_fields_ride_along_with_it(self):
        data = []
        self.client._add_common_params(data, "p", "t", ["x"], paid_partnership=True)
        self.client._add_x_params(data, is_text=False, x_paid_partnership=False)
        self.client._add_tiktok_params(data, is_video=True, brand_content_toggle=False)
        sent = _form(data)
        self.assertEqual(sent["paid_partnership"], "true")
        self.assertEqual(sent["x_paid_partnership"], "false")
        self.assertEqual(sent["brand_content_toggle"], "false")


class TestSponsorIds(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")

    def test_facebook_sponsor_id_on_video_photo_and_text(self):
        for is_video, is_text in ((True, False), (False, False), (False, True)):
            data = []
            self.client._add_facebook_params(
                data, is_video=is_video, is_text=is_text,
                facebook_page_id="1", facebook_sponsor_id="1234567890",
            )
            self.assertEqual(_form(data)["facebook_sponsor_id"], "1234567890")

    def test_pinterest_sponsor_id_on_video_and_photo(self):
        for is_video in (True, False):
            data = []
            self.client._add_pinterest_params(
                data, is_video=is_video, pinterest_board_id="b", pinterest_sponsor_id="987654321",
            )
            self.assertEqual(_form(data)["pinterest_sponsor_id"], "987654321")

    def test_empty_sponsor_ids_are_not_sent(self):
        fb, pin = [], []
        self.client._add_facebook_params(fb, is_text=True, facebook_page_id="1", facebook_sponsor_id="")
        self.client._add_pinterest_params(pin, pinterest_board_id="b", pinterest_sponsor_id="")
        self.assertNotIn("facebook_sponsor_id", _form(fb))
        self.assertNotIn("pinterest_sponsor_id", _form(pin))


class TestUnchangedWhenNotAsked(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(self.client.session, "post", return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def test_no_new_field_on_an_upload_that_never_sets_them(self):
        self.client.upload_text(
            title="Plain", user="p", platforms=["x", "facebook", "pinterest"], facebook_page_id="1",
        )
        sent = _form(self.post.call_args[1]["data"])
        for name in NEW_FIELDS:
            self.assertNotIn(name, sent)


if __name__ == "__main__":
    unittest.main()
