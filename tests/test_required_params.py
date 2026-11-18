"""Required arguments are checked before any request.

An empty profile or id in the path (``/analytics/None``) and get_analytics
without platforms are answered 400 by the API, so the client says so itself and
sends nothing. Values in the path are percent-encoded (``/`` and spaces too).

No network: the session's HTTP verbs are patched.

Run with: python -m unittest discover -s tests
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient, UploadPostError

BASE = "https://api.upload-post.com/api"


def _response(payload=None):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


class RequiredParamsTest(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.verbs = {}
        for verb in ("get", "post", "patch", "put", "delete"):
            self.verbs[verb] = patch.object(self.client.session, verb, return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def assert_nothing_sent(self):
        for verb, mock in self.verbs.items():
            self.assertFalse(mock.called, f"{verb} was called: {mock.call_args}")

    def test_get_analytics_without_profile(self):
        for profile in (None, "", "   "):
            with self.assertRaisesRegex(UploadPostError, "profile_username is required"):
                self.client.get_analytics(profile, platforms=["instagram"])
        self.assert_nothing_sent()

    def test_get_analytics_without_platforms(self):
        for platforms in (None, [], ""):
            with self.assertRaisesRegex(UploadPostError, "platforms is required"):
                self.client.get_analytics("acme", platforms=platforms)
        self.assert_nothing_sent()

    def test_get_analytics_encodes_the_profile(self):
        self.client.get_analytics("my brand/eu", platforms=["instagram", "tiktok"])
        args, kwargs = self.verbs["get"].call_args
        self.assertEqual(args[0], f"{BASE}/analytics/my%20brand%2Feu")
        self.assertEqual(kwargs["params"], {"platforms": "instagram,tiktok"})

    def test_get_analytics_accepts_a_comma_separated_string(self):
        self.client.get_analytics("acme", platforms="instagram,x")
        self.assertEqual(self.verbs["get"].call_args[1]["params"], {"platforms": "instagram,x"})

    def test_other_path_ids_are_required(self):
        calls = [
            (lambda: self.client.get_total_impressions(None), "profile_username"),
            (lambda: self.client.get_post_analytics(""), "request_id"),
            (lambda: self.client.cancel_scheduled(None), "job_id"),
            (lambda: self.client.edit_scheduled(None, title="x"), "job_id"),
            (lambda: self.client.get_webhook_delivery(None), "delivery_id"),
            (lambda: self.client.redeliver_webhook(""), "delivery_id"),
        ]
        for call, name in calls:
            with self.assertRaisesRegex(UploadPostError, f"{name} is required"):
                call()
        self.assert_nothing_sent()

    def test_path_ids_are_encoded(self):
        self.client.get_total_impressions("a b")
        self.assertEqual(self.verbs["get"].call_args[0][0], f"{BASE}/uploadposts/total-impressions/a%20b")
        self.client.get_post_analytics("r/1")
        self.assertEqual(self.verbs["get"].call_args[0][0], f"{BASE}/uploadposts/post-analytics/r%2F1")
        self.client.cancel_scheduled("job/1")
        self.assertEqual(self.verbs["delete"].call_args[0][0], f"{BASE}/uploadposts/schedule/job%2F1")
        self.client.edit_scheduled("job 2", title="x")
        self.assertEqual(self.verbs["patch"].call_args[0][0], f"{BASE}/uploadposts/schedule/job%202")


if __name__ == "__main__":
    unittest.main()
