"""Native commercial disclosure (TT-988).

The SDK copies fields from a whitelist, so a field that is not listed never
reaches the API: paid_partnership / facebook_sponsor_id / pinterest_sponsor_id
sent through the SDK produced a post without the label and no error.

No network: the session is patched and the multipart form inspected.
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient

VIDEO = "https://cdn.example.com/v.mp4"
PHOTOS = ["https://cdn.example.com/a.jpg"]


def _response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"success": True}
    response.raise_for_status.return_value = None
    return response


def _fields(call):
    last = {}
    for key, value in call.call_args[1]["data"]:
        last[key] = value
    return last


class CommercialDisclosureTests(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(self.client.session, "post", return_value=_response()).start()
        self.addCleanup(patch.stopall)

    # -- paid_partnership -------------------------------------------------
    def test_paid_partnership_goes_on_video_photo_and_text(self):
        self.client.upload_video(VIDEO, title="t", user="p", platforms=["tiktok"], paid_partnership=True)
        self.assertEqual(_fields(self.post)["paid_partnership"], "true")

        self.client.upload_photos(PHOTOS, title="t", user="p", platforms=["x"], paid_partnership=True)
        self.assertEqual(_fields(self.post)["paid_partnership"], "true")

        self.client.upload_text(title="t", user="p", platforms=["x"], paid_partnership=True)
        self.assertEqual(_fields(self.post)["paid_partnership"], "true")

    def test_paid_partnership_false_is_forwarded_and_absent_means_not_sent(self):
        self.client.upload_video(VIDEO, title="t", user="p", platforms=["youtube"], paid_partnership=False)
        self.assertEqual(_fields(self.post)["paid_partnership"], "false")

        self.client.upload_video(VIDEO, title="t", user="p", platforms=["tiktok", "youtube", "x"])
        self.assertNotIn("paid_partnership", _fields(self.post))

    def test_network_specific_fields_still_go_next_to_it(self):
        self.client.upload_video(
            VIDEO, title="t", user="p", platforms=["tiktok", "youtube", "x"],
            paid_partnership=True, brand_content_toggle=True,
            hasPaidProductPlacement=True, x_paid_partnership=True,
        )
        fields = _fields(self.post)
        self.assertEqual(fields["paid_partnership"], "true")
        self.assertEqual(fields["brand_content_toggle"], "true")
        self.assertEqual(fields["hasPaidProductPlacement"], "true")
        self.assertEqual(fields["x_paid_partnership"], "true")

    def test_has_paid_product_placement_false_is_still_sent(self):
        self.client.upload_video(VIDEO, title="t", user="p", platforms=["youtube"], hasPaidProductPlacement=False)
        self.assertEqual(_fields(self.post)["hasPaidProductPlacement"], "false")

    # -- sponsor ids ------------------------------------------------------
    def test_facebook_sponsor_id_goes_on_video_photo_and_text(self):
        self.client.upload_video(
            VIDEO, title="t", user="p", platforms=["facebook"],
            facebook_media_type="VIDEO", facebook_sponsor_id="1234567890",
        )
        self.assertEqual(_fields(self.post)["facebook_sponsor_id"], "1234567890")

        self.client.upload_photos(PHOTOS, title="t", user="p", platforms=["facebook"], facebook_sponsor_id=1234567890)
        self.assertEqual(_fields(self.post)["facebook_sponsor_id"], "1234567890")

        self.client.upload_text(title="t", user="p", platforms=["facebook"], facebook_sponsor_id="1234567890")
        self.assertEqual(_fields(self.post)["facebook_sponsor_id"], "1234567890")

    def test_pinterest_sponsor_id_goes_on_video_and_photo_pins(self):
        self.client.upload_video(
            VIDEO, title="t", user="p", platforms=["pinterest"],
            pinterest_board_id="b", pinterest_sponsor_id="987654321",
        )
        self.assertEqual(_fields(self.post)["pinterest_sponsor_id"], "987654321")

        self.client.upload_photos(
            PHOTOS, title="t", user="p", platforms=["pinterest"],
            pinterest_board_id="b", pinterest_sponsor_id="987654321",
        )
        self.assertEqual(_fields(self.post)["pinterest_sponsor_id"], "987654321")

    def test_sponsor_id_only_for_its_platform_and_never_empty(self):
        self.client.upload_video(
            VIDEO, title="t", user="p", platforms=["tiktok"],
            facebook_sponsor_id="1", pinterest_sponsor_id="2",
        )
        fields = _fields(self.post)
        self.assertNotIn("facebook_sponsor_id", fields)
        self.assertNotIn("pinterest_sponsor_id", fields)

        self.client.upload_video(
            VIDEO, title="t", user="p", platforms=["facebook", "pinterest"],
            facebook_sponsor_id="", pinterest_sponsor_id="",
        )
        fields = _fields(self.post)
        self.assertNotIn("facebook_sponsor_id", fields)
        self.assertNotIn("pinterest_sponsor_id", fields)


if __name__ == "__main__":
    unittest.main()
