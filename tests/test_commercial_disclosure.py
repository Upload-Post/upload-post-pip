"""Native commercial disclosure (TT-988): the SDK sends the cross-network
``paid_partnership`` switch and the Facebook / Pinterest sponsor ids.

No network: the param helpers are called directly.
"""

import unittest

from upload_post import UploadPostClient


def _form(data):
    """Every value sent, per key."""
    out = {}
    for key, value in data:
        out.setdefault(key, []).append(value)
    return out


class PaidPartnershipTests(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")

    def _common(self, **kwargs):
        data = []
        self.client._add_common_params(data, "profile", "Sponsored", ["tiktok", "youtube"], **kwargs)
        return _form(data)

    def test_true_is_sent_lowercase(self):
        self.assertEqual(self._common(paid_partnership=True)["paid_partnership"], ["true"])

    def test_false_is_sent_so_a_caller_can_say_no(self):
        self.assertEqual(self._common(paid_partnership=False)["paid_partnership"], ["false"])

    def test_left_out_when_not_asked(self):
        self.assertNotIn("paid_partnership", self._common())

    def test_upload_text_puts_it_on_the_request(self):
        from unittest.mock import MagicMock, patch
        response = MagicMock(status_code=200)
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        with patch.object(self.client.session, "post", return_value=response) as post:
            self.client.upload_text(title="Hi", user="p", platforms=["x"], paid_partnership=True)
        sent = _form(post.call_args.kwargs["data"])
        self.assertEqual(sent["paid_partnership"], ["true"])


class SponsorIdTests(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")

    def test_facebook_sponsor_id_on_video_photo_and_text(self):
        for kind in ({"is_video": True}, {"is_video": False}, {"is_text": True}):
            data = []
            self.client._add_facebook_params(data, facebook_sponsor_id="1234567890", **kind)
            self.assertEqual(_form(data)["facebook_sponsor_id"], ["1234567890"], kind)

    def test_pinterest_sponsor_id_on_video_and_photo(self):
        for is_video in (True, False):
            data = []
            self.client._add_pinterest_params(data, is_video=is_video, pinterest_sponsor_id="99")
            self.assertEqual(_form(data)["pinterest_sponsor_id"], ["99"])

    def test_a_number_is_sent_as_its_digits(self):
        data = []
        self.client._add_facebook_params(data, facebook_sponsor_id=7)
        self.assertEqual(_form(data)["facebook_sponsor_id"], ["7"])

    def test_left_out_when_not_given(self):
        data = []
        self.client._add_facebook_params(data, facebook_page_id="1")
        self.client._add_pinterest_params(data, pinterest_board_id="b")
        self.assertFalse([k for k in _form(data) if k.endswith("_sponsor_id")])


if __name__ == "__main__":
    unittest.main()
