"""TikTok Ads (the customer's own TikTok ad account).

Each method sends the request the API expects, and what TikTok has not granted
Upload-Post (spark/authorize-post, the boost of the profile's own post) stays
out. No network: the session is patched.

Run with: python -m unittest discover -s tests
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://api.upload-post.com/api/uploadposts/ads/tiktok"
SHIPPED = ""
for name in ("upload_post/api_client.py", "README.md", "CHANGELOG.md"):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        SHIPPED += fh.read()

METHODS = [
    "start_tiktok_ads_connection", "list_tiktok_ads_grant_advertisers", "list_tiktok_ads_accounts",
    "connect_tiktok_ads_account", "disconnect_tiktok_ads_account", "get_tiktok_ads_account", "boost_tiktok_post",
    "list_tiktok_spark_posts", "pause_tiktok_campaign", "resume_tiktok_campaign", "delete_tiktok_campaign",
    "pause_tiktok_adgroup", "resume_tiktok_adgroup", "delete_tiktok_adgroup", "pause_tiktok_ad", "resume_tiktok_ad",
    "delete_tiktok_ad", "list_tiktok_ads_locations", "list_tiktok_ads_interests", "list_tiktok_campaigns",
    "create_tiktok_campaign", "list_tiktok_adgroups", "create_tiktok_adgroup", "list_tiktok_ads", "create_tiktok_ad",
    "get_tiktok_ads_insights", "get_tiktok_campaign_insights", "get_tiktok_adgroup_insights", "get_tiktok_ad_insights",
    "upload_tiktok_video_creative", "upload_tiktok_image_creative", "list_tiktok_ads_identities",
    "list_tiktok_ads_audiences", "create_tiktok_customer_file_audience", "create_tiktok_lookalike_audience",
    "update_tiktok_campaign", "update_tiktok_ad_group", "update_tiktok_ad", "delete_tiktok_audience",
]


class TestTiktokAds(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("k")
        response = MagicMock()
        response.json.return_value = {"success": True}
        response.raise_for_status.return_value = None
        self.request = patch.object(self.client.session, "request", return_value=response).start()
        self.addCleanup(patch.stopall)

    def sent(self, i=-1):
        args, kwargs = self.request.call_args_list[i]
        return args[0], args[1], kwargs

    def test_every_operation_has_a_method_none_marked_not_generally_available(self):
        self.assertEqual(len(METHODS), 39)
        for name in METHODS:
            with self.subTest(method=name):
                self.assertTrue(callable(getattr(UploadPostClient, name, None)), name)
        ops = [op_id for op_id, (_, route, meta) in UploadPostClient._OPENAPI_OPERATIONS.items()
               if route.startswith("/uploadposts/ads/tiktok")]
        self.assertEqual(len(ops), 39)
        for op_id in ops:
            self.assertNotIn("na", UploadPostClient._OPENAPI_OPERATIONS[op_id][2], op_id)

    def test_no_spark_authorization_of_the_own_post(self):
        self.assertFalse(hasattr(UploadPostClient, "authorize_tiktok_post_for_spark_ads"))
        self.assertNotIn("authorizeTiktokPostForSparkAds", UploadPostClient._OPENAPI_OPERATIONS)
        self.assertNotIn("authorization_days", UploadPostClient._OPENAPI_OPERATIONS["boostTiktokPost"][2]["b"])
        for text in ("spark/authorize-post", "tiktok_spark_scope_missing", "Spark Ads permission", "own TikTok account"):
            self.assertNotIn(text, SHIPPED, text)

    def test_boost_sends_a_json_body_with_the_post_of_the_linked_account(self):
        self.client.boost_tiktok_post(
            "reach", {"amount": 20, "type": "daily"}, {"countries": ["ES"], "age_min": 18},
            profile_username="my-profile", identity_id="5f39abca-0000-4000-8000-000000000001",
            post_id="7311111111111111111", pause_all_levels=True, idempotency_key="boost-1")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("POST", f"{BASE}/boost"))
        self.assertEqual(kwargs["json"], {
            "goal": "reach", "budget": {"amount": 20, "type": "daily"}, "targeting": {"countries": ["ES"], "age_min": 18},
            "profile_username": "my-profile", "identity_id": "5f39abca-0000-4000-8000-000000000001",
            "post_id": "7311111111111111111", "pause_all_levels": True, "idempotency_key": "boost-1",
        })

    def test_spark_posts_of_an_identity_go_in_the_query(self):
        self.client.list_tiktok_spark_posts(identity_id="id-1", cursor="1732700000000", count=20)
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("GET", f"{BASE}/spark/posts"))
        self.assertEqual(kwargs["params"], {"identity_id": "id-1", "cursor": "1732700000000", "count": 20})

    def test_create_campaign_adgroup_and_ad(self):
        self.client.create_tiktok_campaign("Summer", "video_views", profile_username="my-profile")
        self.client.create_tiktok_adgroup("c1", "ES", "video_views", {"amount": 25}, {"countries": ["ES"]})
        self.client.create_tiktok_ad("g1", "Ad", identity_id="id-1", post_id="p1",
                                     landing_page_url="https://example.com", call_to_action="SHOP_NOW")
        calls = [self.sent(i)[:2] for i in range(3)]
        self.assertEqual(calls, [("POST", f"{BASE}/campaigns"), ("POST", f"{BASE}/adgroups"), ("POST", f"{BASE}/ads")])
        self.assertEqual(self.sent(0)[2]["json"], {"name": "Summer", "goal": "video_views", "profile_username": "my-profile"})
        self.assertEqual(self.sent(1)[2]["json"]["campaign_id"], "c1")
        self.assertEqual(self.sent(2)[2]["json"], {
            "adgroup_id": "g1", "name": "Ad", "identity_id": "id-1", "post_id": "p1",
            "landing_page_url": "https://example.com", "call_to_action": "SHOP_NOW",
        })

    def test_pause_resume_delete_put_the_id_in_the_path(self):
        self.client.pause_tiktok_campaign("18001", advertiser_id="7300")
        self.client.resume_tiktok_adgroup("18002", profile_username="my-profile")
        self.client.delete_tiktok_ad("18003", confirm=True)
        self.assertEqual([self.sent(i)[:2] for i in range(3)], [
            ("POST", f"{BASE}/campaigns/18001/pause"), ("POST", f"{BASE}/adgroups/18002/resume"),
            ("POST", f"{BASE}/ads/18003/delete"),
        ])
        self.assertEqual(self.sent(0)[2]["json"], {"advertiser_id": "7300"})
        self.assertEqual(self.sent(2)[2]["json"], {"confirm": True})

    def test_update_ad_group_is_a_patch(self):
        self.client.update_tiktok_ad_group("18002", budget=40)
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("PATCH", f"{BASE}/adgroups/18002"))
        self.assertEqual(kwargs["json"], {"budget": 40})

    def test_campaign_insights_by_day(self):
        self.client.get_tiktok_campaign_insights("18001", start_date="2026-11-18", end_date="2026-11-24", breakdown="day")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("GET", f"{BASE}/campaigns/18001/insights"))
        self.assertEqual(kwargs["params"], {"start_date": "2026-11-18", "end_date": "2026-11-24", "breakdown": "day"})

    def test_disconnect_sends_the_profile_in_the_query(self):
        self.client.disconnect_tiktok_ads_account("7300", profile_username="my-profile")
        method, url, kwargs = self.sent()
        self.assertEqual((method, url), ("DELETE", f"{BASE}/accounts/7300"))
        self.assertEqual(kwargs["params"], {"profile_username": "my-profile"})
        self.assertIsNone(kwargs.get("json"))


if __name__ == "__main__":
    unittest.main()
