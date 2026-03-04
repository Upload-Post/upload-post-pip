"""
Upload-Post API Client

Cross-platform social media upload for TikTok, Instagram, YouTube, LinkedIn,
Facebook, Pinterest, Threads, Reddit, Bluesky, and X (Twitter).
"""

from pathlib import Path
from typing import Dict, List, Union, Optional, Any
import requests


class UploadPostError(Exception):
    """Base exception for Upload-Post API errors"""
    pass


class UploadPostClient:
    """
    Upload-Post API Client
    
    Supports uploading to: TikTok, Instagram, YouTube, LinkedIn, Facebook,
    Pinterest, Threads, Reddit, Bluesky, X (Twitter)
    
    Example:
        >>> client = UploadPostClient("YOUR_API_KEY")
        >>> response = client.upload_video(
        ...     "video.mp4",
        ...     title="My awesome video",
        ...     user="my-profile",
        ...     platforms=["tiktok", "instagram"]
        ... )
    """
    
    BASE_URL = "https://api.upload-post.com/api"
    
    def __init__(self, api_key: str):
        """
        Initialize the Upload-Post client.
        
        Args:
            api_key: Your API key from Upload-Post
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Apikey {self.api_key}",
            "User-Agent": "upload-post-python-client/2.0.0",
            "X-Upload-Post-Source": "pip",
        })

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[List[tuple]] = None,
        files: Optional[List[tuple]] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make an API request."""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                if json_data:
                    response = self.session.post(url, json=json_data)
                else:
                    response = self.session.post(url, data=data, files=files)
            elif method == "DELETE":
                if json_data:
                    response = self.session.delete(url, json=json_data)
                else:
                    response = self.session.delete(url)
            else:
                raise UploadPostError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message') or error_data.get('detail') or str(error_data)
                except (ValueError, KeyError):
                    pass
            raise UploadPostError(f"API request failed: {error_msg}") from e

    def _add_common_params(
        self,
        data: List[tuple],
        user: str,
        title: Optional[str],
        platforms: List[str],
        first_comment: Optional[str] = None,
        alt_text: Optional[str] = None,
        scheduled_date: Optional[str] = None,
        timezone: Optional[str] = None,
        add_to_queue: Optional[bool] = None,
        max_posts_per_slot: Optional[int] = None,
        async_upload: Optional[bool] = None,
        **kwargs
    ):
        """Add common upload parameters."""
        data.append(("user", user))
        if title:
            data.append(("title", title))
        for p in platforms:
            data.append(("platform[]", p))

        if first_comment:
            data.append(("first_comment", first_comment))
        if alt_text:
            data.append(("alt_text", alt_text))
        if scheduled_date:
            data.append(("scheduled_date", scheduled_date))
        if timezone:
            data.append(("timezone", timezone))
        if add_to_queue is not None:
            data.append(("add_to_queue", str(add_to_queue).lower()))
        if max_posts_per_slot is not None:
            data.append(("max_posts_per_slot", str(max_posts_per_slot)))
        if async_upload is not None:
            data.append(("async_upload", str(async_upload).lower()))
        
        # Platform-specific title overrides
        title_overrides = [
            "bluesky_title", "instagram_title", "facebook_title", "tiktok_title",
            "linkedin_title", "x_title", "youtube_title", "pinterest_title", "threads_title"
        ]
        for key in title_overrides:
            if kwargs.get(key):
                data.append((key, kwargs[key]))
        
        # Platform-specific description overrides
        desc_overrides = [
            "description", "linkedin_description", "youtube_description",
            "facebook_description", "tiktok_description", "pinterest_description"
        ]
        for key in desc_overrides:
            if kwargs.get(key):
                data.append((key, kwargs[key]))
        
        # Platform-specific first comment overrides
        comment_overrides = [
            "instagram_first_comment", "facebook_first_comment", "x_first_comment",
            "threads_first_comment", "youtube_first_comment", "reddit_first_comment",
            "bluesky_first_comment"
        ]
        for key in comment_overrides:
            if kwargs.get(key):
                data.append((key, kwargs[key]))

    def _add_tiktok_params(self, data: List[tuple], is_video: bool = True, **kwargs):
        """Add TikTok-specific parameters."""
        if kwargs.get("disable_comment") is not None:
            data.append(("disable_comment", str(kwargs["disable_comment"]).lower()))
        if kwargs.get("brand_content_toggle") is not None:
            data.append(("brand_content_toggle", str(kwargs["brand_content_toggle"]).lower()))
        if kwargs.get("brand_organic_toggle") is not None:
            data.append(("brand_organic_toggle", str(kwargs["brand_organic_toggle"]).lower()))
        
        if is_video:
            if kwargs.get("privacy_level"):
                data.append(("privacy_level", kwargs["privacy_level"]))
            if kwargs.get("disable_duet") is not None:
                data.append(("disable_duet", str(kwargs["disable_duet"]).lower()))
            if kwargs.get("disable_stitch") is not None:
                data.append(("disable_stitch", str(kwargs["disable_stitch"]).lower()))
            if kwargs.get("cover_timestamp") is not None:
                data.append(("cover_timestamp", str(kwargs["cover_timestamp"])))
            if kwargs.get("is_aigc") is not None:
                data.append(("is_aigc", str(kwargs["is_aigc"]).lower()))
            if kwargs.get("post_mode"):
                data.append(("post_mode", kwargs["post_mode"]))
        else:
            if kwargs.get("auto_add_music") is not None:
                data.append(("auto_add_music", str(kwargs["auto_add_music"]).lower()))
            if kwargs.get("photo_cover_index") is not None:
                data.append(("photo_cover_index", str(kwargs["photo_cover_index"])))

    def _add_instagram_params(self, data: List[tuple], is_video: bool = True, **kwargs):
        """Add Instagram-specific parameters."""
        if kwargs.get("media_type"):
            data.append(("media_type", kwargs["media_type"]))
        if kwargs.get("collaborators"):
            data.append(("collaborators", kwargs["collaborators"]))
        if kwargs.get("user_tags"):
            data.append(("user_tags", kwargs["user_tags"]))
        if kwargs.get("location_id"):
            data.append(("location_id", kwargs["location_id"]))
        
        if is_video:
            if kwargs.get("share_to_feed") is not None:
                data.append(("share_to_feed", str(kwargs["share_to_feed"]).lower()))
            if kwargs.get("cover_url"):
                data.append(("cover_url", kwargs["cover_url"]))
            if kwargs.get("audio_name"):
                data.append(("audio_name", kwargs["audio_name"]))
            if kwargs.get("thumb_offset"):
                data.append(("thumb_offset", kwargs["thumb_offset"]))

    def _add_youtube_params(self, data: List[tuple], **kwargs):
        """Add YouTube-specific parameters."""
        if kwargs.get("tags"):
            tags = kwargs["tags"]
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            for tag in tags:
                data.append(("tags[]", tag))
        if kwargs.get("categoryId"):
            data.append(("categoryId", kwargs["categoryId"]))
        if kwargs.get("privacyStatus"):
            data.append(("privacyStatus", kwargs["privacyStatus"]))
        if kwargs.get("embeddable") is not None:
            data.append(("embeddable", str(kwargs["embeddable"]).lower()))
        if kwargs.get("license"):
            data.append(("license", kwargs["license"]))
        if kwargs.get("publicStatsViewable") is not None:
            data.append(("publicStatsViewable", str(kwargs["publicStatsViewable"]).lower()))
        if kwargs.get("thumbnail_url"):
            data.append(("thumbnail_url", kwargs["thumbnail_url"]))
        if kwargs.get("selfDeclaredMadeForKids") is not None:
            data.append(("selfDeclaredMadeForKids", str(kwargs["selfDeclaredMadeForKids"]).lower()))
        if kwargs.get("containsSyntheticMedia") is not None:
            data.append(("containsSyntheticMedia", str(kwargs["containsSyntheticMedia"]).lower()))
        if kwargs.get("defaultLanguage"):
            data.append(("defaultLanguage", kwargs["defaultLanguage"]))
        if kwargs.get("defaultAudioLanguage"):
            data.append(("defaultAudioLanguage", kwargs["defaultAudioLanguage"]))
        if kwargs.get("allowedCountries"):
            data.append(("allowedCountries", kwargs["allowedCountries"]))
        if kwargs.get("blockedCountries"):
            data.append(("blockedCountries", kwargs["blockedCountries"]))
        if kwargs.get("hasPaidProductPlacement") is not None:
            data.append(("hasPaidProductPlacement", str(kwargs["hasPaidProductPlacement"]).lower()))
        if kwargs.get("recordingDate"):
            data.append(("recordingDate", kwargs["recordingDate"]))

    def _add_linkedin_params(self, data: List[tuple], is_text: bool = False, **kwargs):
        """Add LinkedIn-specific parameters."""
        if kwargs.get("visibility"):
            data.append(("visibility", kwargs["visibility"]))
        if kwargs.get("target_linkedin_page_id"):
            data.append(("target_linkedin_page_id", kwargs["target_linkedin_page_id"]))
        if is_text and (kwargs.get("linkedin_link_url") or kwargs.get("link_url")):
            link = kwargs.get("linkedin_link_url") or kwargs.get("link_url")
            data.append(("linkedin_link_url", link))

    def _add_facebook_params(self, data: List[tuple], is_video: bool = False, is_text: bool = False, **kwargs):
        """Add Facebook-specific parameters."""
        if kwargs.get("facebook_page_id"):
            data.append(("facebook_page_id", kwargs["facebook_page_id"]))
        
        if is_video:
            if kwargs.get("video_state"):
                data.append(("video_state", kwargs["video_state"]))
            if kwargs.get("facebook_media_type"):
                data.append(("facebook_media_type", kwargs["facebook_media_type"]))
            if kwargs.get("thumbnail_url"):
                data.append(("thumbnail_url", kwargs["thumbnail_url"]))

        if is_text and kwargs.get("facebook_link_url"):
            data.append(("facebook_link_url", kwargs["facebook_link_url"]))

    def _add_pinterest_params(self, data: List[tuple], is_video: bool = False, **kwargs):
        """Add Pinterest-specific parameters."""
        if kwargs.get("pinterest_board_id"):
            data.append(("pinterest_board_id", kwargs["pinterest_board_id"]))
        if kwargs.get("pinterest_alt_text"):
            data.append(("pinterest_alt_text", kwargs["pinterest_alt_text"]))
        if kwargs.get("pinterest_link"):
            data.append(("pinterest_link", kwargs["pinterest_link"]))
        
        if is_video:
            if kwargs.get("pinterest_cover_image_url"):
                data.append(("pinterest_cover_image_url", kwargs["pinterest_cover_image_url"]))
            if kwargs.get("pinterest_cover_image_content_type"):
                data.append(("pinterest_cover_image_content_type", kwargs["pinterest_cover_image_content_type"]))
            if kwargs.get("pinterest_cover_image_data"):
                data.append(("pinterest_cover_image_data", kwargs["pinterest_cover_image_data"]))
            if kwargs.get("pinterest_cover_image_key_frame_time") is not None:
                data.append(("pinterest_cover_image_key_frame_time", str(kwargs["pinterest_cover_image_key_frame_time"])))

    def _add_x_params(self, data: List[tuple], is_text: bool = False, **kwargs):
        """Add X (Twitter) specific parameters."""
        reply_settings = kwargs.get("reply_settings")
        if reply_settings and reply_settings != "everyone":
            data.append(("reply_settings", reply_settings))
        if kwargs.get("nullcast") is not None:
            data.append(("nullcast", str(kwargs["nullcast"]).lower()))
        if kwargs.get("quote_tweet_id"):
            data.append(("quote_tweet_id", kwargs["quote_tweet_id"]))
        if kwargs.get("geo_place_id"):
            data.append(("geo_place_id", kwargs["geo_place_id"]))
        if kwargs.get("for_super_followers_only") is not None:
            data.append(("for_super_followers_only", str(kwargs["for_super_followers_only"]).lower()))
        if kwargs.get("community_id"):
            data.append(("community_id", kwargs["community_id"]))
        if kwargs.get("share_with_followers") is not None:
            data.append(("share_with_followers", str(kwargs["share_with_followers"]).lower()))
        if kwargs.get("direct_message_deep_link"):
            data.append(("direct_message_deep_link", kwargs["direct_message_deep_link"]))
        if kwargs.get("x_long_text_as_post") is not None:
            data.append(("x_long_text_as_post", str(kwargs["x_long_text_as_post"]).lower()))
        
        if not is_text:
            if kwargs.get("tagged_user_ids"):
                ids = kwargs["tagged_user_ids"]
                if isinstance(ids, str):
                    ids = [t.strip() for t in ids.split(",")]
                for uid in ids:
                    data.append(("tagged_user_ids[]", uid))
            if kwargs.get("place_id"):
                data.append(("place_id", kwargs["place_id"]))
            if kwargs.get("x_thread_image_layout"):
                data.append(("x_thread_image_layout", kwargs["x_thread_image_layout"]))
        else:
            if kwargs.get("post_url"):
                data.append(("post_url", kwargs["post_url"]))
            if kwargs.get("card_uri"):
                data.append(("card_uri", kwargs["card_uri"]))
            
            if kwargs.get("poll_options"):
                poll_opts = kwargs["poll_options"]
                if isinstance(poll_opts, str):
                    poll_opts = [o.strip() for o in poll_opts.split(",")]
                for opt in poll_opts:
                    data.append(("poll_options[]", opt))
                if kwargs.get("poll_duration"):
                    data.append(("poll_duration", str(kwargs["poll_duration"])))
                if kwargs.get("poll_reply_settings"):
                    data.append(("poll_reply_settings", kwargs["poll_reply_settings"]))

    def _add_threads_params(self, data: List[tuple], **kwargs):
        """Add Threads-specific parameters."""
        if kwargs.get("threads_long_text_as_post") is not None:
            data.append(("threads_long_text_as_post", str(kwargs["threads_long_text_as_post"]).lower()))
        if kwargs.get("threads_thread_media_layout"):
            data.append(("threads_thread_media_layout", kwargs["threads_thread_media_layout"]))

    def _add_reddit_params(self, data: List[tuple], is_text: bool = False, **kwargs):
        """Add Reddit-specific parameters."""
        if kwargs.get("subreddit"):
            data.append(("subreddit", kwargs["subreddit"]))
        if kwargs.get("flair_id"):
            data.append(("flair_id", kwargs["flair_id"]))
        if is_text:
            reddit_link = kwargs.get("reddit_link_url") or kwargs.get("link_url")
            if reddit_link:
                data.append(("reddit_link_url", reddit_link))

    def upload_video(
        self,
        video_path: Union[str, Path],
        title: Optional[str] = None,
        user: str = "",
        platforms: Optional[List[str]] = None,
        **kwargs
    ) -> Dict:
        """
        Upload a video to social media platforms.

        Args:
            video_path: Path to video file or video URL.
            title: Video title/caption. Required for YouTube and Reddit.
                   Optional for TikTok, Instagram, Facebook, LinkedIn, X, Threads, Bluesky, Pinterest.
            user: User identifier (profile name).
            platforms: Target platforms. Supported: tiktok, instagram, youtube,
                      linkedin, facebook, pinterest, threads, bluesky, x

        Keyword Args:
            description: Video description
            first_comment: First comment to post
            scheduled_date: ISO date for scheduling (e.g., "2024-12-25T10:00:00Z")
            timezone: Timezone for scheduled date (e.g., "Europe/Madrid")
            add_to_queue: Add to posting queue
            async_upload: Process asynchronously (default: True)
            
            TikTok:
                privacy_level: PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, 
                              FOLLOWER_OF_CREATOR, SELF_ONLY
                disable_duet: Disable duet
                disable_comment: Disable comments
                disable_stitch: Disable stitch
                cover_timestamp: Timestamp in ms for cover
                is_aigc: AI-generated content flag
                post_mode: DIRECT_POST or MEDIA_UPLOAD
                brand_content_toggle: Branded content toggle
                brand_organic_toggle: Brand organic toggle
            
            Instagram:
                media_type: REELS or STORIES
                share_to_feed: Share to feed
                collaborators: Comma-separated collaborator usernames
                cover_url: Custom cover URL
                audio_name: Audio track name
                user_tags: Comma-separated user tags
                location_id: Location ID
                thumb_offset: Thumbnail offset
            
            YouTube:
                tags: List or comma-separated tags
                categoryId: Category ID (default: "22")
                privacyStatus: public, unlisted, private
                embeddable: Allow embedding
                license: youtube, creativeCommon
                publicStatsViewable: Show public stats
                thumbnail_url: Custom thumbnail URL
                selfDeclaredMadeForKids: Made for kids (COPPA)
                containsSyntheticMedia: AI/synthetic content flag
                defaultLanguage: Title/description language (BCP-47)
                defaultAudioLanguage: Audio language (BCP-47)
                allowedCountries: Comma-separated country codes
                blockedCountries: Comma-separated country codes
                hasPaidProductPlacement: Paid placement flag
                recordingDate: Recording date (ISO 8601)
            
            LinkedIn:
                visibility: PUBLIC, CONNECTIONS, LOGGED_IN, CONTAINER
                target_linkedin_page_id: Page ID for organization posts
            
            Facebook:
                facebook_page_id: Facebook Page ID
                video_state: PUBLISHED or DRAFT
                facebook_media_type: REELS, STORIES, or VIDEO
                thumbnail_url: Thumbnail URL for normal page videos (VIDEO type only)
            
            Pinterest:
                pinterest_board_id: Board ID
                pinterest_link: Destination link
                pinterest_cover_image_url: Cover image URL
                pinterest_cover_image_key_frame_time: Key frame time in ms
            
            X (Twitter):
                reply_settings: everyone, following, mentionedUsers, subscribers, verified
                nullcast: Promoted-only post
                tagged_user_ids: User IDs to tag
                place_id: Location place ID
                geo_place_id: Geographic place ID
                for_super_followers_only: Exclusive for super followers
                community_id: Community ID
                share_with_followers: Share community post with followers
                x_long_text_as_post: Post long text as single post
            
            Threads:
                threads_long_text_as_post: Post long text as single post

        Returns:
            API response with request_id for async uploads.

        Raises:
            UploadPostError: If upload fails or video file not found.
        """
        data: List[tuple] = []
        files: List[tuple] = []
        video_file = None
        
        try:
            video_str = str(video_path)
            if video_str.lower().startswith(("http://", "https://")):
                data.append(("video", video_str))
            else:
                video_p = Path(video_path)
                if not video_p.exists():
                    raise UploadPostError(f"Video file not found: {video_p}")
                video_file = video_p.open("rb")
                files.append(("video", (video_p.name, video_file)))
            
            self._add_common_params(data, user, title, platforms, **kwargs)
            
            if "tiktok" in platforms:
                self._add_tiktok_params(data, is_video=True, **kwargs)
            if "instagram" in platforms:
                self._add_instagram_params(data, is_video=True, **kwargs)
            if "youtube" in platforms:
                self._add_youtube_params(data, **kwargs)
            if "linkedin" in platforms:
                self._add_linkedin_params(data, **kwargs)
            if "facebook" in platforms:
                self._add_facebook_params(data, is_video=True, **kwargs)
            if "pinterest" in platforms:
                self._add_pinterest_params(data, is_video=True, **kwargs)
            if "x" in platforms:
                self._add_x_params(data, is_text=False, **kwargs)
            if "threads" in platforms:
                self._add_threads_params(data, **kwargs)
            
            return self._request("/upload", "POST", data=data, files=files if files else None)
            
        finally:
            if video_file:
                video_file.close()

    def upload_photos(
        self,
        photos: List[Union[str, Path]],
        title: Optional[str] = None,
        user: str = "",
        platforms: Optional[List[str]] = None,
        **kwargs
    ) -> Dict:
        """
        Upload photos to social media platforms.

        Args:
            photos: List of photo file paths or URLs.
            title: Post title/caption. Required for Reddit.
                   Optional for TikTok, Instagram, Facebook, LinkedIn, X, Threads, Bluesky, Pinterest.
            user: User identifier (profile name).
            platforms: Target platforms. Supported: tiktok, instagram, linkedin,
                      facebook, pinterest, threads, reddit, bluesky, x

        Keyword Args:
            description: Photo description
            first_comment: First comment to post
            alt_text: Alt text for accessibility
            scheduled_date: ISO date for scheduling
            timezone: Timezone for scheduled date
            add_to_queue: Add to posting queue
            async_upload: Process asynchronously
            
            TikTok:
                auto_add_music: Auto add music
                disable_comment: Disable comments
                photo_cover_index: Index of photo for cover (0-based)
                brand_content_toggle: Branded content toggle
                brand_organic_toggle: Brand organic toggle
            
            Instagram:
                media_type: IMAGE or STORIES
                collaborators: Comma-separated collaborator usernames
                user_tags: Comma-separated user tags
                location_id: Location ID
            
            LinkedIn:
                visibility: PUBLIC (only PUBLIC supported for photos)
                target_linkedin_page_id: Page ID for organization posts
            
            Facebook:
                facebook_page_id: Facebook Page ID
            
            Pinterest:
                pinterest_board_id: Board ID
                pinterest_alt_text: Alt text
                pinterest_link: Destination link
            
            X (Twitter):
                reply_settings: Who can reply
                nullcast: Promoted-only post
                tagged_user_ids: User IDs to tag
                x_long_text_as_post: Post long text as single post
                x_thread_image_layout: Comma-separated image layout for thread
                    (e.g. "4,4", "2,3,1", or "0,1"). Each value 0-4, total must
                    equal image count. 0 means no images for that tweet (useful
                    for URL preview cards). Auto-chunks into groups of 4 if >4
                    images and no layout specified.

            Threads:
                threads_long_text_as_post: Post long text as single post
                threads_thread_media_layout: Comma-separated media layout for thread
                    (e.g. "5,5", "3,4,3", or "0,1"). Each value 0-10, total must
                    equal media count. 0 means no media for that post. Auto-chunks
                    into groups of 10 if >10 items and no layout specified.

            Reddit:
                subreddit: Subreddit name (without r/)
                flair_id: Flair template ID

            first_comment_media: List of file paths to attach as images in
                the first comment. Supported on Reddit and X.

        Returns:
            API response.

        Raises:
            UploadPostError: If upload fails or photo file not found.
        """
        data: List[tuple] = []
        files: List[tuple] = []
        opened_files: List = []

        try:
            for photo in photos:
                photo_str = str(photo)
                if photo_str.lower().startswith(("http://", "https://")):
                    data.append(("photos[]", photo_str))
                else:
                    photo_p = Path(photo)
                    if not photo_p.exists():
                        raise UploadPostError(f"Photo file not found: {photo_p}")
                    photo_file = photo_p.open("rb")
                    opened_files.append(photo_file)
                    files.append(("photos[]", (photo_p.name, photo_file)))

            self._add_common_params(data, user, title, platforms, **kwargs)

            if "tiktok" in platforms:
                self._add_tiktok_params(data, is_video=False, **kwargs)
            if "instagram" in platforms:
                self._add_instagram_params(data, is_video=False, **kwargs)
            if "linkedin" in platforms:
                self._add_linkedin_params(data, **kwargs)
            if "facebook" in platforms:
                self._add_facebook_params(data, is_video=False, **kwargs)
            if "pinterest" in platforms:
                self._add_pinterest_params(data, is_video=False, **kwargs)
            if "x" in platforms:
                self._add_x_params(data, is_text=False, **kwargs)
            if "threads" in platforms:
                self._add_threads_params(data, **kwargs)
            if "reddit" in platforms:
                self._add_reddit_params(data, **kwargs)

            first_comment_media = kwargs.get("first_comment_media")
            if first_comment_media:
                for media_path in first_comment_media:
                    p = Path(media_path)
                    if not p.exists():
                        raise UploadPostError(f"First comment media file not found: {media_path}")
                    f = open(p, "rb")
                    opened_files.append(f)
                    files.append(("first_comment_media[]", (p.name, f)))

            return self._request("/upload_photos", "POST", data=data, files=files if files else None)

        finally:
            for f in opened_files:
                f.close()

    def upload_text(
        self,
        title: str,
        user: str,
        platforms: List[str],
        **kwargs
    ) -> Dict:
        """
        Upload text posts to social media platforms.

        Args:
            title: Text content for the post.
            user: User identifier (profile name).
            platforms: Target platforms. Supported: x, linkedin, facebook, 
                      threads, reddit, bluesky

        Keyword Args:
            first_comment: First comment to post
            scheduled_date: ISO date for scheduling
            timezone: Timezone for scheduled date
            add_to_queue: Add to posting queue
            async_upload: Process asynchronously
            link_url: Generic URL for link preview card (works for LinkedIn,
                Bluesky, Facebook). Platform-specific params take priority.

            LinkedIn:
                target_linkedin_page_id: Page ID for organization posts
                linkedin_link_url: URL to attach as link preview on LinkedIn

            Facebook:
                facebook_page_id: Facebook Page ID
                facebook_link_url: URL to attach as link preview on Facebook

            Bluesky:
                bluesky_link_url: URL to attach as external embed link preview

            X (Twitter):
                reply_settings: Who can reply
                post_url: URL to attach
                quote_tweet_id: Tweet ID to quote
                poll_options: Poll options (2-4 options)
                poll_duration: Poll duration in minutes (5-10080)
                poll_reply_settings: Who can reply to poll
                card_uri: Card URI for Twitter Cards
                x_long_text_as_post: Post long text as single post

            Threads:
                threads_long_text_as_post: Post long text as single post

            Reddit:
                subreddit: Subreddit name (without r/)
                flair_id: Flair template ID
                reddit_link_url: URL for link post. Creates a Reddit link post
                    (kind: "link") instead of a text post. Overrides `link_url`
                    for Reddit.

            first_comment_media: List of file paths to attach as images in
                the first comment. Supported on Reddit and X.

        Returns:
            API response.

        Raises:
            UploadPostError: If upload fails.
        """
        data: List[tuple] = []
        files: Optional[List[tuple]] = None

        self._add_common_params(data, user, title, platforms, **kwargs)

        # Generic link_url support
        if kwargs.get("link_url"):
            data.append(("link_url", kwargs["link_url"]))

        if "linkedin" in platforms:
            self._add_linkedin_params(data, is_text=True, **kwargs)
        if "facebook" in platforms:
            self._add_facebook_params(data, is_video=False, is_text=True, **kwargs)
        if "x" in platforms:
            self._add_x_params(data, is_text=True, **kwargs)
        if "threads" in platforms:
            self._add_threads_params(data, **kwargs)
        if "reddit" in platforms:
            self._add_reddit_params(data, is_text=True, **kwargs)
        if "bluesky" in platforms:
            bluesky_link = kwargs.get("bluesky_link_url")
            if bluesky_link:
                data.append(("bluesky_link_url", bluesky_link))

        first_comment_media = kwargs.get("first_comment_media")
        opened_files: List = []
        if first_comment_media:
            files = []
            for media_path in first_comment_media:
                p = Path(media_path)
                if not p.exists():
                    raise UploadPostError(f"First comment media file not found: {media_path}")
                f = open(p, "rb")
                opened_files.append(f)
                files.append(("first_comment_media[]", (p.name, f)))

        try:
            return self._request("/upload_text", "POST", data=data, files=files)
        finally:
            for f in opened_files:
                f.close()

    def upload_document(
        self,
        document_path: Union[str, Path],
        title: str,
        user: str,
        description: Optional[str] = None,
        visibility: Optional[str] = None,
        target_linkedin_page_id: Optional[str] = None,
        scheduled_date: Optional[str] = None,
        timezone: Optional[str] = None,
        add_to_queue: Optional[bool] = None,
        async_upload: Optional[bool] = None,
    ) -> Dict:
        """
        Upload a document to LinkedIn (PDF, PPT, PPTX, DOC, DOCX).

        Args:
            document_path: Path to document file or document URL.
            title: Post title/caption.
            user: User identifier (profile name).
            description: Document description/commentary.
            visibility: PUBLIC, CONNECTIONS, LOGGED_IN, CONTAINER
            target_linkedin_page_id: Page ID for organization posts.
            scheduled_date: ISO date for scheduling.
            timezone: Timezone for scheduled date.
            add_to_queue: Add to posting queue.
            async_upload: Process asynchronously.

        Returns:
            API response.

        Raises:
            UploadPostError: If upload fails or document file not found.
        """
        data: List[tuple] = []
        files: List[tuple] = []
        doc_file = None
        
        try:
            doc_str = str(document_path)
            if doc_str.lower().startswith(("http://", "https://")):
                data.append(("document", doc_str))
            else:
                doc_p = Path(document_path)
                if not doc_p.exists():
                    raise UploadPostError(f"Document file not found: {doc_p}")
                doc_file = doc_p.open("rb")
                files.append(("document", (doc_p.name, doc_file)))
            
            data.append(("user", user))
            data.append(("title", title))
            data.append(("platform[]", "linkedin"))
            
            if description:
                data.append(("description", description))
            if visibility:
                data.append(("visibility", visibility))
            if target_linkedin_page_id:
                data.append(("target_linkedin_page_id", target_linkedin_page_id))
            if scheduled_date:
                data.append(("scheduled_date", scheduled_date))
            if timezone:
                data.append(("timezone", timezone))
            if add_to_queue is not None:
                data.append(("add_to_queue", str(add_to_queue).lower()))
            if async_upload is not None:
                data.append(("async_upload", str(async_upload).lower()))
            
            return self._request("/upload_document", "POST", data=data, files=files if files else None)
            
        finally:
            if doc_file:
                doc_file.close()

    # ==================== Status & History ====================

    def get_status(self, request_id: str) -> Dict:
        """
        Get the status of an async upload.

        Args:
            request_id: The request_id from an async upload.

        Returns:
            Upload status.
        """
        return self._request("/uploadposts/status", "GET", params={"request_id": request_id})

    def get_history(self, page: int = 1, limit: int = 20) -> Dict:
        """
        Get upload history.

        Args:
            page: Page number.
            limit: Items per page (20, 50, or 100).

        Returns:
            Upload history.
        """
        return self._request("/uploadposts/history", "GET", params={"page": page, "limit": limit})

    def get_analytics(self, profile_username: str, platforms: Optional[List[str]] = None,
                      page_id: Optional[str] = None, page_urn: Optional[str] = None) -> Dict:
        """
        Get analytics for a profile.

        Args:
            profile_username: Profile username.
            platforms: Filter by platforms (instagram, linkedin, facebook, x, youtube, tiktok, threads, pinterest, reddit).
            page_id: Facebook Page ID (required for Facebook analytics).
            page_urn: LinkedIn page URN (defaults to "me" for personal profile).

        Returns:
            Analytics data per platform.
        """
        params = {}
        if platforms:
            params["platforms"] = ",".join(platforms)
        if page_id:
            params["page_id"] = page_id
        if page_urn:
            params["page_urn"] = page_urn
        return self._request(f"/analytics/{profile_username}", "GET", params=params if params else None)

    def get_total_impressions(
        self,
        profile_username: str,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        breakdown: bool = False,
        metrics: Optional[List[str]] = None,
    ) -> Dict:
        """
        Get total impressions for a profile from daily snapshots.

        Args:
            profile_username: Profile username.
            period: Period shortcut (last_day, last_week, last_month, last_3months, last_year).
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            date: Single date in YYYY-MM-DD format.
            platforms: Filter by platforms.
            breakdown: Include per-platform and per-day breakdown.
            metrics: Specific metrics to aggregate (e.g., ["likes", "comments", "shares"]).

        Returns:
            Total impressions data with optional breakdown.
        """
        params: Dict[str, Any] = {}
        if period:
            params["period"] = period
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if date:
            params["date"] = date
        if platforms:
            params["platform"] = ",".join(platforms)
        if breakdown:
            params["breakdown"] = "true"
        if metrics:
            params["metrics"] = ",".join(metrics)
        return self._request(f"/uploadposts/total-impressions/{profile_username}", "GET", params=params if params else None)

    def get_post_analytics(self, request_id: str) -> Dict:
        """
        Get analytics for a specific post across all platforms it was published to.

        Args:
            request_id: The request_id from the upload.

        Returns:
            Post analytics with per-platform metrics, profile snapshots, and post-level metrics.
        """
        return self._request(f"/uploadposts/post-analytics/{request_id}", "GET")

    def get_platform_metrics(self) -> Dict:
        """
        Get available metrics configuration for all supported platforms.

        Returns:
            Platform metrics config with primary fields, available metrics, and labels.
        """
        return self._request("/uploadposts/platform-metrics", "GET")

    # ==================== Scheduled Posts ====================

    def list_scheduled(self) -> Dict:
        """
        List scheduled posts.

        Returns:
            List of scheduled posts.
        """
        return self._request("/uploadposts/schedule", "GET")

    def cancel_scheduled(self, job_id: str) -> Dict:
        """
        Cancel a scheduled post.

        Args:
            job_id: Scheduled job ID.

        Returns:
            Cancellation result.
        """
        return self._request(f"/uploadposts/schedule/{job_id}", "DELETE")

    def edit_scheduled(
        self,
        job_id: str,
        scheduled_date: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> Dict:
        """
        Edit a scheduled post.

        Args:
            job_id: Scheduled job ID.
            scheduled_date: New scheduled date (ISO 8601).
            timezone: New timezone.

        Returns:
            Edit result.
        """
        body = {}
        if scheduled_date:
            body["scheduled_date"] = scheduled_date
        if timezone:
            body["timezone"] = timezone
        return self._request(f"/uploadposts/schedule/{job_id}", "POST", json_data=body)

    # ==================== User Management ====================

    def list_users(self) -> Dict:
        """
        List all users/profiles.

        Returns:
            List of users.
        """
        return self._request("/uploadposts/users", "GET")

    def create_user(self, username: str) -> Dict:
        """
        Create a new user/profile.

        Args:
            username: Profile name to create.

        Returns:
            Created user.
        """
        return self._request("/uploadposts/users", "POST", json_data={"username": username})

    def delete_user(self, username: str) -> Dict:
        """
        Delete a user/profile.

        Args:
            username: Profile name to delete.

        Returns:
            Deletion result.
        """
        return self._request("/uploadposts/users", "DELETE", json_data={"username": username})

    def generate_jwt(
        self,
        username: str,
        redirect_url: Optional[str] = None,
        logo_image: Optional[str] = None,
        redirect_button_text: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        show_calendar: Optional[bool] = None,
        readonly_calendar: Optional[bool] = None,
        connect_title: Optional[str] = None,
        connect_description: Optional[str] = None
    ) -> Dict:
        """
        Generate a JWT for platform integration.
        Used when integrating Upload-Post into your own platform.

        Args:
            username: Profile username.
            redirect_url: URL to redirect after linking.
            logo_image: Logo image URL for the linking page.
            redirect_button_text: Text for redirect button.
            platforms: Platforms to show for connection.
            show_calendar: Whether to show the calendar view.
            readonly_calendar: Show only a read-only calendar (no editing, no account connection).
            connect_title: Custom title for the connection page.
            connect_description: Custom description for the connection page.

        Returns:
            JWT and connection URL.
        """
        body: Dict[str, Any] = {"username": username}
        if redirect_url:
            body["redirect_url"] = redirect_url
        if logo_image:
            body["logo_image"] = logo_image
        if redirect_button_text:
            body["redirect_button_text"] = redirect_button_text
        if platforms:
            body["platforms"] = platforms
        if show_calendar is not None:
            body["show_calendar"] = show_calendar
        if readonly_calendar is not None:
            body["readonly_calendar"] = readonly_calendar
        if connect_title:
            body["connect_title"] = connect_title
        if connect_description:
            body["connect_description"] = connect_description
        return self._request("/uploadposts/users/generate-jwt", "POST", json_data=body)

    def validate_jwt(self, jwt: str) -> Dict:
        """
        Validate a JWT token.

        Args:
            jwt: JWT token to validate.

        Returns:
            Validation result.
        """
        return self._request("/uploadposts/users/validate-jwt", "POST", json_data={"jwt": jwt})

    # ==================== Helper Endpoints ====================

    def get_facebook_pages(self, profile: Optional[str] = None) -> Dict:
        """
        Get Facebook pages for a profile.

        Args:
            profile: Profile username.

        Returns:
            List of Facebook pages.
        """
        params = {"profile": profile} if profile else None
        return self._request("/uploadposts/facebook/pages", "GET", params=params)

    def get_linkedin_pages(self, profile: Optional[str] = None) -> Dict:
        """
        Get LinkedIn pages for a profile.

        Args:
            profile: Profile username.

        Returns:
            List of LinkedIn pages.
        """
        params = {"profile": profile} if profile else None
        return self._request("/uploadposts/linkedin/pages", "GET", params=params)

    def get_pinterest_boards(self, profile: Optional[str] = None) -> Dict:
        """
        Get Pinterest boards for a profile.

        Args:
            profile: Profile username.

        Returns:
            List of Pinterest boards.
        """
        params = {"profile": profile} if profile else None
        return self._request("/uploadposts/pinterest/boards", "GET", params=params)
