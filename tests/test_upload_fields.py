"""Uploads send every form field the API accepts.

upload_video(), upload_photos(), upload_text() and upload_document() build the
multipart body from per-platform whitelists (``_add_*_params``): a field that
is not listed is dropped without a word (AGENTS.md, rule 6). This checks every
form field the spec gives the four upload endpoints against what the methods
actually send. A field the API gains in codegen/openapi.json fails here until
the client forwards it.

Run with: python -m unittest discover -s tests
"""

import json
import os
import re
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient, UploadPostError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "codegen", "openapi.json"), encoding="utf-8") as fh:
    SPEC = json.load(fh)

PLATFORMS = ["tiktok", "instagram", "youtube", "linkedin", "facebook", "pinterest", "threads", "reddit",
             "bluesky", "x", "google_business", "discord", "telegram", "mastodon", "wordpress", "lemmy",
             "slack", "nostr", "devto", "hashnode", "whop", "listmonk"]
# Keyword prefixes: the client also takes `<platform>_<field>` names.
PREFIXES = PLATFORMS + ["gbp"]
# Fields the method takes as an argument, or that the client fills in.
STRUCTURAL = {"video", "photos", "document", "platform", "user", "title"}
# Fields sent from a keyword that also sends another field, checked on their own below.
SEPARATE = {}
# Fields the client knowingly does not send, with the reason: features that
# are off in production (the SDK offers nothing that is off there). Move a
# field out of here when its feature is switched on.
UNIFIED_LOGIN = "Instagram Unified Login: off in production"
THREADS_PERMISSIONS = "Threads: needs permissions not granted yet, off in production"
NOT_SENT = {
    "instagram_audio_id": UNIFIED_LOGIN,
    "instagram_audio_volume": UNIFIED_LOGIN,
    "instagram_video_volume": UNIFIED_LOGIN,
    "instagram_paid_partnership": UNIFIED_LOGIN,
    "instagram_sponsor_ids": UNIFIED_LOGIN,
    "instagram_poll": UNIFIED_LOGIN,
    "instagram_poll_extended": UNIFIED_LOGIN,
    "instagram_comment_prompt": UNIFIED_LOGIN,
    "instagram_product_tags": UNIFIED_LOGIN,
    "threads_enable_reply_approvals": THREADS_PERMISSIONS,
    "threads_allowlisted_country_codes": THREADS_PERMISSIONS,
    "threads_location_id": THREADS_PERMISSIONS,
    "threads_share_to_instagram": THREADS_PERMISSIONS,
    "threads_share_to_instagram_dark_mode": THREADS_PERMISSIONS,
    "facebook_tags": "Facebook user tags: not confirmed as switched on in production",
}

UPLOADS = [
    ("/upload", "upload_video", lambda: ["https://example.com/v.mp4"]),
    ("/upload_photos", "upload_photos", lambda: [["https://example.com/a.jpg"]]),
    ("/upload_text", "upload_text", lambda: []),
    ("/upload_document", "upload_document", lambda: ["https://example.com/a.pdf"]),
]


def resolve(node):
    while isinstance(node, dict) and "$ref" in node:
        target = SPEC
        for part in node["$ref"][2:].split("/"):
            target = target[part]
        node = target
    return node or {}


def props(schema):
    schema = resolve(schema)
    out = {}
    for sub in schema.get("allOf", []):
        out.update(props(sub))
    out.update(schema.get("properties", {}))
    return out


def is_binary(schema):
    schema = resolve(schema)
    return schema.get("format") == "binary" or resolve(schema.get("items")).get("format") == "binary"


def snake(name):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


class TestUploadFields(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        response = MagicMock()
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        self.post = patch.object(self.client.session, "post", return_value=response).start()
        self.addCleanup(patch.stopall)
        handle, self.file = tempfile.mkstemp(suffix=".jpg")
        os.write(handle, b"x")
        os.close(handle)
        self.addCleanup(os.remove, self.file)

    def sent_fields(self):
        kwargs = self.post.call_args[1]
        names = [k for k, _ in (kwargs.get("data") or [])] + [k for k, _ in (kwargs.get("files") or [])]
        return {n[:-2] if n.endswith("[]") else n for n in names}

    def test_every_field_is_sent(self):
        for route, method, leading in UPLOADS:
            schema = SPEC["paths"][route]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]
            fields = {(n[:-2] if n.endswith("[]") else n): s for n, s in props(schema).items()}
            with self.subTest(method=method, fields=len(fields)):
                kwargs = {}
                for field, s in fields.items():
                    if field in STRUCTURAL:
                        continue
                    if is_binary(s):
                        value = [self.file] if resolve(s).get("type") == "array" else self.file
                    else:
                        value = "https://example.com/value"
                    for key in [field, snake(field)] + [f"{p}_{snake(field)}" for p in PREFIXES]:
                        kwargs.setdefault(key, value)
                kwargs.update(user="u", title="t", platforms=PLATFORMS)
                if method == "upload_document":
                    kwargs["platforms"] = ["linkedin", "telegram"]
                getattr(self.client, method)(*leading(), **kwargs)
                got = self.sent_fields()
                dropped = [f for f in fields if f not in STRUCTURAL and f not in got
                           and f not in NOT_SENT and f not in SEPARATE]
                self.assertEqual(dropped, [], f"{method} drops these API fields: {', '.join(dropped)}")

    def test_upload_document_to_telegram(self):
        self.client.upload_document("https://example.com/a.zip", "t", "u", platforms=["telegram"],
                                    telegram_send_by_url=True, telegram_allow_paid_broadcast=True)
        data = self.post.call_args[1]["data"]
        self.assertIn(("platform[]", "telegram"), data)
        self.assertNotIn(("platform[]", "linkedin"), data)
        self.assertIn(("telegram_send_by_url", "true"), data)

    def test_upload_document_still_defaults_to_linkedin(self):
        self.client.upload_document("https://example.com/a.pdf", "t", "u", platforms=["x"])
        data = self.post.call_args[1]["data"]
        self.assertIn(("platform[]", "linkedin"), data)
        self.assertNotIn(("platform[]", "x"), data)

    def test_x_exclude_reply_user_ids_goes_as_a_list(self):
        self.client.upload_text("t", "u", ["x"], exclude_reply_user_ids=["1", "2"])
        data = self.post.call_args[1]["data"]
        self.assertEqual([v for k, v in data if k == "exclude_reply_user_ids[]"], ["1", "2"])

    def test_youtube_thumbnail_and_instagram_cover_as_files(self):
        self.client.upload_video("https://example.com/v.mp4", "t", "u", ["youtube", "instagram"],
                                 thumbnail=self.file, cover_image=self.file)
        files = [k for k, _ in self.post.call_args[1]["files"]]
        self.assertIn("thumbnail", files)
        self.assertIn("cover_image", files)



class TestFirstCommentMedia(unittest.TestCase):
    """The API reads first_comment_media[] from the uploaded files only."""

    def setUp(self):
        self.client = UploadPostClient("secret-key")
        response = MagicMock()
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        self.post = patch.object(self.client.session, "post", return_value=response).start()
        image = MagicMock()
        image.content = b"PNGDATA"
        image.headers = {"Content-Type": "image/png"}
        image.raise_for_status.return_value = None
        self.download = patch("upload_post.api_client.requests.get", return_value=image).start()
        self.addCleanup(patch.stopall)
        handle, self.file = tempfile.mkstemp(suffix=".jpg")
        os.write(handle, b"x")
        os.close(handle)
        self.addCleanup(os.remove, self.file)

    def test_a_url_is_downloaded_and_sent_as_a_file(self):
        calls = [
            lambda media: self.client.upload_video("https://example.com/v.mp4", "t", "u", ["reddit"], first_comment_media=media),
            lambda media: self.client.upload_photos(["https://example.com/a.jpg"], "t", "u", ["reddit"], first_comment_media=media),
            lambda media: self.client.upload_text("t", "u", ["reddit"], first_comment_media=media),
        ]
        for call in calls:
            with self.subTest(call=call):
                self.post.reset_mock()
                call(["https://images.example.com/chart.png?x=1", self.file])
                parts = [v for k, v in self.post.call_args[1]["files"] if k == "first_comment_media[]"]
                self.assertEqual(parts[0], ("chart.png", b"PNGDATA", "image/png"))
                self.assertEqual(parts[1][0], os.path.basename(self.file))

    def test_the_download_does_not_carry_the_api_key(self):
        self.client.upload_text("t", "u", ["reddit"], first_comment_media=["https://images.example.com/a.jpg"])
        args, kwargs = self.download.call_args
        self.assertEqual(args[0], "https://images.example.com/a.jpg")
        self.assertNotIn("headers", kwargs)

    def test_a_url_that_cannot_be_downloaded_fails_before_uploading(self):
        import requests
        self.download.side_effect = requests.exceptions.ConnectionError("down")
        with self.assertRaises(UploadPostError) as ctx:
            self.client.upload_text("t", "u", ["reddit"], first_comment_media=["https://images.example.com/x.png"])
        self.assertIn("https://images.example.com/x.png", str(ctx.exception))
        self.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
