"""Paid partnership / branded content fields: sent only when the caller sets them."""

import unittest

from upload_post import UploadPostClient


def _form(data):
    last = {}
    for key, value in data:
        last[key] = value
    return last


class TestPaidPartnership(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient(api_key="test-key")

    def _common(self, **kwargs):
        data = []
        self.client._add_common_params(data, "user", "title", ["tiktok", "youtube"], **kwargs)
        return _form(data)

    def test_true_and_false_are_sent(self):
        self.assertEqual(self._common(paid_partnership=True)["paid_partnership"], "true")
        self.assertEqual(self._common(paid_partnership=False)["paid_partnership"], "false")

    def test_absent_sends_nothing(self):
        self.assertNotIn("paid_partnership", self._common())

    def test_sponsor_ids_on_every_facebook_surface(self):
        for is_video, is_text in ((True, False), (False, False), (False, True)):
            data = []
            self.client._add_facebook_params(
                data, is_video=is_video, is_text=is_text,
                facebook_page_id="1", facebook_sponsor_id="1234567890",
            )
            self.assertEqual(_form(data)["facebook_sponsor_id"], "1234567890")

    def test_pinterest_sponsor_id(self):
        for is_video in (True, False):
            data = []
            self.client._add_pinterest_params(
                data, is_video=is_video, pinterest_board_id="b", pinterest_sponsor_id="987",
            )
            self.assertEqual(_form(data)["pinterest_sponsor_id"], "987")

    def test_no_sponsor_fields_without_the_option(self):
        fb, pin = [], []
        self.client._add_facebook_params(fb, is_video=True, facebook_page_id="1")
        self.client._add_pinterest_params(pin, is_video=True, pinterest_board_id="b")
        self.assertNotIn("facebook_sponsor_id", _form(fb))
        self.assertNotIn("pinterest_sponsor_id", _form(pin))

    def test_native_fields_keep_working(self):
        data = []
        self.client._add_x_params(data, is_text=False, x_paid_partnership=True)
        self.assertEqual(_form(data)["x_paid_partnership"], "true")


if __name__ == "__main__":
    unittest.main()
