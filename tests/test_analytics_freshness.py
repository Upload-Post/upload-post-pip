"""Tests for the analytics freshness endpoints and parameters.

refresh, the daily history of a post, /cached sort / origin / date_field, the
period of /api/analytics, insights and analytics status.

No network: the session's HTTP verbs are patched, so every assertion is about
what the client would have sent.

Run with: python -m unittest discover -s tests
"""

import unittest
from unittest.mock import MagicMock, patch

from upload_post import UploadPostClient, UploadPostError


def _response(payload=None, status=200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload if payload is not None else {"success": True}
    response.raise_for_status.return_value = None
    return response


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.client = UploadPostClient("test-key")
        self.get = patch.object(self.client.session, "get", return_value=_response()).start()
        self.addCleanup(patch.stopall)

    def assertGet(self, endpoint, params):
        url, kwargs = self.get.call_args[0][0], self.get.call_args[1]
        self.assertEqual(url, f"https://api.upload-post.com/api{endpoint}")
        self.assertEqual(kwargs["params"], params)


class TestPostAnalytics(ClientTestCase):
    def test_request_id_alone_sends_no_query_as_before(self):
        self.client.get_post_analytics("req-1")
        self.assertGet("/uploadposts/post-analytics/req-1", None)

    def test_platform_and_refresh(self):
        self.client.get_post_analytics("req-1", platform="tiktok", refresh=True)
        self.assertGet("/uploadposts/post-analytics/req-1", {"platform": "tiktok", "refresh": "true"})

    def test_platform_only_is_unchanged(self):
        self.client.get_post_analytics("req-1", "x")
        self.assertGet("/uploadposts/post-analytics/req-1", {"platform": "x"})

    def test_by_platform_id_with_and_without_refresh(self):
        self.client.get_post_analytics_by_platform_id("7300", "youtube", "brand")
        self.assertGet("/uploadposts/post-analytics",
                       {"platform_post_id": "7300", "platform": "youtube", "user": "brand"})
        self.client.get_post_analytics_by_platform_id("7300", "youtube", "brand", refresh=True)
        self.assertGet("/uploadposts/post-analytics",
                       {"platform_post_id": "7300", "platform": "youtube", "user": "brand", "refresh": "true"})


class TestDaily(ClientTestCase):
    def test_daily_by_request_id(self):
        self.client.get_post_analytics_daily("req-1", "tiktok", since="2026-11-01", until="2026-11-15")
        self.assertGet("/uploadposts/post-analytics/req-1/daily",
                       {"platform": "tiktok", "since": "2026-11-01", "until": "2026-11-15"})

    def test_daily_without_platform_is_refused_before_any_request(self):
        with self.assertRaises(UploadPostError):
            self.client.get_post_analytics_daily("req-1", "")
        self.get.assert_not_called()

    def test_daily_by_platform_id(self):
        self.client.get_post_analytics_daily_by_platform_id("7300", "x", "brand", since="2026-11-01")
        self.assertGet("/uploadposts/post-analytics/daily",
                       {"platform_post_id": "7300", "platform": "x", "user": "brand", "since": "2026-11-01"})


class TestCached(ClientTestCase):
    def test_without_new_options_is_unchanged(self):
        self.client.get_cached_post_analytics("brand", platform="tiktok", limit=50)
        self.assertGet("/uploadposts/post-analytics/cached", {"user": "brand", "platform": "tiktok", "limit": 50})

    def test_sort_order_date_field_origin(self):
        self.client.get_cached_post_analytics("brand", sort="-views", order="desc",
                                              date_field="published_at", origin="all")
        self.assertGet("/uploadposts/post-analytics/cached", {
            "user": "brand", "sort": "-views", "order": "desc", "date_field": "published_at", "origin": "all",
        })


class TestAccountPeriod(ClientTestCase):
    def test_since_until_compare(self):
        self.client.get_analytics("brand", platforms=["instagram", "youtube"],
                                  since="2026-10-17", until="2026-11-15", compare="previous")
        self.assertGet("/analytics/brand", {
            "platforms": "instagram,youtube", "since": "2026-10-17", "until": "2026-11-15", "compare": "previous",
        })

    def test_without_period_is_unchanged(self):
        self.client.get_analytics("brand", platforms=["tiktok"])
        self.assertGet("/analytics/brand", {"platforms": "tiktok"})


class TestInsightsAndStatus(ClientTestCase):
    def test_insights(self):
        self.client.get_insights("brand", platform="tiktok", since="2026-10-01")
        self.assertGet("/uploadposts/insights", {"user": "brand", "platform": "tiktok", "since": "2026-10-01"})

    def test_analytics_status(self):
        self.client.get_analytics_status()
        self.assertGet("/uploadposts/analytics-status", None)
        self.client.get_analytics_status(user="brand", platform="x")
        self.assertGet("/uploadposts/analytics-status", {"user": "brand", "platform": "x"})


if __name__ == "__main__":
    unittest.main()
