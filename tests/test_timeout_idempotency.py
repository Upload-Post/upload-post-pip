"""Every request has a timeout, and uploads can carry an Idempotency-Key.

A long timeout for uploads and file transfers (a synchronous upload waits on
the server and a big video takes minutes to send), a normal one for the rest;
both set in the constructor. ``idempotency_key`` on an upload goes in the
``Idempotency-Key`` header, so a retried upload is not published twice.

No network: the session's HTTP verbs are patched.

Run with: python -m unittest discover -s tests
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient


def _response(payload=None):
    response = MagicMock()
    response.status_code = 200
    response.content = b'{"success": true}'
    response.text = '{"success": true}'
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


class TimeoutTest(unittest.TestCase):
    def make(self, **options):
        client = UploadPostClient("test-key", **options)
        self.verbs = {}
        for verb in ("get", "post", "patch", "put", "delete", "request"):
            self.verbs[verb] = patch.object(client.session, verb, return_value=_response()).start()
        self.addCleanup(patch.stopall)
        return client

    def kwargs(self, verb):
        return self.verbs[verb].call_args[1]

    def test_default_timeouts(self):
        client = self.make()
        client.get_history()
        self.assertEqual(self.kwargs("get")["timeout"], 60)
        client.get_analytics("acme", platforms=["x"])
        self.assertEqual(self.kwargs("get")["timeout"], 60)
        client.cancel_scheduled("job-1")
        self.assertEqual(self.kwargs("delete")["timeout"], 60)
        client.upload_text("Hello", "acme", ["x"])
        self.assertEqual(self.kwargs("post")["timeout"], 600)
        client.upload_video("https://example.com/v.mp4", title="t", user="acme", platforms=["tiktok"])
        self.assertEqual(self.kwargs("post")["timeout"], 600)
        client.validate_jwt("jwt")
        self.assertEqual(self.kwargs("get")["timeout"], 60)

    def test_generated_methods_have_a_timeout(self):
        client = self.make()
        client.get_ffmpeg_consumption()
        self.assertEqual(self.kwargs("request")["timeout"], 60)
        client.download_ffmpeg_result("job-1")
        self.assertEqual(self.kwargs("request")["timeout"], 600)

    def test_timeouts_from_the_constructor(self):
        client = self.make(timeout=5, upload_timeout=1800)
        client.get_history()
        self.assertEqual(self.kwargs("get")["timeout"], 5)
        client.upload_text("Hello", "acme", ["x"])
        self.assertEqual(self.kwargs("post")["timeout"], 1800)

    def test_no_limit(self):
        for value in (None, 0):
            client = self.make(timeout=value, upload_timeout=value)
            client.get_history()
            self.assertIsNone(self.kwargs("get")["timeout"])
            client.upload_text("Hello", "acme", ["x"])
            self.assertIsNone(self.kwargs("post")["timeout"])


class IdempotencyKeyTest(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(self.client.session, "post", return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def headers(self):
        return self.post.call_args[1].get("headers") or {}

    def test_uploads_send_the_key(self):
        self.client.upload_text("Hello", "acme", ["x"], idempotency_key="k-text")
        self.assertEqual(self.headers().get("Idempotency-Key"), "k-text")
        self.client.upload_video("https://example.com/v.mp4", title="t", user="acme", platforms=["tiktok"],
                                 idempotency_key="k-video")
        self.assertEqual(self.headers().get("Idempotency-Key"), "k-video")
        self.client.upload_photos(["https://example.com/a.jpg"], title="t", user="acme", platforms=["x"],
                                  idempotency_key="k-photos")
        self.assertEqual(self.headers().get("Idempotency-Key"), "k-photos")
        self.client.upload_document("https://example.com/a.pdf", title="t", user="acme", idempotency_key="k-doc")
        self.assertEqual(self.headers().get("Idempotency-Key"), "k-doc")

    def test_key_is_a_header_not_a_form_field(self):
        self.client.upload_text("Hello", "acme", ["x"], idempotency_key="k-text")
        fields = [k for k, _ in self.post.call_args[1]["data"]]
        self.assertNotIn("idempotency_key", fields)

    def test_without_a_key_no_header(self):
        self.client.upload_text("Hello", "acme", ["x"])
        self.assertNotIn("Idempotency-Key", self.headers())


if __name__ == "__main__":
    unittest.main()
