"""edit_scheduled must forward every editable part of the PATCH body.

The SDK builds the body from fixed arguments, so anything it does not map is
unreachable. No network: the session's PATCH is patched.
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient


class TestEditScheduled(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("k")
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        self.patch = patch.object(self.client.session, "patch", return_value=response).start()
        self.addCleanup(patch.stopall)

    def body(self):
        return self.patch.call_args.kwargs["json"]

    def test_positional_date_and_timezone_still_work(self):
        self.client.edit_scheduled("job1", "2026-11-01T09:00:00Z", "Europe/Madrid")
        self.assertTrue(self.patch.call_args.args[0].endswith("/uploadposts/schedule/job1"))
        self.assertEqual(self.body(), {"scheduled_date": "2026-11-01T09:00:00Z", "timezone": "Europe/Madrid"})

    def test_text_and_platform_content(self):
        pc = {"instagram": {"caption": "ig"}, "youtube": {"title": "yt"}}
        self.client.edit_scheduled("job1", title="T", caption="C", platform_content=pc)
        self.assertEqual(self.body(), {"title": "T", "caption": "C", "platform_content": pc})

    def test_description_is_alias_and_caption_wins(self):
        self.client.edit_scheduled("job1", description="D")
        self.assertEqual(self.body(), {"description": "D"})
        self.client.edit_scheduled("job1", caption="C", description="D")
        self.assertEqual(self.body(), {"caption": "C"})

    def test_fields_and_youtube_publish_at(self):
        self.client.edit_scheduled(
            "job1",
            fields={"privacyStatus": "unlisted", "disable_comment": True, "cover_url": None,
                    "youtube_publish_at": "old"},
            youtube_publish_at="2026-11-01T09:00:00Z",
        )
        self.assertEqual(self.body(), {"fields": {
            "privacyStatus": "unlisted", "disable_comment": True, "cover_url": None,
            "youtube_publish_at": "2026-11-01T09:00:00Z",
        }})

    def test_cover_and_its_removal(self):
        self.client.edit_scheduled("job1", cover_image_base64="AAAA", cover_filename="c.png",
                                   cover_content_type="image/png")
        self.assertEqual(self.body(), {"cover_image_base64": "AAAA", "cover_filename": "c.png",
                                       "cover_content_type": "image/png"})
        self.client.edit_scheduled("job1", remove_cover=True, cover_image_base64="AAAA")
        self.assertEqual(self.body(), {"remove_cover": True})

    def test_empty_fields_are_not_sent(self):
        self.client.edit_scheduled("job1", "2026-11-01T09:00:00Z", fields={})
        self.assertEqual(self.body(), {"scheduled_date": "2026-11-01T09:00:00Z"})


if __name__ == "__main__":
    unittest.main()
