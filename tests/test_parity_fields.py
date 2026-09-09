"""Whitelist tests for 2.13.0 API parity fields.

No network: helpers are called directly, and upload_text is patched at the
session. Fields not in the whitelist must still be dropped.
"""

import json
import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient, __version__


def _response(payload=None, status=200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


def _form(data):
    """Last-wins map, plus every value for repeated keys."""
    last = {}
    lists = {}
    for key, value in data:
        last[key] = value
        lists.setdefault(key, []).append(value)
    return last, lists


class TestVersions(unittest.TestCase):
    def test_setup_and_init_agree(self):
        setup = Path(__file__).resolve().parents[1] / "setup.py"
        text = setup.read_text(encoding="utf-8")
        match = re.search(r'version="([^"]*)"', text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), __version__)
        self.assertEqual(__version__, "2.13.0")


class TestTikTokDraftAliases(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")

    def test_post_mode_media_upload_is_sent(self):
        data = []
        self.client._add_tiktok_params(data, is_video=True, post_mode="MEDIA_UPLOAD")
        last, _ = _form(data)
        self.assertEqual(last["post_mode"], "MEDIA_UPLOAD")

    def test_tiktok_upload_to_draft_is_sent_on_video_and_photos(self):
        for is_video in (True, False):
            with self.subTest(is_video=is_video):
                data = []
                self.client._add_tiktok_params(
                    data, is_video=is_video, tiktok_upload_to_draft=True
                )
                last, _ = _form(data)
                self.assertEqual(last["tiktok_upload_to_draft"], "true")

    def test_upload_to_draft_and_is_draft_aliases(self):
        data = []
        self.client._add_tiktok_params(data, is_video=True, upload_to_draft=True)
        self.assertEqual(dict(data)["upload_to_draft"], "true")
        data = []
        self.client._add_tiktok_params(data, is_video=False, is_draft=True)
        self.assertEqual(dict(data)["is_draft"], "true")

    def test_ads_only_and_tto_invite_are_video_only(self):
        data = []
        self.client._add_tiktok_params(
            data, is_video=True, tiktok_is_ads_only=True,
            tiktok_tto_invite_link="https://example.com/tto",
        )
        last, _ = _form(data)
        self.assertEqual(last["tiktok_is_ads_only"], "true")
        self.assertEqual(last["tiktok_tto_invite_link"], "https://example.com/tto")

        data = []
        self.client._add_tiktok_params(
            data, is_video=False, tiktok_is_ads_only=True,
            tiktok_tto_invite_link="https://example.com/tto",
        )
        last, _ = _form(data)
        self.assertNotIn("tiktok_is_ads_only", last)
        self.assertNotIn("tiktok_tto_invite_link", last)

    def test_existing_privacy_level_still_works(self):
        data = []
        self.client._add_tiktok_params(
            data, is_video=True, privacy_level="SELF_ONLY", disable_comment=True
        )
        last, _ = _form(data)
        self.assertEqual(last["privacy_level"], "SELF_ONLY")
        self.assertEqual(last["disable_comment"], "true")


class TestParityWhitelists(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")

    def test_instagram_alt_text_list(self):
        data = []
        self.client._add_instagram_params(
            data, is_video=False, instagram_alt_text=["front", "back"]
        )
        last, lists = _form(data)
        self.assertEqual(lists["instagram_alt_text[]"], ["front", "back"])
        self.assertNotIn("instagram_alt_text", last)

    def test_facebook_json_and_bools(self):
        data = []
        self.client._add_facebook_params(
            data, is_video=True, is_text=True,
            facebook_page_id="1",
            facebook_place_id="place",
            facebook_targeting={"geo": "ES"},
            facebook_is_ai_generated=True,
            facebook_call_to_action={"type": "LEARN_MORE", "link": "https://x"},
            facebook_unpublished_content_type="DRAFT",
            facebook_no_story=True,
        )
        last, _ = _form(data)
        self.assertEqual(last["facebook_page_id"], "1")
        self.assertEqual(last["facebook_place_id"], "place")
        self.assertEqual(json.loads(last["facebook_targeting"]), {"geo": "ES"})
        self.assertEqual(last["facebook_is_ai_generated"], "true")
        self.assertEqual(last["facebook_unpublished_content_type"], "DRAFT")
        self.assertEqual(last["facebook_no_story"], "true")

    def test_linkedin_visibility_alias_and_targeting(self):
        data = []
        self.client._add_linkedin_params(
            data, linkedin_visibility="CONNECTIONS",
            linkedin_disable_reshare=True,
            linkedin_target_geo_locations=["urn:li:geo:103644278"],
        )
        last, lists = _form(data)
        self.assertEqual(last["visibility"], "CONNECTIONS")
        self.assertEqual(last["linkedin_visibility"], "CONNECTIONS")
        self.assertEqual(last["linkedin_disable_reshare"], "true")
        self.assertEqual(
            lists["linkedin_target_geo_locations[]"],
            ["urn:li:geo:103644278"],
        )

    def test_x_alt_paid_and_article_fields(self):
        data = []
        self.client._add_x_params(
            data, is_text=True, x_alt_text="A cat",
            x_paid_partnership=True, x_article_title="Hello",
            x_article_draft=True,
        )
        last, _ = _form(data)
        self.assertEqual(last["x_alt_text"], "A cat")
        self.assertEqual(last["x_paid_partnership"], "true")
        self.assertEqual(last["x_article_title"], "Hello")
        self.assertEqual(last["x_article_draft"], "true")

    def test_threads_text_fields(self):
        data = []
        self.client._add_threads_params(
            data, is_text=True,
            threads_reply_control="mentioned_only",
            threads_poll_options=["Sí", "No"],
            threads_auto_publish_text=True,
        )
        last, lists = _form(data)
        self.assertEqual(last["threads_reply_control"], "mentioned_only")
        self.assertEqual(lists["threads_poll_options[]"], ["Sí", "No"])
        self.assertEqual(last["threads_auto_publish_text"], "true")

    def test_reddit_flags(self):
        data = []
        self.client._add_reddit_params(
            data, is_text=True, subreddit="test",
            reddit_nsfw=True, reddit_spoiler=True, reddit_flair_text="News",
        )
        last, _ = _form(data)
        self.assertEqual(last["subreddit"], "test")
        self.assertEqual(last["reddit_nsfw"], "true")
        self.assertEqual(last["reddit_spoiler"], "true")
        self.assertEqual(last["reddit_flair_text"], "News")

    def test_gbp_offer_aliases_and_language(self):
        data = []
        self.client._add_google_business_params(
            data, gbp_offer_coupon="SAVE10", gbp_coupon_code="SAVE10",
            gbp_language_code="es",
        )
        last, _ = _form(data)
        self.assertEqual(last["gbp_offer_coupon"], "SAVE10")
        self.assertEqual(last["gbp_coupon_code"], "SAVE10")
        self.assertEqual(last["gbp_language_code"], "es")

    def test_youtube_notify_false_is_sent(self):
        data = []
        self.client._add_youtube_params(
            data, youtube_notify_subscribers=False,
            youtube_publish_at="2030-01-01T10:00:00Z",
        )
        last, _ = _form(data)
        self.assertEqual(last["youtube_notify_subscribers"], "false")
        self.assertEqual(last["youtube_publish_at"], "2030-01-01T10:00:00Z")

    def test_pinterest_carousel(self):
        data = []
        self.client._add_pinterest_params(
            data, is_video=False,
            pinterest_board_section_id="sec",
            pinterest_ai_disclosures=["AI_MODIFIED"],
            pinterest_carousel_titles=["One", "Two"],
            pinterest_carousel_index=1,
        )
        last, lists = _form(data)
        self.assertEqual(last["pinterest_board_section_id"], "sec")
        self.assertEqual(lists["pinterest_ai_disclosures[]"], ["AI_MODIFIED"])
        self.assertEqual(lists["pinterest_carousel_titles[]"], ["One", "Two"])
        self.assertEqual(last["pinterest_carousel_index"], "1")

    def test_credential_channels(self):
        data = []
        self.client._add_discord_params(data, discord_thread_name="launch", discord_tts=True)
        self.client._add_telegram_params(data, telegram_parse_mode="HTML", telegram_caption_overflow="split")
        self.client._add_mastodon_params(data, mastodon_visibility="unlisted", mastodon_spoiler_text="CW")
        self.client._add_wordpress_params(data, wordpress_status="draft")
        self.client._add_lemmy_params(data, lemmy_url="https://example.com", lemmy_nsfw=False)
        self.client._add_slack_params(data, slack_markdown=True)
        self.client._add_nostr_params(data, nostr_long_form=True)
        self.client._add_devto_params(data, devto_tags="python,testing", devto_published=True)
        self.client._add_hashnode_params(data, hashnode_body="# Hello", hashnode_draft=True)
        self.client._add_whop_params(data, whop_body="hello", whop_pinned=True)
        self.client._add_listmonk_params(data, listmonk_content_type="markdown")
        self.client._add_bluesky_params(
            data, bluesky_alt_text=["storefront"], bluesky_langs="en",
            bluesky_gallery=True,
        )
        last, lists = _form(data)
        self.assertEqual(last["discord_thread_name"], "launch")
        self.assertEqual(last["telegram_caption_overflow"], "split")
        self.assertEqual(last["mastodon_visibility"], "unlisted")
        self.assertEqual(last["wordpress_status"], "draft")
        self.assertEqual(last["lemmy_nsfw"], "false")
        self.assertEqual(last["slack_markdown"], "true")
        self.assertEqual(last["nostr_long_form"], "true")
        self.assertEqual(last["devto_published"], "true")
        self.assertEqual(last["hashnode_body"], "# Hello")
        self.assertEqual(last["whop_pinned"], "true")
        self.assertEqual(last["listmonk_content_type"], "markdown")
        self.assertEqual(lists["bluesky_alt_text[]"], ["storefront"])
        self.assertEqual(last["bluesky_gallery"], "true")

    def test_unknown_kwargs_are_still_dropped(self):
        data = []
        self.client._add_facebook_params(
            data, facebook_page_id="1", not_a_real_field="drop-me"
        )
        last, _ = _form(data)
        self.assertEqual(last["facebook_page_id"], "1")
        self.assertNotIn("not_a_real_field", last)


class TestUploadTextForwardsNewFields(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.post = patch.object(
            self.client.session, "post", return_value=_response()
        ).start()
        self.addCleanup(patch.stopall)

    def test_reddit_and_threads_and_x_ride_along(self):
        self.client.upload_text(
            title="hi",
            user="my-profile",
            platforms=["reddit", "threads", "x"],
            reddit_nsfw=True,
            threads_reply_control="mentioned_only",
            x_paid_partnership=True,
            x_article_title="Article",
        )
        last, _ = _form(self.post.call_args[1]["data"])
        self.assertEqual(last["reddit_nsfw"], "true")
        self.assertEqual(last["threads_reply_control"], "mentioned_only")
        self.assertEqual(last["x_paid_partnership"], "true")
        self.assertEqual(last["x_article_title"], "Article")


if __name__ == "__main__":
    unittest.main()
