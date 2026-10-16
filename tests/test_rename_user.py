"""rename_user / create_user(display_name).

The profile username is the ``user`` value of every API call and never
changes; renaming only sets ``display_name``.

No network: the session's HTTP verbs are patched.

Run with: python -m unittest discover -s tests
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient

BASE = "https://api.upload-post.com/api"


def _response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"success": True}
    response.raise_for_status.return_value = None
    return response


class RenameUserTest(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.patch = patch.object(self.client.session, "patch", return_value=_response()).start()
        self.post = patch.object(self.client.session, "post", return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def test_rename_patches_display_name_on_the_profile_path(self):
        self.client.rename_user("client-acme", "Acme Corp")
        self.assertEqual(self.patch.call_args[0][0], f"{BASE}/uploadposts/users/client-acme")
        self.assertEqual(self.patch.call_args[1]["json"], {"display_name": "Acme Corp"})

    def test_rename_encodes_the_username_and_never_sends_a_new_one(self):
        self.client.rename_user("me@brand/x", "Brand")
        self.assertEqual(self.patch.call_args[0][0], f"{BASE}/uploadposts/users/me%40brand%2Fx")
        self.assertNotIn("username", self.patch.call_args[1]["json"])

    def test_rename_with_none_clears_the_display_name(self):
        self.client.rename_user("client-acme", None)
        self.assertEqual(self.patch.call_args[1]["json"], {"display_name": None})

    def test_create_user_forwards_display_name(self):
        self.client.create_user("client-acme", display_name="Acme Corp")
        self.assertEqual(self.post.call_args[1]["json"],
                         {"username": "client-acme", "display_name": "Acme Corp"})

    def test_create_user_without_display_name_sends_only_the_username(self):
        self.client.create_user("client-acme")
        self.assertEqual(self.post.call_args[1]["json"], {"username": "client-acme"})


if __name__ == "__main__":
    unittest.main()
