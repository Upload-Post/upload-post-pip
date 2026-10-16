"""edit_scheduled builds its PATCH body from a fixed list: anything left out is
dropped silently. It used to forward only the date, so text edits and every
other option (cover frame, AI labels...) were unreachable from Python.

No network: the session is patched.
"""

import unittest
from unittest.mock import MagicMock

from upload_post import UploadPostClient


def _client():
    client = UploadPostClient("k")
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"success": True}
    response.raise_for_status.return_value = None
    client.session = MagicMock()
    client.session.patch.return_value = response
    client.session.get.return_value = response
    return client


class TestEditScheduled(unittest.TestCase):
    def test_forwards_text_platform_content_and_fields(self):
        client = _client()
        fields = {"cover_timestamp": 4200, "is_aigc": True, "description": None}
        client.edit_scheduled(
            "job1",
            scheduled_date="2026-10-01T10:00:00Z",
            timezone="UTC",
            title="T",
            caption="C",
            platform_content={"youtube": {"title": "Y"}},
            fields=fields,
        )
        url = client.session.patch.call_args[0][0]
        self.assertTrue(url.endswith("/uploadposts/schedule/job1"))
        self.assertEqual(client.session.patch.call_args[1]["json"], {
            "scheduled_date": "2026-10-01T10:00:00Z",
            "timezone": "UTC",
            "title": "T",
            "caption": "C",
            "platform_content": {"youtube": {"title": "Y"}},
            "fields": fields,
        })

    def test_date_only_edit_is_unchanged(self):
        client = _client()
        client.edit_scheduled("job1", scheduled_date="2026-10-01T10:00:00Z")
        self.assertEqual(client.session.patch.call_args[1]["json"], {"scheduled_date": "2026-10-01T10:00:00Z"})

    def test_getters_read_the_job(self):
        client = _client()
        client.get_scheduled("job1")
        self.assertTrue(client.session.get.call_args[0][0].endswith("/uploadposts/schedule/job1"))
        client.get_scheduled_thumbnail("job1")
        self.assertTrue(client.session.get.call_args[0][0].endswith("/uploadposts/schedule/job1/thumbnail"))


if __name__ == "__main__":
    unittest.main()
