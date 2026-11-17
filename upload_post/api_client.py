"""
Upload-Post API Client

Cross-platform social media upload for TikTok, Instagram, YouTube, LinkedIn,
Facebook, Pinterest, Threads, Reddit, Bluesky, Discord, Telegram, and X (Twitter).
"""

from pathlib import Path
from typing import Dict, List, Union, Optional, Any
from urllib.parse import quote
import json
import os
import re
import requests


class UploadPostError(Exception):
    """Base exception for Upload-Post API errors.

    ``str(error)`` is the readable message, as before. When the API answered,
    the error also carries what it said, so code can branch on it instead of
    parsing text:

    - ``status_code``: HTTP status (``None`` when no answer arrived).
    - ``error_code``: the stable machine code of the answer, read from
      ``error_code``, ``code`` or ``reason`` (for example
      ``"bluesky_dm_scope_missing"``, ``"TEAM_SEAT_SUSPENDED"``,
      ``"comment_not_found"``, ``"webhook_removed"``).
    - ``response``: the decoded JSON body (``None`` if it was not JSON).
    - ``retry_after``: the ``Retry-After`` header in seconds, when present.
    - ``error_type``: the ``error_type`` of the answer, when it has one.
    """

    def __init__(
        self,
        message: str = "",
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        response: Optional[Any] = None,
        retry_after: Optional[float] = None,
    ):
        super().__init__(message)
        # error_type: the Google Business / Ads zones' kind of failure, when sent.
        self.error_type: Optional[str] = None
        self.status_code = status_code
        self.error_code = error_code
        self.response = response
        self.retry_after = retry_after


class UploadPostClient:
    """
    Upload-Post API Client
    
    Supports uploading to: TikTok, Instagram, YouTube, LinkedIn, Facebook,
    Pinterest, Threads, Reddit, Bluesky, Discord, Telegram, X (Twitter)
    
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
    
    def __init__(self, api_key: str, act_as_user: Optional[str] = None):
        """
        Initialize the Upload-Post client.

        Args:
            api_key: Your API key from Upload-Post
            act_as_user: Team members only: the email of the account owner to
                work on. Every request is sent with ``X-Act-As-User`` and acts
                on that account. If the owner's current plan no longer covers
                your team seat, requests fail with ``UploadPostError``
                (``status_code`` 403, ``error_code`` ``"TEAM_SEAT_SUSPENDED"``);
                access comes back by itself when the owner upgrades or frees a
                seat.
        """
        self.api_key = api_key
        self.act_as_user = act_as_user
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Apikey {self.api_key}",
            "User-Agent": "upload-post-python-client/2.0.0",
            "X-Upload-Post-Source": "pip",
        })
        if act_as_user:
            self.session.headers["X-Act-As-User"] = act_as_user

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[List[tuple]] = None,
        files: Optional[List[tuple]] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        raw: bool = False,
    ) -> Dict:
        """Make an API request. ``raw=True`` returns the body as text (file downloads)."""
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
            elif method == "PATCH":
                if json_data is None and (data is not None or files is not None):
                    response = self.session.patch(url, data=data, files=files)
                else:
                    response = self.session.patch(url, json=json_data)
            elif method == "PUT":
                if json_data is None and (data is not None or files is not None):
                    response = self.session.put(url, data=data, files=files)
                else:
                    response = self.session.put(url, json=json_data)
            else:
                raise UploadPostError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            if raw:
                return response.text
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise self._api_error(e) from e

    @staticmethod
    def _api_error(e: "requests.exceptions.RequestException") -> "UploadPostError":
        """The UploadPostError for a failed request, with what the API answered."""
        error_msg = str(e)
        status_code = error_code = error_data = retry_after = None
        if hasattr(e, 'response') and e.response is not None:
            status_code = getattr(e.response, "status_code", None)
            try:
                error_data = e.response.json()
            except ValueError:
                error_data = None
            if isinstance(error_data, dict):
                error_msg = (error_data.get('message') or error_data.get('detail')
                             or error_data.get('error') or str(error_data))
                if not isinstance(error_msg, str):
                    error_msg = str(error_msg)
                for key in ("error_code", "code", "reason"):
                    if isinstance(error_data.get(key), str) and error_data[key]:
                        error_code = error_data[key]
                        break
            headers = getattr(e.response, "headers", None) or {}
            try:
                raw = headers.get("Retry-After")
                retry_after = float(raw) if raw not in (None, "") else None
            except (TypeError, ValueError, AttributeError):
                retry_after = None
        error = UploadPostError(
            f"API request failed: {error_msg}",
            status_code=status_code,
            error_code=error_code,
            response=error_data,
            retry_after=retry_after,
        )
        if isinstance(error_data, dict) and isinstance(error_data.get("error_type"), str):
            error.error_type = error_data["error_type"]
        return error

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
        # AI auto-generation of native per-platform copy from the media (fills blank fields)
        # Sponsored / paid-partnership post, mapped by the API to each network's
        # native label (TikTok brand_content_toggle, YouTube
        # hasPaidProductPlacement, X paid_partnership; Facebook and Pinterest
        # also need their sponsor id). A network-specific field wins over it.
        self._put(data, "paid_partnership", kwargs.get("paid_partnership"), "bool")
        
        # Platform-specific title overrides
        title_overrides = [
            "bluesky_title", "instagram_title", "facebook_title", "tiktok_title",
            "linkedin_title", "x_title", "youtube_title", "pinterest_title", "threads_title",
            "telegram_title",
            # New credential-based platforms
            "slack_title", "mastodon_title", "nostr_title", "lemmy_title", "devto_title",
            "hashnode_title", "wordpress_title", "whop_title", "listmonk_title"
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
        
        # Platform-specific first comment overrides. TikTok needs the
        # `comments` capability on the connection: without it the post still
        # publishes and the response carries a warning instead of the comment.
        comment_overrides = [
            "instagram_first_comment", "facebook_first_comment", "x_first_comment",
            "threads_first_comment", "youtube_first_comment", "reddit_first_comment",
            "bluesky_first_comment", "linkedin_first_comment", "tiktok_first_comment",
            "telegram_first_comment"
        ]
        for key in comment_overrides:
            if kwargs.get(key):
                data.append((key, kwargs[key]))

    @staticmethod
    def _put(data: List[tuple], key: str, value, kind: str = "str"):
        """Append one form field. kind: str, bool, json, list, upper."""
        if value is None:
            return
        if kind == "bool":
            data.append((key, str(value).lower()))
            return
        if kind == "json":
            if isinstance(value, (dict, list)):
                data.append((key, json.dumps(value)))
            elif value != "":
                data.append((key, str(value)))
            return
        if kind == "list":
            if isinstance(value, (list, tuple)):
                form_key = key if key.endswith("[]") else f"{key}[]"
                for item in value:
                    if item is None or item == "":
                        continue
                    if isinstance(item, (dict, list)):
                        data.append((form_key, json.dumps(item)))
                    else:
                        data.append((form_key, str(item)))
            elif value != "":
                data.append((key, str(value)))
            return
        if kind == "upper":
            if value != "":
                data.append((key, str(value).upper()))
            return
        if value == "":
            return
        data.append((key, str(value)))

    def _put_many(self, data: List[tuple], kwargs: dict, spec):
        """Copy whitelisted kwargs into multipart. spec: (key, kind) pairs."""
        for key, kind in spec:
            self._put(data, key, kwargs.get(key), kind)

    def _put_file(
        self,
        data: List[tuple],
        files: Optional[List[tuple]],
        opened: Optional[List],
        key: str,
        value,
    ):
        """Attach a local file, or send a URL / media id as a form string."""
        if value is None or value == "":
            return
        val = str(value)
        if val.lower().startswith(("http://", "https://")):
            data.append((key, val))
            return
        path = Path(val)
        if files is not None and path.exists():
            fh = path.open("rb")
            if opened is not None:
                opened.append(fh)
            files.append((key, (path.name, fh)))
            return
        data.append((key, val))

    def _add_first_comment_media(self, files: List[tuple], opened: List, items) -> None:
        """Attach the first comment images (``first_comment_media[]``).

        The API takes them as files only (a URL in that field was ignored), so
        local paths are opened, bytes are sent as they are, and http(s) URLs are
        downloaded here and sent as files. A URL that cannot be downloaded, or a
        path that does not exist, raises UploadPostError instead of publishing
        without the images.
        """
        if not items:
            return
        if isinstance(items, (str, Path, bytes, bytearray)):
            items = [items]
        for item in items:
            if isinstance(item, (bytes, bytearray)):
                files.append(("first_comment_media[]", ("image.jpg", bytes(item))))
                continue
            value = str(item)
            if value.lower().startswith(("http://", "https://")):
                try:
                    # Plain request, not the session: the API key must not go to another host.
                    response = requests.get(value, timeout=60)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    raise UploadPostError(
                        f"Could not download first_comment_media {value} ({e}). The API takes "
                        "first comment images as files: pass a local path or bytes instead."
                    ) from e
                name = os.path.basename(value.split("?", 1)[0].rstrip("/")) or "image.jpg"
                content_type = (response.headers.get("Content-Type") or "").split(";")[0] or None
                part = (name, response.content, content_type) if content_type else (name, response.content)
                files.append(("first_comment_media[]", part))
                continue
            p = Path(value)
            if not p.exists():
                raise UploadPostError(f"First comment media file not found: {item}")
            f = open(p, "rb")
            opened.append(f)
            files.append(("first_comment_media[]", (p.name, f)))

    def _add_all_platform_params(
        self,
        data: List[tuple],
        platforms: Optional[List[str]],
        *,
        is_video: bool = False,
        is_text: bool = False,
        files: Optional[List[tuple]] = None,
        opened: Optional[List] = None,
        **kwargs,
    ):
        """Dispatch platform whitelists. Fields not listed here are dropped."""
        if "tiktok" in platforms and not is_text:
            self._add_tiktok_params(data, is_video=is_video, **kwargs)
        if "instagram" in platforms and not is_text:
            self._add_instagram_params(data, is_video=is_video, files=files, **kwargs)
        if "youtube" in platforms and is_video:
            self._add_youtube_params(data, files=files, **kwargs)
        if "linkedin" in platforms:
            self._add_linkedin_params(
                data, is_text=is_text, files=files, opened=opened, **kwargs
            )
        if "facebook" in platforms:
            self._add_facebook_params(
                data, is_video=is_video, is_text=is_text, **kwargs
            )
        if "pinterest" in platforms and not is_text:
            self._add_pinterest_params(data, is_video=is_video, **kwargs)
        if "x" in platforms:
            self._add_x_params(
                data, is_text=is_text, files=files, opened=opened, **kwargs
            )
        if "threads" in platforms:
            self._add_threads_params(data, is_text=is_text, **kwargs)
        if "reddit" in platforms:
            self._add_reddit_params(data, is_text=is_text, **kwargs)
        if "google_business" in platforms:
            self._add_google_business_params(data, **kwargs)
        if "bluesky" in platforms:
            self._add_bluesky_params(data, **kwargs)
        if "discord" in platforms:
            self._add_discord_params(data, **kwargs)
        if "telegram" in platforms:
            self._add_telegram_params(data, files=files, opened=opened, **kwargs)
        if "mastodon" in platforms:
            self._add_mastodon_params(data, **kwargs)
        if "wordpress" in platforms:
            self._add_wordpress_params(data, **kwargs)
        if "lemmy" in platforms:
            self._add_lemmy_params(data, **kwargs)
        if "slack" in platforms:
            self._add_slack_params(data, **kwargs)
        if "nostr" in platforms:
            self._add_nostr_params(data, **kwargs)
        if "devto" in platforms:
            self._add_devto_params(data, **kwargs)
        if "hashnode" in platforms:
            self._add_hashnode_params(data, **kwargs)
        if "whop" in platforms:
            self._add_whop_params(data, **kwargs)
        if "listmonk" in platforms:
            self._add_listmonk_params(data, **kwargs)

    # TikTok form fields, by where they apply. Booleans go out lowercased
    # ("true"/"false"), everything else as a plain string.
    #
    # The shared block is shared on purpose: the backend reads privacy_level and
    # post_mode on both /upload and /upload_photos, and the photo endpoint also
    # accepts the music track id, the location pair and is_ai_generated. They
    # used to sit behind the `is_video` gate, so photo carousels silently
    # published as PUBLIC_TO_EVERYONE / DIRECT_POST (issue #24) and could not
    # carry music or a location tag at all.
    #
    # The music/location/cover/draft fields need the matching capability on the
    # connection (see `capabilities` on the TikTok account returned by
    # list_users()). Without it the field is ignored, the post still publishes,
    # and the response includes a per-field `warnings` entry.
    _TIKTOK_SHARED_FIELDS = (
        ("disable_comment", True),
        ("brand_content_toggle", True),
        ("brand_organic_toggle", True),
        ("privacy_level", False),
        ("post_mode", False),
        ("tiktok_music_id", False),
        ("tiktok_location_id", False),
        ("tiktok_location_name", False),
        ("tiktok_is_ai_generated", True),
        ("is_ai_generated", True),
        # post_mode="MEDIA_UPLOAD" and tiktok_upload_to_draft=True are the same
        # draft. Aliases upload_to_draft / is_draft are accepted too.
        ("tiktok_upload_to_draft", True),
        ("upload_to_draft", True),
        ("is_draft", True),
        # TikTok's "Disclose post content" switch and its two kinds (your own
        # brand, branded content for a third party).
        ("disclose_commercial", True),
        ("your_brand", True),
        ("branded_content", True),
    )
    # Video-only: TikTok's photo contract takes the track id alone, with no
    # volume or trim, and has no custom cover.
    _TIKTOK_VIDEO_FIELDS = (
        ("disable_duet", True),
        ("disable_stitch", True),
        ("cover_timestamp", False),
        ("is_aigc", True),
        ("tiktok_music_volume", False),
        ("tiktok_music_start", False),
        ("tiktok_music_end", False),
        ("tiktok_original_sound_volume", False),
        ("tiktok_cover_image_url", False),
        ("tiktok_is_ads_only", True),
        ("is_ads_only", True),
        ("tiktok_tto_invite_link", False),
        ("tto_invite_link", False),
    )
    _TIKTOK_PHOTO_FIELDS = (
        ("auto_add_music", True),
        ("photo_cover_index", False),
    )

    def _add_tiktok_params(self, data: List[tuple], is_video: bool = True, **kwargs):
        """Add TikTok-specific parameters."""
        fields = self._TIKTOK_SHARED_FIELDS + (
            self._TIKTOK_VIDEO_FIELDS if is_video else self._TIKTOK_PHOTO_FIELDS
        )
        for key, is_bool in fields:
            value = kwargs.get(key)
            # privacy_level and post_mode keep their historical truthiness check:
            # an empty string means "not set", not "send an empty value".
            if value is None or (not is_bool and value == ""):
                continue
            data.append((key, str(value).lower() if is_bool else str(value)))

    def _add_instagram_params(self, data: List[tuple], is_video: bool = True, files: List[tuple] | None = None, **kwargs):
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
            # Trial Reels: TRIAL_REELS_SHARE_TO_FOLLOWERS_IF_LIKED or TRIAL_REELS_DONT_SHARE_TO_FOLLOWERS.
            self._put(data, "share_mode", kwargs.get("share_mode"))
            # The Reels cover as a local file (cover_url takes a URL or a path too).
            cover_image = kwargs.get("cover_image")
            if cover_image and files is not None:
                cover_path = Path(str(cover_image))
                if cover_path.is_file():
                    files.append(("cover_image", (cover_path.name, cover_path.open("rb"))))
            if kwargs.get("cover_url"):
                cover_val = str(kwargs["cover_url"])
                if cover_val.lower().startswith(("http://", "https://")):
                    data.append(("cover_url", cover_val))
                elif files is not None:
                    cover_path = Path(cover_val)
                    if cover_path.exists():
                        files.append(("cover_image", (cover_path.name, cover_path.open("rb"))))
                else:
                    data.append(("cover_url", cover_val))
            if kwargs.get("audio_name"):
                data.append(("audio_name", kwargs["audio_name"]))
            if kwargs.get("thumb_offset"):
                data.append(("thumb_offset", kwargs["thumb_offset"]))

        self._put_many(data, kwargs, (
            ("instagram_alt_text", "list"),
        ))

    def _add_youtube_params(self, data: List[tuple], files: List[tuple] = None, **kwargs):
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
        # Custom thumbnail as a local file (thumbnail_url takes a URL).
        thumbnail = kwargs.get("thumbnail")
        if thumbnail and files is not None:
            thumb_path = Path(str(thumbnail))
            if thumb_path.is_file():
                files.append(("thumbnail", (thumb_path.name, thumb_path.open("rb"))))
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
        # Translated title/description per language ({"es": {"title", "description"}})
        # and the brand partner channel id (UC...) for brand partner access.
        self._put(data, "youtube_localizations", kwargs.get("youtube_localizations"), "json")
        self._put(data, "youtube_brand_partner", kwargs.get("youtube_brand_partner"))
        playlist_value = kwargs.get("youtube_playlist_id")
        if playlist_value:
            if isinstance(playlist_value, (list, tuple)):
                playlist_value = ",".join(str(p).strip() for p in playlist_value if str(p).strip())
            if playlist_value:
                data.append(("youtube_playlist_id", str(playlist_value)))
        if kwargs.get("subtitles"):
            for idx, sub in enumerate(kwargs["subtitles"]):
                if sub.get("language"):
                    data.append((f"youtube_subtitle_language_{idx}", sub["language"]))
                    if sub.get("name"):
                        data.append((f"youtube_subtitle_name_{idx}", sub["name"]))
                    if sub.get("file"):
                        sub_path = Path(sub["file"])
                        if sub_path.exists() and files is not None:
                            files.append((f"youtube_subtitle_file_{idx}", (sub_path.name, sub_path.open("rb"))))
                        else:
                            # Treat as URL string
                            data.append((f"youtube_subtitle_file_{idx}", str(sub["file"])))
                    elif sub.get("url"):
                        data.append((f"youtube_subtitle_file_{idx}", sub["url"]))
        self._put_many(data, kwargs, (
            ("youtube_notify_subscribers", "bool"),
            ("youtube_publish_at", "str"),
        ))

    def _add_linkedin_params(
        self,
        data: List[tuple],
        is_text: bool = False,
        files: Optional[List[tuple]] = None,
        opened: Optional[List] = None,
        **kwargs,
    ):
        """Add LinkedIn-specific parameters."""
        visibility = (
            kwargs.get("visibility")
            or kwargs.get("linkedin_visibility")
            or kwargs.get("linkedinVisibility")
        )
        if visibility:
            data.append(("visibility", visibility))
        if kwargs.get("linkedin_visibility"):
            data.append(("linkedin_visibility", kwargs["linkedin_visibility"]))
        if kwargs.get("linkedinVisibility"):
            data.append(("linkedinVisibility", kwargs["linkedinVisibility"]))
        if kwargs.get("target_linkedin_page_id"):
            data.append(("target_linkedin_page_id", kwargs["target_linkedin_page_id"]))
        if is_text and (kwargs.get("linkedin_link_url") or kwargs.get("link_url")):
            link = kwargs.get("linkedin_link_url") or kwargs.get("link_url")
            data.append(("linkedin_link_url", link))
        self._put_many(data, kwargs, (
            ("linkedin_alt_text", "list"),
            ("linkedin_disable_reshare", "bool"),
            ("linkedin_link_title", "str"),
            ("linkedin_link_description", "str"),
            ("linkedin_thumbnail_alt_text", "str"),
            ("linkedin_target_geo_locations", "list"),
            ("linkedin_target_industries", "list"),
            ("linkedin_target_seniorities", "list"),
            ("linkedin_target_job_functions", "list"),
            ("linkedin_target_staff_count_ranges", "list"),
            ("linkedin_target_interface_locales", "list"),
            ("linkedin_target_degrees", "list"),
            ("linkedin_target_fields_of_study", "list"),
            ("linkedin_target_organizations", "list"),
            ("linkedin_target_entities", "json"),
            ("linkedin_target_check_audience", "bool"),
            ("linkedin_subtitles_url", "str"),
            ("linkedin_subtitles_text", "str"),
        ))
        self._put_file(data, files, opened, "linkedin_subtitles", kwargs.get("linkedin_subtitles"))

    def _add_facebook_params(self, data: List[tuple], is_video: bool = False, is_text: bool = False, **kwargs):
        """Add Facebook-specific parameters."""
        if kwargs.get("facebook_page_id"):
            data.append(("facebook_page_id", kwargs["facebook_page_id"]))

        # facebook_media_type (POSTS/STORIES/REELS) is honored for BOTH photos and video
        # (backend uploadphotos.py reads request.form.get('facebook_media_type')). Gating it
        # behind is_video prevented publishing Facebook Story photos from the SDK.
        if kwargs.get("facebook_media_type"):
            data.append(("facebook_media_type", kwargs["facebook_media_type"]))

        if is_video:
            if kwargs.get("video_state"):
                data.append(("video_state", kwargs["video_state"]))
            if kwargs.get("thumbnail_url"):
                data.append(("thumbnail_url", kwargs["thumbnail_url"]))

        if is_text and kwargs.get("facebook_link_url"):
            data.append(("facebook_link_url", kwargs["facebook_link_url"]))

        self._put_many(data, kwargs, (
            ("facebook_alt_text", "list"),
            ("facebook_place_id", "str"),
            ("facebook_targeting", "json"),
            ("facebook_feed_targeting", "json"),
            ("facebook_is_ai_generated", "bool"),
            ("facebook_collaborators", "list"),
            # Branded content tag: the sponsor's Facebook Page id (not on Reels/Stories).
            ("facebook_sponsor_id", "str"),
        ))
        if is_text:
            self._put_many(data, kwargs, (
                ("facebook_call_to_action", "json"),
                ("facebook_child_attachments", "json"),
                ("facebook_multi_share_end_card", "bool"),
            ))
        if is_video:
            self._put_many(data, kwargs, (
                ("facebook_unpublished_content_type", "str"),
                ("facebook_no_story", "bool"),
                ("facebook_secret", "bool"),
            ))

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

        self._put_many(data, kwargs, (
            ("pinterest_board_section_id", "str"),
            ("pinterest_ai_disclosures", "list"),
            ("pinterest_carousel_titles", "list"),
            ("pinterest_carousel_descriptions", "list"),
            ("pinterest_carousel_links", "list"),
            ("pinterest_carousel_index", "str"),
            ("pinterest_sponsor_id", "str"),
        ))

    def _add_x_params(
        self,
        data: List[tuple],
        is_text: bool = False,
        files: Optional[List[tuple]] = None,
        opened: Optional[List] = None,
        **kwargs,
    ):
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
        # Users who may not reply (with reply_to_id): a list, or comma-separated.
        self._put(data, "exclude_reply_user_ids", kwargs.get("exclude_reply_user_ids"), "list")
        
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

        self._put_many(data, kwargs, (
            ("x_alt_text", "list"),
            ("x_paid_partnership", "bool"),
            ("reply_to_id", "str"),
        ))
        if not is_text:
            self._put_many(data, kwargs, (
                ("x_subtitles", "str"),
                ("x_subtitles_url", "str"),
                ("x_subtitles_language", "str"),
                ("x_subtitles_name", "str"),
            ))
        else:
            self._put_many(data, kwargs, (
                ("x_article_title", "str"),
                ("x_article_body", "str"),
                ("x_article_content_state", "json"),
                ("x_article_draft", "bool"),
            ))
            self._put_file(
                data, files, opened, "x_article_cover_media",
                kwargs.get("x_article_cover_media"),
            )

    def _add_threads_params(self, data: List[tuple], is_text: bool = False, **kwargs):
        """Add Threads-specific parameters."""
        if kwargs.get("threads_long_text_as_post") is not None:
            data.append(("threads_long_text_as_post", str(kwargs["threads_long_text_as_post"]).lower()))
        if kwargs.get("threads_thread_media_layout"):
            data.append(("threads_thread_media_layout", kwargs["threads_thread_media_layout"]))
        if kwargs.get("threads_topic_tag"):
            data.append(("threads_topic_tag", kwargs["threads_topic_tag"]))
        self._put_many(data, kwargs, (
            ("threads_reply_control", "str"),
            ("threads_alt_text", "list"),
            ("threads_reply_to_id", "str"),
            ("threads_quote_post_id", "str"),
        ))
        if is_text:
            self._put_many(data, kwargs, (
                ("threads_link_attachment", "str"),
                ("threads_poll_options", "list"),
                ("threads_auto_publish_text", "bool"),
            ))

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
        self._put_many(data, kwargs, (
            ("reddit_nsfw", "bool"),
            ("nsfw", "bool"),
            ("reddit_spoiler", "bool"),
            ("spoiler", "bool"),
            ("reddit_resubmit", "bool"),
            ("reddit_send_replies", "bool"),
            ("reddit_flair_text", "str"),
            ("reddit_title", "str"),
            ("reddit_gallery_captions", "list"),
            ("reddit_gallery_urls", "list"),
        ))

    def _add_google_business_params(self, data: List[tuple], **kwargs):
        """Add Google Business Profile parameters.

        ``gbp_location_id`` is required for accounts with more than one location;
        the API only auto-selects when exactly one location exists.

        ``gbp_post_type`` switches the call from the default Local Post to a
        gallery photo upload (MEDIA / PHOTO / GALLERY). Any other value, or
        omitting it, keeps the Local Post behaviour.
        """
        if kwargs.get("gbp_location_id"):
            data.append(("gbp_location_id", kwargs["gbp_location_id"]))
        if kwargs.get("gbp_post_type"):
            data.append(("gbp_post_type", str(kwargs["gbp_post_type"]).upper()))
        if kwargs.get("gbp_media_category"):
            data.append(("gbp_media_category", str(kwargs["gbp_media_category"]).upper()))
        if kwargs.get("gbp_topic_type"):
            data.append(("gbp_topic_type", str(kwargs["gbp_topic_type"]).upper()))
        media_url = kwargs.get("gbp_media_url")
        if isinstance(media_url, (list, tuple)):
            # Several photos (with gbp_multi_media=True) go as gbp_media_url[].
            self._put(data, "gbp_media_url[]", list(media_url), "list")
        elif media_url:
            data.append(("gbp_media_url", media_url))
        if kwargs.get("gbp_media_format"):
            data.append(("gbp_media_format", str(kwargs["gbp_media_format"]).upper()))
        if kwargs.get("gbp_cta_type"):
            data.append(("gbp_cta_type", str(kwargs["gbp_cta_type"]).upper()))
        if kwargs.get("gbp_cta_url"):
            data.append(("gbp_cta_url", kwargs["gbp_cta_url"]))
        if kwargs.get("gbp_event_title"):
            data.append(("gbp_event_title", kwargs["gbp_event_title"]))
        if kwargs.get("gbp_event_start_date"):
            data.append(("gbp_event_start_date", kwargs["gbp_event_start_date"]))
        if kwargs.get("gbp_event_start_time"):
            data.append(("gbp_event_start_time", kwargs["gbp_event_start_time"]))
        if kwargs.get("gbp_event_end_date"):
            data.append(("gbp_event_end_date", kwargs["gbp_event_end_date"]))
        if kwargs.get("gbp_event_end_time"):
            data.append(("gbp_event_end_time", kwargs["gbp_event_end_time"]))
        if kwargs.get("gbp_offer_coupon"):
            data.append(("gbp_offer_coupon", kwargs["gbp_offer_coupon"]))
        if kwargs.get("gbp_offer_redeem_url"):
            data.append(("gbp_offer_redeem_url", kwargs["gbp_offer_redeem_url"]))
        if kwargs.get("gbp_offer_terms"):
            data.append(("gbp_offer_terms", kwargs["gbp_offer_terms"]))
        self._put_many(data, kwargs, (
            ("gbp_language_code", "str"),
            ("language_code", "str"),
            ("gbp_language", "str"),
            ("gbp_coupon_code", "str"),
            ("coupon_code", "str"),
            ("offer_coupon", "str"),
            ("gbp_redeem_url", "str"),
            ("gbp_terms", "str"),
            ("gbp_alert_type", "str"),
            ("gbp_upload_to_gallery", "bool"),
            ("gbp_multi_media", "bool"),
            ("gbp_recurrence", "str"),
            ("gbp_recurrence_days", "str"),
            ("gbp_recurrence_day_of_month", "str"),
            ("gbp_recurrence_week_occurrence", "str"),
            ("gbp_recurrence_end", "str"),
            ("gbp_scheduled_time", "str"),
        ))

    def _add_bluesky_params(self, data: List[tuple], **kwargs):
        """Add Bluesky-specific parameters."""
        self._put_many(data, kwargs, (
            ("bluesky_link_url", "str"),
            ("bluesky_alt_text", "list"),
            ("bluesky_alt_texts", "list"),
            ("bluesky_langs", "str"),
            ("bluesky_labels", "str"),
            ("bluesky_gallery", "bool"),
            ("bluesky_threadgate", "str"),
            ("bluesky_reply_settings", "str"),
            ("bluesky_postgate", "str"),
            ("bluesky_quote_settings", "str"),
            ("bluesky_quote_uri", "str"),
            ("bluesky_quote_id", "str"),
            ("bluesky_quote_url", "str"),
            ("bluesky_tags", "json"),
            ("bluesky_created_at", "str"),
            ("bluesky_thread_overflow", "bool"),
            ("bluesky_gif_as_video", "bool"),
            ("bluesky_captions", "json"),
            ("bluesky_video_presentation", "str"),
        ))

    def _add_discord_params(self, data: List[tuple], **kwargs):
        """Add Discord-specific parameters."""
        self._put_many(data, kwargs, (
            ("discord_thread_id", "str"),
            ("discord_thread_name", "str"),
            ("discord_applied_tags", "str"),
            ("discord_embeds", "json"),
            ("discord_username", "str"),
            ("discord_avatar_url", "str"),
            ("discord_allowed_mentions", "json"),
            ("discord_alt_text", "str"),
            ("discord_flags", "str"),
            ("discord_tts", "bool"),
            ("discord_poll", "json"),
            ("discord_max_file_mb", "str"),
        ))

    def _add_telegram_params(
        self,
        data: List[tuple],
        files: Optional[List[tuple]] = None,
        opened: Optional[List] = None,
        **kwargs,
    ):
        """Add Telegram-specific parameters.

        JSON objects keep Telegram's own shape (ReplyParameters,
        LinkPreviewOptions, MessageEntity, InputPollOption...).
        """
        # A dice: an emoji, or True for the default one.
        dice = kwargs.get("telegram_dice")
        self._put(data, "telegram_dice", str(dice).lower() if isinstance(dice, bool) else dice)
        # Files (local path) or URLs / file_ids.
        for key in ("telegram_cover", "telegram_thumbnail", "telegram_live_photo_photo"):
            self._put_file(data, files, opened, key, kwargs.get(key))
        self._put_many(data, kwargs, (
            ("telegram_parse_mode", "str"),
            ("telegram_message_thread_id", "str"),
            ("telegram_disable_notification", "bool"),
            ("telegram_protect_content", "bool"),
            ("telegram_has_spoiler", "bool"),
            ("telegram_link_preview", "bool"),
            ("telegram_reply_markup", "json"),
            ("telegram_caption_overflow", "str"),
            ("telegram_as_document", "bool"),
            ("telegram_media_urls", "str"),
            ("telegram_pin", "bool"),
            ("telegram_pin_notify", "bool"),
            ("telegram_poll", "json"),
            ("telegram_location", "json"),
            ("telegram_venue", "json"),
            ("telegram_contact", "json"),
            ("telegram_game_short_name", "str"),
            ("telegram_rich_message", "json"),
            ("telegram_reply_to_message_id", "str"),
            ("telegram_reply_quote", "str"),
            ("telegram_reply_parameters", "json"),
            ("telegram_link_preview_options", "json"),
            ("telegram_entities", "json"),
            ("telegram_caption_entities", "json"),
            ("telegram_show_caption_above_media", "bool"),
            ("telegram_first_comment_as_reply", "bool"),
            ("telegram_direct_messages_topic_id", "str"),
            ("telegram_suggested_post_parameters", "json"),
            ("telegram_ephemeral_message_parameters", "json"),
            ("telegram_message_effect_id", "str"),
            ("telegram_send_by_url", "bool"),
            ("telegram_send_as", "str"),
            ("telegram_paid_star_count", "str"),
            ("telegram_paid_payload", "str"),
            ("telegram_start_timestamp", "str"),
            ("telegram_disable_content_type_detection", "bool"),
            ("telegram_performer", "str"),
            ("telegram_title_audio", "str"),
            ("telegram_duration", "str"),
            ("telegram_length", "str"),
            ("telegram_emoji", "str"),
            ("telegram_allow_paid_broadcast", "bool"),
            ("telegram_send_title", "bool"),
        ))

    def _add_mastodon_params(self, data: List[tuple], **kwargs):
        """Add Mastodon-specific parameters."""
        self._put_many(data, kwargs, (
            ("mastodon_visibility", "str"),
            ("mastodon_sensitive", "bool"),
            ("mastodon_spoiler_text", "str"),
            ("mastodon_language", "str"),
            ("mastodon_alt_text", "str"),
            ("mastodon_poll_options", "str"),
            ("mastodon_poll_expires_in", "str"),
            ("mastodon_poll_multiple", "bool"),
            ("mastodon_scheduled_at", "str"),
        ))

    def _add_wordpress_params(self, data: List[tuple], **kwargs):
        """Add WordPress-specific parameters."""
        self._put_many(data, kwargs, (
            ("wordpress_status", "str"),
            ("wordpress_date", "str"),
            ("wordpress_categories", "str"),
            ("wordpress_tags", "str"),
            ("wordpress_excerpt", "str"),
            ("wordpress_slug", "str"),
            ("wordpress_alt_text", "str"),
            ("wordpress_media_caption", "str"),
            ("wordpress_block_format", "bool"),
        ))

    def _add_lemmy_params(self, data: List[tuple], **kwargs):
        """Add Lemmy-specific parameters."""
        self._put_many(data, kwargs, (
            ("lemmy_url", "str"),
            ("lemmy_community", "str"),
            ("lemmy_nsfw", "bool"),
            ("lemmy_language_id", "str"),
            ("lemmy_alt_text", "str"),
        ))

    def _add_slack_params(self, data: List[tuple], **kwargs):
        """Add Slack-specific parameters."""
        self._put_many(data, kwargs, (
            ("slack_markdown", "bool"),
            ("slack_blocks", "json"),
            ("slack_mrkdwn", "bool"),
            ("slack_alt_text", "str"),
            ("slack_first_comment_mode", "str"),
        ))

    def _add_nostr_params(self, data: List[tuple], **kwargs):
        """Add Nostr-specific parameters."""
        self._put_many(data, kwargs, (
            ("nostr_kind", "str"),
            ("nostr_long_form", "bool"),
        ))

    def _add_devto_params(self, data: List[tuple], **kwargs):
        """Add Dev.to-specific parameters."""
        self._put_many(data, kwargs, (
            ("devto_tags", "str"),
            ("devto_canonical_url", "str"),
            ("devto_description", "str"),
            ("devto_main_image", "str"),
            ("devto_series", "str"),
            ("devto_published", "bool"),
        ))

    def _add_hashnode_params(self, data: List[tuple], **kwargs):
        """Add Hashnode-specific parameters."""
        self._put_many(data, kwargs, (
            ("hashnode_tags", "str"),
            ("hashnode_original_article_url", "str"),
            ("hashnode_subtitle", "str"),
            ("hashnode_cover_image_url", "str"),
            ("hashnode_draft", "bool"),
            ("hashnode_body", "str"),
            ("content", "str"),
        ))

    def _add_whop_params(self, data: List[tuple], **kwargs):
        """Add Whop-specific parameters."""
        self._put_many(data, kwargs, (
            ("whop_body", "str"),
            ("whop_pinned", "bool"),
            ("whop_is_mention", "bool"),
            ("whop_paywall_amount", "str"),
            ("whop_paywall_currency", "str"),
            ("whop_attachment_ids", "str"),
        ))

    def _add_listmonk_params(self, data: List[tuple], **kwargs):
        """Add Listmonk-specific parameters."""
        self._put_many(data, kwargs, (
            ("listmonk_content_type", "str"),
            ("listmonk_send_at", "str"),
            ("listmonk_lists", "str"),
            ("listmonk_template_id", "str"),
            ("listmonk_media_ids", "str"),
        ))

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
                   Optional for TikTok, Instagram, Facebook, LinkedIn, X, Threads, Bluesky, Discord, Telegram, Pinterest.
            user: User identifier (profile name).
            platforms: Target platforms. Supported: tiktok, instagram, youtube,
                      linkedin, facebook, pinterest, threads, bluesky, discord, telegram, x,
                      google_business, mastodon, wordpress

        Keyword Args:
            description: Video description
            first_comment: First comment to post
            scheduled_date: ISO date for scheduling (e.g., "2024-12-25T10:00:00Z")
            timezone: Timezone for scheduled date (e.g., "Europe/Madrid")
            add_to_queue: Add to posting queue
            async_upload: Process asynchronously (default: True)
                          title/description from the media and fills any platform field
                          the language (omit to auto-detect from the media).
            
            TikTok:
                privacy_level: PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS,
                              FOLLOWER_OF_CREATOR, SELF_ONLY. TikTok decides
                              per account which of these are available (a
                              private account has no PUBLIC_TO_EVERYONE);
                              asking for another one fails with
                              error_code="tiktok_privacy_unavailable" listing
                              the allowed ones. Omit it to keep the account's
                              own default.
                disable_duet: Disable duet
                disable_comment: Disable comments
                disable_stitch: Disable stitch
                cover_timestamp: Timestamp in ms for cover
                is_aigc: AI-generated content flag
                post_mode: DIRECT_POST or MEDIA_UPLOAD. MEDIA_UPLOAD is the
                    same draft as tiktok_upload_to_draft=True.
                brand_content_toggle: Branded content toggle
                brand_organic_toggle: Brand organic toggle
                tiktok_is_ads_only: Only show the video in ads
                tiktok_tto_invite_link: TikTok One invite link (needs branded content)

            TikTok music, location, cover and draft options. Available on
            connections that declare the matching capability (`music`,
            `location`, `cover_image`, `draft`) - see `capabilities` on the
            TikTok account returned by list_users(). If your connection does
            not have it, the field is ignored, the post still publishes, and
            the response includes a per-field `warnings` entry; reconnect the
            TikTok account to enable it.
                tiktok_music_id: Commercial Music Library track id
                                 (see get_tiktok_trending_music)
                tiktok_music_volume: Music volume 0-100 (defaults to 50 when
                                     music is set)
                tiktok_music_start: Music start offset in ms
                tiktok_music_end: Music end offset in ms
                tiktok_original_sound_volume: Original audio volume 0-100
                                              (defaults to 50 when music is set,
                                              so the original audio is not muted)
                tiktok_location_id: Location id (see get_tiktok_locations)
                tiktok_location_name: Location name, required together with the id
                tiktok_cover_image_url: Custom cover image URL
                tiktok_is_ai_generated: AI-generated content disclosure
                tiktok_upload_to_draft: Publish to drafts (alias of
                    post_mode="MEDIA_UPLOAD"; also upload_to_draft / is_draft).
                    When True TikTok ignores the rest of the post settings.

            Instagram:
                media_type: REELS or STORIES
                share_to_feed: Share to feed
                collaborators: Comma-separated collaborator usernames
                cover_url: Custom cover URL or file path. URLs are sent directly; file paths are uploaded as binary.
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
                youtube_playlist_id: Playlist ID (or list/comma-separated of IDs) to add
                    the uploaded video to after publishing
                subtitles: List of subtitle dicts with keys: language (BCP-47),
                    name (display name), file (path to SRT/VTT file), url (subtitle URL)

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
                threads_topic_tag: Topic tag for the post (1-50 chars, no periods or ampersands)

            Google Business:
                gbp_location_id: Location, e.g. "accounts/123/locations/456". Required
                    when the account has more than one location.
                gbp_post_type: MEDIA, PHOTO or GALLERY to publish into the location's
                    gallery instead of creating a Local Post. Any other value, or
                    omitting it, keeps the Local Post behaviour.
                gbp_media_category: Gallery category (default ADDITIONAL). One of
                    COVER, PROFILE, LOGO, EXTERIOR, INTERIOR, PRODUCT, AT_WORK,
                    FOOD_AND_DRINK, MENU, COMMON_AREA, ROOMS, TEAMS, ADDITIONAL.
                gbp_topic_type: STANDARD, EVENT or OFFER
                gbp_media_url / gbp_media_format: Media attached to the post
                gbp_cta_type / gbp_cta_url: Call-to-action button
                gbp_event_title / gbp_event_start_date / gbp_event_start_time /
                    gbp_event_end_date / gbp_event_end_time: Used with EVENT
                gbp_offer_coupon / gbp_offer_redeem_url / gbp_offer_terms: Used with OFFER

        Returns:
            API response with request_id for async uploads.
            Team roles and post approvals (not generally available yet): for an
            Editor or Contributor team member the post is not published; the
            answer (HTTP 202) has ``pending_approval: True``, ``approval_id``,
            ``approval_status`` ("pending_approval" or "draft") and ``job_id: None``.

        Raises:
            UploadPostError: If upload fails or video file not found.
        """
        data: List[tuple] = []
        files: List[tuple] = []
        video_file = None
        opened_files: List = []
        
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
            self._add_all_platform_params(
                data, platforms, is_video=True, is_text=False,
                files=files, opened=opened_files, **kwargs,
            )

            # Images for the first comment (Reddit), as on photos and text posts.
            self._add_first_comment_media(files, opened_files, kwargs.get("first_comment_media"))

            return self._request("/upload", "POST", data=data, files=files if files else None)
            
        finally:
            if video_file:
                video_file.close()
            for f in opened_files:
                f.close()

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
                   Optional for TikTok, Instagram, Facebook, LinkedIn, X, Threads, Bluesky, Discord, Telegram, Pinterest.
            user: User identifier (profile name).
            platforms: Target platforms. Supported: tiktok, instagram, linkedin,
                      facebook, pinterest, threads, reddit, bluesky, discord, telegram, x,
                      google_business, mastodon, lemmy, wordpress

        Keyword Args:
            description: Photo description
            first_comment: First comment to post
            alt_text: Alt text for accessibility
            scheduled_date: ISO date for scheduling
            timezone: Timezone for scheduled date
            add_to_queue: Add to posting queue
            async_upload: Process asynchronously
            
            TikTok:
                privacy_level: PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS,
                              FOLLOWER_OF_CREATOR, SELF_ONLY. TikTok requires
                              one on photo posts, so it defaults to
                              PUBLIC_TO_EVERYONE. Which values the account may
                              use is decided by TikTok (a private account has
                              no PUBLIC_TO_EVERYONE). Available on connections
                              that declare the `photo_privacy` capability - see
                              `capabilities` on the TikTok account returned by
                              list_users().
                post_mode: DIRECT_POST or MEDIA_UPLOAD. MEDIA_UPLOAD is the
                    same draft as tiktok_upload_to_draft=True.
                auto_add_music: Auto add music
                disable_comment: Disable comments
                photo_cover_index: Index of photo for cover (0-based)
                tiktok_music_id: Commercial Music Library track id
                                 (see get_tiktok_trending_music). TikTok's photo
                                 contract takes the id alone - the volume, trim
                                 and cover-image fields are video-only.
                tiktok_location_id / tiktok_location_name: Location tag, both
                                 required together.
                tiktok_is_ai_generated: AI-generated content disclosure.
                tiktok_upload_to_draft: Same draft as post_mode="MEDIA_UPLOAD".
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
                threads_topic_tag: Topic tag for the post (1-50 chars, no periods or ampersands)

            Reddit:
                subreddit: Subreddit name (without r/)
                flair_id: Flair template ID
                reddit_nsfw / reddit_spoiler / reddit_resubmit / reddit_send_replies
                reddit_flair_text / reddit_gallery_captions / reddit_gallery_urls
                Uploads currently return error_code=reddit_unavailable until
                the Reddit app is restored.

            Google Business:
                gbp_location_id: Location, e.g. "accounts/123/locations/456". Required
                    when the account has more than one location.
                gbp_post_type: MEDIA, PHOTO or GALLERY to publish the photo into the
                    location's gallery instead of creating a Local Post. Any other
                    value, or omitting it, keeps the Local Post behaviour.
                gbp_media_category: Gallery category (default ADDITIONAL). One of
                    COVER, PROFILE, LOGO, EXTERIOR, INTERIOR, PRODUCT, AT_WORK,
                    FOOD_AND_DRINK, MENU, COMMON_AREA, ROOMS, TEAMS, ADDITIONAL.
                gbp_topic_type: STANDARD, EVENT or OFFER
                gbp_cta_type / gbp_cta_url: Call-to-action button

            first_comment_media: Local paths, bytes or URLs (downloaded and sent as
                files) of images to attach in
                the first comment. Supported on Reddit and X.

        Returns:
            API response.
            Team roles and post approvals (not generally available yet): for an
            Editor or Contributor team member the post is not published; the
            answer (HTTP 202) has ``pending_approval: True``, ``approval_id``,
            ``approval_status`` ("pending_approval" or "draft") and ``job_id: None``.

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
            self._add_all_platform_params(
                data, platforms, is_video=False, is_text=False,
                files=files, opened=opened_files, **kwargs,
            )

            self._add_first_comment_media(files, opened_files, kwargs.get("first_comment_media"))

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
                      threads, reddit, bluesky, discord, telegram, google_business,
                      slack, mastodon, nostr, lemmy, devto, hashnode, wordpress,
                      whop, listmonk

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
                threads_topic_tag: Topic tag for the post (1-50 chars, no periods or ampersands)

            Reddit:
                subreddit: Subreddit name (without r/)
                flair_id: Flair template ID
                reddit_link_url: URL for link post. Creates a Reddit link post
                    (kind: "link") instead of a text post. Overrides `link_url`
                    for Reddit.
                reddit_nsfw / reddit_spoiler / reddit_resubmit / reddit_send_replies
                reddit_flair_text / reddit_gallery_captions / reddit_gallery_urls
                Uploads currently return error_code=reddit_unavailable until
                the Reddit app is restored.

            Google Business:
                gbp_location_id: Location, e.g. "accounts/123/locations/456". Required
                    when the account has more than one location.
                gbp_topic_type: STANDARD, EVENT or OFFER
                gbp_cta_type / gbp_cta_url: Call-to-action button
                gbp_event_title / gbp_event_start_date / gbp_event_start_time /
                    gbp_event_end_date / gbp_event_end_time: Used with EVENT
                gbp_offer_coupon / gbp_offer_redeem_url / gbp_offer_terms: Used with OFFER

            first_comment_media: Local paths, bytes or URLs (downloaded and sent as
                files) of images to attach in
                the first comment. Supported on Reddit and X.

        Returns:
            API response.
            Team roles and post approvals (not generally available yet): for an
            Editor or Contributor team member the post is not published; the
            answer (HTTP 202) has ``pending_approval: True``, ``approval_id``,
            ``approval_status`` ("pending_approval" or "draft") and ``job_id: None``.

        Raises:
            UploadPostError: If upload fails.
        """
        data: List[tuple] = []
        files: List[tuple] = []
        opened_files: List = []

        self._add_common_params(data, user, title, platforms, **kwargs)

        # Generic link_url support
        if kwargs.get("link_url"):
            data.append(("link_url", kwargs["link_url"]))

        self._add_all_platform_params(
            data, platforms, is_video=False, is_text=True,
            files=files, opened=opened_files, **kwargs,
        )

        self._add_first_comment_media(files, opened_files, kwargs.get("first_comment_media"))

        try:
            return self._request("/upload_text", "POST", data=data, files=files if files else None)
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
        **kwargs,
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
            **kwargs: Extra LinkedIn form fields (linkedin_disable_reshare,
                linkedin_visibility, targeting, …). ``platforms=["telegram"]``
                (or ``["linkedin", "telegram"]``) sends the file to Telegram as
                well, with the ``telegram_*`` fields of upload_video.

        Returns:
            API response.
            Team roles and post approvals (not generally available yet): for an
            Editor or Contributor team member the post is not published; the
            answer (HTTP 202) has ``pending_approval: True``, ``approval_id``,
            ``approval_status`` ("pending_approval" or "draft") and ``job_id: None``.

        Raises:
            UploadPostError: If upload fails or document file not found.
        """
        data: List[tuple] = []
        files: List[tuple] = []
        doc_file = None
        opened_files: List = []
        
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
            # LinkedIn by default; platforms=["telegram"] (or both) sends the file
            # to Telegram too. Other platforms do not take documents.
            doc_platforms = [p for p in (kwargs.get("platforms") or []) if p in ("linkedin", "telegram")]
            for platform in doc_platforms or ["linkedin"]:
                data.append(("platform[]", platform))
            
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
            self._add_linkedin_params(
                data, files=files, opened=opened_files, **kwargs
            )
            if "telegram" in doc_platforms:
                self._add_telegram_params(data, files=files, opened=opened_files, **kwargs)
                self._put(data, "telegram_first_comment", kwargs.get("telegram_first_comment"))
            
            return self._request("/upload_document", "POST", data=data, files=files if files else None)
            
        finally:
            if doc_file:
                doc_file.close()
            for f in opened_files:
                f.close()

    # ==================== Status & History ====================

    def get_status(self, request_id: str) -> Dict:
        """
        Get the status of an async upload by request ID.

        Args:
            request_id: The request_id from an async upload.

        Returns:
            Upload status.
        """
        return self._request("/uploadposts/status", "GET", params={"request_id": request_id})

    def get_job_status(self, job_id: str) -> Dict:
        """
        Get the status of a scheduled or queued upload by job ID.

        Args:
            job_id: The job_id from a scheduled or queued upload.

        Returns:
            Upload status.
        """
        return self._request("/uploadposts/status", "GET", params={"job_id": job_id})

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

    def retry_post(
        self,
        request_id: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> Dict:
        """
        Retry a failed post.

        Args:
            request_id: Request ID of the post to retry.
            job_id: Job ID of the post to retry.

        One of request_id or job_id is required.

        Returns:
            Retry result.
        """
        json_data = {}
        if request_id is not None:
            json_data["request_id"] = request_id
        if job_id is not None:
            json_data["job_id"] = job_id
        return self._request("/uploadposts/posts/retry", "POST", json_data=json_data)

    def unpublish_post(
        self,
        user: str,
        platform: str,
        post_id: str,
        **params,
    ) -> Dict:
        """
        Unpublish (delete) a previously published post.

        Instagram posts cannot be deleted through Upload-Post: Meta only allows
        it through the Instagram API with Facebook Login, and Upload-Post
        connects Instagram with Instagram Login, so the API answers 400. TikTok
        has no delete API, and Threads answers 400 ``platform_not_supported``.

        Args:
            user: Profile username.
            platform: Platform name (facebook, youtube, x, linkedin, pinterest,
                bluesky, google_business...).
            post_id: ID of the published post to unpublish. Bluesky: the
                ``at://`` URI or a bsky.app URL.
            **params: Other API fields, e.g. ``delete_all_messages=True``
                (Telegram: delete every message of the post, not only
                ``post_id``).

        Returns:
            Unpublish result.
        """
        body = {k: v for k, v in params.items() if v is not None}
        body.update({"user": user, "platform": platform, "post_id": post_id})
        return self._request("/uploadposts/posts/unpublish", "POST", json_data=body)

    def get_analytics(self, profile_username: str, platforms: Optional[List[str]] = None,
                      page_id: Optional[str] = None, page_urn: Optional[str] = None) -> Dict:
        """
        Get analytics for a profile.

        Args:
            profile_username: Profile username.
            platforms: Filter by platforms (instagram, linkedin, facebook, x, youtube, tiktok, threads, pinterest, reddit).
            page_id: Facebook Page ID (required for Facebook analytics).
            page_urn: LinkedIn organization/company page URN or numeric ID. LinkedIn
                analytics are only available for pages you administer; personal profiles
                are not supported (LinkedIn's API exposes no member-level analytics). If
                omitted, the first administered organization page is used.

        Returns:
            Analytics data per platform. For Instagram, the response includes both
            'views' (official Instagram metric) and 'impressions' (backwards-compatible alias),
            plus two audience breakdowns with the same shape ('age', 'gender',
            'country', 'city'): 'follower_demographics' for the account's followers
            and 'engaged_audience_demographics' for the accounts that engaged with
            its content.
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
            metrics: Specific metrics to aggregate (e.g., ["likes", "comments", "shares", "views"]).

        Returns:
            Total impressions data with optional breakdown. For Instagram, uses 'reach' as the primary metric.
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

    def get_post_analytics(self, request_id: str, platform: Optional[str] = None) -> Dict:
        """
        Get analytics for a specific post across all platforms it was published to.

        'post_metrics' carries whatever the platform reports, so it is not the
        same shape everywhere: on TikTok it also brings 'retention' (the curve,
        second by second), 'impression_sources' (For You, search, profile...),
        'audience_types' (followers vs non-followers), 'new_followers', 'reach'
        and the watch times ('average_time_watched', 'total_time_watched',
        'full_video_watched_rate').

        TikTok drafts (``post_mode="MEDIA_UPLOAD"`` / ``tiktok_upload_to_draft``)
        have no post until the creator publishes them from the TikTok app.
        Call this again after that: Upload-Post asks TikTok which post came
        from the draft and fills in ``platform_post_id`` and ``post_url``.
        While the draft is still in the inbox, ``post_metrics_error`` says so
        (that answer is reused for a while, from ~5 minutes for a fresh upload
        up to 6 hours); after 30 days without a post it stops asking. TikTok
        only gives the post id once the post is public and moderated, so a
        draft published as private never gets per-post analytics. TikTok rows
        also carry ``original_publish_id`` (the upload's TikTok ``publish_id``),
        and ``post_url`` is empty when the account's @username is not known.

        Args:
            request_id: The request_id from the upload.
            platform: Only this platform's row (e.g. ``"tiktok"``).

        Returns:
            Post analytics with per-platform metrics, profile snapshots, and post-level metrics.
        """
        params = {"platform": platform} if platform else None
        return self._request(f"/uploadposts/post-analytics/{request_id}", "GET", params=params)

    def get_post_analytics_by_platform_id(self, platform_post_id: str, platform: str, user: str) -> Dict:
        """
        Get analytics for any post (including organic posts) using its native platform ID.

        Args:
            platform_post_id: The native post ID on the platform (e.g., Instagram media ID).
            platform: The platform to query (instagram, youtube, tiktok, facebook, linkedin, x, threads, pinterest, reddit).
            user: The profile_username that owns the social account.

        Returns:
            Post analytics with live per-post metrics from the platform API.
        """
        params = {
            "platform_post_id": platform_post_id,
            "platform": platform,
            "user": user,
        }
        return self._request("/uploadposts/post-analytics", "GET", params=params)

    def get_cached_post_analytics(
        self,
        user: str,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Dict:
        """
        Replay per-post metrics already fetched, instead of querying
        the platforms live.

        Because it never calls the platform APIs it is not subject to the live
        post-analytics rate limit (100 requests / 5 minutes), which makes it the
        right method for paging through a profile's whole post history.

        Args:
            user: Profile username.
            platform: Filter by platform (instagram, tiktok, youtube, facebook,
                linkedin, threads, pinterest, reddit).
            limit: Posts per page. Defaults to 50, max 200.
            cursor: Opaque cursor from a previous response's ``next_cursor``.
            since: Start date in YYYY-MM-DD format (defaults to 30 days ago).
            until: End date in YYYY-MM-DD format (defaults to today).

        Returns:
            Cached post metrics with ``source: "snapshot_cache"``, plus
            ``next_cursor`` and ``has_more`` for pagination. A TikTok draft
            appears once, under its real post id, with ``original_publish_id``.
        """
        params: Dict[str, Any] = {"user": user}
        if platform:
            params["platform"] = platform
        if limit is not None:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        return self._request("/uploadposts/post-analytics/cached", "GET", params=params)

    def get_audience(
        self,
        user: str,
        platform: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        benchmark_category: Optional[str] = None
    ) -> Dict:
        """
        Get who the audience is: where they are, how old they are, when they
        are online and what they tap on the profile.

        Where the post-analytics methods answer how did my posts do, this one
        answers who is following me. It is one endpoint for every platform,
        chosen with `platform`; a platform that cannot answer it comes back
        with "platform_not_supported" and the list of the ones that can.

        The window is clamped server-side: at most 60 days, and end_date always
        before today. A wider window is trimmed rather than rejected.

        Args:
            user: Profile username.
            platform: Platform to ask (tiktok).
            start_date: Window start, ISO "YYYY-MM-DD".
            end_date: Window end, ISO "YYYY-MM-DD".
            benchmark_category: Compare the account against this category's
                averages, e.g. "SOFTWARE_AND_APPS". Every accepted value comes
                back in "benchmark_categories" on any response, so a picker
                needs no second call.

        Returns:
            'range', 'audience' (countries, cities, ages, genders),
            'activity_by_hour', 'followers_daily', 'profile_actions',
            'bio_description', 'benchmark_categories' and, with a category,
            'benchmark'.
        """
        params: Dict[str, Any] = {"user": user, "platform": platform}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if benchmark_category:
            params["benchmark_category"] = benchmark_category
        return self._request("/uploadposts/audience", "GET", params=params)

    def get_suggestions(
        self,
        user: str,
        platform: str,
        type: str,
        q: Optional[str] = None,
        country_code: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict:
        """
        Get what to write about: the hashtags or the searches a platform
        suggests around a keyword.

        One endpoint for both questions, told apart by `type`:

            type        answers
            hashtags    {"hashtags": [{"name": ..., "view_count": ...}]}
            keywords    {"keywords": [...]}

        Chosen with `platform`, like every other question in the API; a
        platform that cannot answer it comes back with
        "platform_not_supported" and the list of the ones that can.

        Args:
            user: Profile username.
            platform: Platform to ask (tiktok).
            type: Which suggestions you want: "hashtags" or "keywords".
            q: Keyword to get suggestions around.
            country_code: ISO country code to bias the suggestions.
            language: Language code to bias the suggestions.

        Returns:
            {"success": True, "platform": ..., "type": ..., "hashtags": [...]}
            or {"success": True, "platform": ..., "type": ..., "keywords": [...]}
        """
        params: Dict[str, Any] = {"user": user, "platform": platform, "type": type}
        if q:
            params["q"] = q
        if country_code:
            params["country_code"] = country_code
        if language:
            params["language"] = language
        return self._request("/uploadposts/suggestions", "GET", params=params)

    def get_platform_metrics(self) -> Dict:
        """
        Get available metrics configuration for all supported platforms.

        Returns:
            Platform metrics config with primary fields, available metrics, and labels.
        """
        return self._request("/uploadposts/platform-metrics", "GET")

    def get_media(
        self,
        platform: str,
        user: str,
        page_urn: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict:
        """
        Retrieve recent media from a connected social account.

        Instagram leaves ``media_url`` out of videos, reels and video stories
        with copyrighted or licensed audio (Instagram's audio library included),
        even on your own media: fall back to ``permalink`` or ``thumbnail_url``.

        Args:
            platform: instagram, tiktok, youtube, linkedin, facebook, x,
                threads, pinterest, bluesky, or reddit.
            user: Profile username.
            page_urn: LinkedIn only. Numeric org ID, full URN, or ``"me"`` to
                force the personal profile of an org-admin account.
            limit: Items per page. Defaults to 25 and is clamped to 1-100.
                Per-platform caps: TikTok 20, YouTube 50, everything else 100.
            cursor: Opaque cursor from a previous response's
                ``pagination["next_cursor"]``. LinkedIn, Discord and Telegram do
                not support cursors: passing one there returns HTTP 400.

        Returns:
            ``{"success": True, "media": [...], "pagination": {"limit": 50,
            "next_cursor": "QVFI...", "has_more": True}}``. The last page has
            ``next_cursor`` ``None`` and ``has_more`` ``False``.
        """
        params: Dict[str, Any] = {"platform": platform, "user": user}
        if page_urn:
            params["page_urn"] = page_urn
        if limit is not None:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        return self._request("/uploadposts/media", "GET", params=params)

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
        timezone: Optional[str] = None,
        *,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        description: Optional[str] = None,
        platform_content: Optional[Dict[str, Dict[str, str]]] = None,
        fields: Optional[Dict[str, Any]] = None,
        youtube_publish_at: Optional[str] = None,
        cover_image_base64: Optional[str] = None,
        cover_filename: Optional[str] = None,
        cover_content_type: Optional[str] = None,
        remove_cover: bool = False,
    ) -> Dict:
        """
        Edit a scheduled post (``PATCH /api/uploadposts/schedule/<job_id>``).

        Every argument is optional; only what you pass is changed. The media,
        profile and platforms of a scheduled post cannot be edited.

        Args:
            job_id: Scheduled job ID.
            scheduled_date: New scheduled date (ISO 8601), future and within 1 year.
            timezone: IANA timezone ``scheduled_date`` is read in (default UTC).
            title: New title for every platform of the post.
            caption: New caption/description for every platform of the post.
            description: Alias of ``caption`` (``caption`` wins if both are given).
            platform_content: Per-platform text, e.g.
                ``{"instagram": {"caption": "..."}, "youtube": {"title": "..."}}``.
                Only the platforms listed are touched.
            fields: Any other editable upload option, keyed by its API form name
                (``privacyStatus``, ``tags``, ``disable_comment``,
                ``instagram_first_comment``, ``gbp_cta_url``...). ``None`` as a
                value removes that option; unknown or internal keys are ignored.
            youtube_publish_at: Native YouTube scheduling (RFC3339), sent as
                ``fields["youtube_publish_at"]``; wins over the same key in
                ``fields``. To remove it pass ``fields={"youtube_publish_at": None}``.
            cover_image_base64: New cover image (Instagram / Facebook Reels) as
                base64 or a data URL.
            cover_filename: File name of the new cover (default ``cover.jpg``).
            cover_content_type: MIME type of the new cover (default ``image/jpeg``).
            remove_cover: Remove the custom cover (ignores ``cover_image_base64``).

        Returns:
            Edit result (``success``, ``job_id``, and the new ``scheduled_date``,
            ``title``, ``caption``, ``platform_content`` when they changed).
        """
        body: Dict[str, Any] = {}
        if scheduled_date:
            body["scheduled_date"] = scheduled_date
        if timezone:
            body["timezone"] = timezone
        if title is not None:
            body["title"] = title
        if caption is not None:
            body["caption"] = caption
        elif description is not None:
            body["description"] = description
        if platform_content:
            body["platform_content"] = platform_content
        edited_fields = dict(fields or {})
        if youtube_publish_at is not None:
            edited_fields["youtube_publish_at"] = youtube_publish_at
        if edited_fields:
            body["fields"] = edited_fields
        if remove_cover:
            body["remove_cover"] = True
        elif cover_image_base64:
            body["cover_image_base64"] = cover_image_base64
            if cover_filename:
                body["cover_filename"] = cover_filename
            if cover_content_type:
                body["cover_content_type"] = cover_content_type
        return self._request(f"/uploadposts/schedule/{job_id}", "PATCH", json_data=body)

    # ==================== User Management ====================

    def list_users(self) -> Dict:
        """
        List all users/profiles.

        The TikTok account object carries a `capabilities` array with the
        values the connection supports: `music`, `location`, `cover_image`,
        `cover_timestamp`, `draft`, `photo_privacy`, `video_privacy`,
        `inbox_fallback` and `profile_analytics`. Fields whose
        capability is missing are ignored on upload (the post still publishes)
        and reported as plain strings in the response `warnings`.

        Returns:
            List of users.
        """
        return self._request("/uploadposts/users", "GET")

    def create_user(self, username: str) -> Dict:
        """
        Create a new user/profile.

        A username that already exists fails with 409 ("Username already in
        use"); the profile limit of the plan with 403 ``PROFILE_LIMIT_REACHED``.

        Args:
            username: Profile name to create.

        Returns:
            ``{"success": True, "profile": {...}}``.
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
        connect_description: Optional[str] = None,
        language: Optional[str] = None,
        ui_labels: Optional[Dict[str, str]] = None,
        client_approval: Optional[bool] = None,
        connect_theme: Optional[str] = None,
        preserve_settings: Optional[bool] = None
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
            language: Force the connection page language for this profile.
                Supported: 'en', 'es', 'de', 'fr', 'pt', 'pl', 'tr'. When omitted,
                the page auto-detects the visitor's browser language and falls back
                to English.
            ui_labels: Flat mapping of i18n dot-path keys to replacement strings,
                e.g. {"connect.title": "Link your accounts"}. Max 100 entries; keys
                must match ^[a-zA-Z0-9_.]+$ and values are strings of up to 300
                characters. Echoed back in the 'profile' object of validate_jwt.
            client_approval: Not generally available yet (post approvals). True
                lets the end client approve or reject the pending posts of this
                profile from the connect page (``list_client_post_approvals``,
                ``approve_client_post_approval``, ``reject_client_post_approval``
                with this JWT). Stored on the profile; generate again with False
                to turn it off.
            connect_theme: Force the connection page theme: 'light', 'dark', or
                'auto' to follow the visitor's preference again.
            preserve_settings: True mints the link without changing the
                profile's saved settings (by default every setting not sent
                here is cleared). ``platforms`` then applies to this link
                only. Cannot be combined with the other settings, which are
                stored on the profile (400 ``preserve_settings_conflict``).

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
        if language:
            body["language"] = language
        if ui_labels:
            body["ui_labels"] = ui_labels
        if client_approval is not None:
            body["client_approval"] = client_approval
        if connect_theme is not None:
            body["connect_theme"] = connect_theme
        if preserve_settings is not None:
            body["preserve_settings"] = preserve_settings
        return self._request("/uploadposts/users/generate-jwt", "POST", json_data=body)

    def validate_jwt(self, jwt: str) -> Dict:
        """
        Validate a JWT token.

        Args:
            jwt: JWT token to validate.

        Returns:
            Validation result. The 'profile' object echoes back the connection
            page settings, including 'language' and any 'ui_labels' sent to
            generate_jwt. While post approvals are on, 'client_approval' says
            whether the end client may approve posts with this JWT.
        """
        # The API reads the token from the Authorization header, on a GET (a POST
        # with the token in the body was answered 405).
        try:
            response = self.session.get(
                f"{self.BASE_URL}/uploadposts/users/validate-jwt",
                headers={"Authorization": f"Bearer {jwt}"},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise self._api_error(e) from e

    def get_user_preferences(self) -> Dict:
        """
        Get user preferences (including calendar settings).

        Returns:
            User preferences including week_start_day.
        """
        return self._request("/uploadposts/users/preferences", "GET")

    def update_user_preferences(
        self,
        week_start_day: Optional[int] = None
    ) -> Dict:
        """
        Update user preferences (including calendar settings).

        Args:
            week_start_day: Week start day (0=Sunday, 1=Monday).

        Returns:
            Updated preferences.
        """
        body: Dict[str, Any] = {}
        if week_start_day is not None:
            body["week_start_day"] = week_start_day
        return self._request("/uploadposts/users/preferences", "POST", json_data=body)

    def get_notification_config(self) -> Dict:
        """
        Get notification configuration (including webhook settings).

        Returns:
            ``{"success": True, "notifications": {...}}`` with ``channels``,
            ``webhook_url``, ``webhook_events``, ``webhook_secret`` and
            ``channel_health``.
        """
        return self._request("/uploadposts/users/notifications", "GET")

    def update_notification_config(
        self,
        webhook_events: Optional[Union[List[str], Dict[str, bool]]] = None,
        webhook_url: Optional[str] = None,
        channels: Optional[Dict[str, bool]] = None,
    ) -> Dict:
        """
        Update notification configuration (including webhook settings).

        Only the fields you pass change; the rest are kept.

        Args:
            webhook_events: Webhook event types to subscribe to, as a list of
                names or a ``{name: bool}`` dict: upload_completed,
                social_account_connected, social_account_disconnected,
                social_account_reauth_required, and the opt-in dm_received
                (Instagram, Facebook Messenger, WhatsApp, Bluesky) and
                comment_received. The opt-in events are only sent when listed.
            webhook_url: Webhook URL for notifications.
            channels: Which channels are on, e.g. ``{"webhook": True}``
                (``telegram``, ``slack``, ``whatsapp``, ``webhook``).

        Returns:
            Updated notification config.
        """
        body: Dict[str, Any] = {}
        if webhook_events:
            body["webhook_events"] = webhook_events
        if webhook_url:
            body["webhook_url"] = webhook_url
        if channels:
            body["channels"] = channels
        return self._request("/uploadposts/users/notifications", "POST", json_data=body)

    def delete_notification_webhook(self) -> Dict:
        """Remove the account's notification webhook."""
        return self._request("/uploadposts/users/notifications", "DELETE")

    def rotate_webhook_secret(self) -> Dict:
        """Generate a new webhook signing secret (the old one stops working)."""
        return self._request("/uploadposts/users/webhook-secret", "POST", json_data={})

    def get_profile_webhook(self, profile_username: str) -> Dict:
        """Get the webhook of one profile (white-label setups)."""
        return self._request("/uploadposts/users/profile-webhook", "GET",
                             params={"profile_username": profile_username})

    def set_profile_webhook(
        self,
        profile_username: str,
        webhook_url: str,
        webhook_events: Optional[List[str]] = None,
    ) -> Dict:
        """Set the webhook of one profile; it receives only that profile's events."""
        body = {"profile_username": profile_username, "webhook_url": webhook_url}
        if webhook_events is not None:
            body["webhook_events"] = webhook_events
        return self._request("/uploadposts/users/profile-webhook", "POST", json_data=body)

    def delete_profile_webhook(self, profile_username: str) -> Dict:
        """Remove the webhook of one profile."""
        return self._request("/uploadposts/users/profile-webhook", "DELETE",
                             json_data={"profile_username": profile_username})

    # ==================== Teams ====================

    def list_team_members(self) -> Dict:
        """Owner: the team members, with ``suspended`` / ``suspended_reason``.

        With team roles on, each member also has ``role`` (admin, editor,
        contributor, viewer) and ``profiles`` (``None`` = every profile).
        Inviting members and changing roles is done by the owner in the
        dashboard, not with the API key.
        """
        return self._request("/uploadposts/teams/members", "GET")

    def list_shared_accounts(self) -> Dict:
        """Member: the accounts shared with you (pass the owner's email as ``act_as_user``).

        With team roles on, each account also has your ``role`` and ``profiles`` there.
        """
        return self._request("/uploadposts/teams/shared-with-me", "GET")

    # ==================== Webhook deliveries ====================

    def list_webhook_deliveries(
        self,
        event: Optional[str] = None,
        status: Optional[str] = None,
        request_id: Optional[str] = None,
        job_id: Optional[str] = None,
        profile_username: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        include_payload: Optional[bool] = None,
    ) -> Dict:
        """
        List the webhook deliveries of the account (7-day history), newest first.

        Every outgoing webhook (account and per-profile, every event) is logged
        with its attempts. Webhooks are delivered at least once: a timeout, a
        connection error, a 5xx, 408 or 429 is retried with the same body and
        the same ``X-Upload-Post-Delivery`` id (6 attempts over ~8.5 hours);
        other 4xx answers are final. Use this to check whether an event reached
        your server.

        Args:
            event: Only this event (e.g. ``"upload_completed"``, ``"dm_received"``).
            status: ``"pending"`` (a retry is scheduled), ``"delivered"``,
                ``"failed"`` or ``"cancelled"``.
            request_id: Only the deliveries of one upload.
            job_id: Only the deliveries of one scheduled/async job.
            profile_username: Only the deliveries of that profile's webhook.
            limit: Page size, 1-100 (server default 20).
            page: Page number, 1-50 (beyond that the API answers 400: narrow
                the list with ``status``, ``event`` or ``request_id``).
            include_payload: ``True`` to include each delivery's ``payload``
                (left out by default to keep the list light).

        Returns:
            ``{"success": True, "deliveries": [...], "page", "limit", "total",
            "has_more", "retention_days"}``. Each delivery has ``delivery_id``,
            ``event``, ``status``, ``target`` (``account``/``profile``),
            ``url`` (without its query string), ``attempt_count``,
            ``max_attempts``, ``last_status_code``, ``last_error``,
            ``next_attempt_at``, ``attempts[]``, ``redelivery_of``, ``test``...
        """
        params: Dict[str, Any] = {}
        for key, value in (("event", event), ("status", status),
                           ("request_id", request_id), ("job_id", job_id),
                           ("profile_username", profile_username),
                           ("limit", limit), ("page", page)):
            if value is not None:
                params[key] = value
        if include_payload is not None:
            params["include_payload"] = "true" if include_payload else "false"
        return self._request("/uploadposts/webhooks/deliveries", "GET", params=params)

    def get_webhook_delivery(self, delivery_id: str) -> Dict:
        """
        Get one webhook delivery, always with its ``payload`` (the exact body
        that was signed and sent).

        Raises ``UploadPostError`` with ``status_code`` 404 if it does not
        exist, is older than 7 days or belongs to another account.

        Args:
            delivery_id: ``delivery_id`` from list_webhook_deliveries (the
                ``X-Upload-Post-Delivery`` header your endpoint received).

        Returns:
            ``{"success": True, "delivery": {...}}``.
        """
        return self._request(
            f"/uploadposts/webhooks/deliveries/{quote(str(delivery_id), safe='')}", "GET"
        )

    def redeliver_webhook(self, delivery_id: str) -> Dict:
        """
        Send a logged webhook delivery again, right away, with the same body.

        It is a new delivery: it gets its own ``X-Upload-Post-Delivery`` id,
        carries the original in ``X-Upload-Post-Redelivery-Of``, goes to the
        webhook URL configured now and, if it fails in a retryable way, follows
        the normal retry schedule.

        Errors (``UploadPostError``): 404 if the delivery does not exist; 409
        with ``error_code`` ``"webhook_removed"``, ``"event_unsubscribed"`` or
        ``"blocked_url"`` when there is nowhere to send it; 503
        ``"delivery_log_disabled"`` while redelivery is switched off.

        Args:
            delivery_id: ``delivery_id`` from list_webhook_deliveries.

        Returns:
            ``{"success": True, "delivery": {...}}`` with the new delivery
            (``redelivery_of`` = the original id).
        """
        return self._request(
            f"/uploadposts/webhooks/deliveries/{quote(str(delivery_id), safe='')}/redeliver",
            "POST",
        )

    # ==================== Resource endpoints ====================
    #
    # Post actions, best times, the queue, and the Telegram, Bluesky and Google
    # Business management endpoints all go through _call(): every keyword is
    # sent to the API with its API name, nothing is dropped. Path parameters
    # (draft_id, nsid...) are taken out of the keywords. A file field (file,
    # photo, sticker, avatar, telegram_media...) given as a local path, bytes or
    # an open file turns the request into multipart/form-data; URLs and
    # Telegram file_ids stay strings.

    _FILE_FIELDS = frozenset({
        "file", "photo", "animation", "sticker", "avatar", "banner", "thumbnail", "image",
        "telegram_media", "telegram_thumbnail", "telegram_cover", "telegram_live_photo_photo",
    })

    @staticmethod
    def _query_value(value):
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (list, tuple)):
            return ",".join(str(v).lower() if isinstance(v, bool) else str(v) for v in value)
        if isinstance(value, dict):
            return json.dumps(value)
        return value

    @staticmethod
    def _form_value(value) -> str:
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value)
        return str(value)

    def _call(self, method: str, endpoint: str, params: Dict, defaults: Optional[Dict] = None,
              raw: bool = False) -> Dict:
        body = dict(defaults or {})
        body.update({k: v for k, v in params.items() if v is not None})
        for name in re.findall(r"\{(\w+)\}", endpoint):
            value = body.pop(name, None)
            if value is None or value == "":
                raise UploadPostError(f"{name} is required")
            endpoint = endpoint.replace("{%s}" % name, quote(str(value), safe=""))

        if method == "GET":
            return self._request(endpoint, "GET", params={k: self._query_value(v) for k, v in body.items()}, raw=raw)

        files: List[tuple] = []
        opened: List = []
        try:
            for key in list(body):
                if key not in self._FILE_FIELDS:
                    continue
                value = body[key]
                if isinstance(value, (bytes, bytearray)):
                    files.append((key, (key, bytes(value))))
                elif hasattr(value, "read"):
                    files.append((key, (os.path.basename(getattr(value, "name", key)) or key, value)))
                elif isinstance(value, (str, Path)) and not str(value).lower().startswith(("http://", "https://")) \
                        and Path(value).is_file():
                    fh = Path(value).open("rb")
                    opened.append(fh)
                    files.append((key, (Path(value).name, fh)))
                else:
                    continue
                body.pop(key)
            if files:
                data = [(k, self._form_value(v)) for k, v in body.items()]
                return self._request(endpoint, method, data=data, files=files)
            return self._request(endpoint, method, json_data=body)
        finally:
            for fh in opened:
                fh.close()

    # ---- Posts: edit, repost, actions ----
    def edit_post(self, user: str, platform: str, post_id: str, **params) -> Dict:
        """Edit a published post (Facebook, LinkedIn, X, Google Business, Telegram: text, buttons, pin/unpin, stop a poll, live location, replace the media).

        YouTube: ``title``, ``description``, ``tags``, ``privacyStatus``, ``categoryId``,
        ``publishAt``, ``hasPaidProductPlacement``, ``defaultLanguage``, ``embeddable``,
        ``publicStatsViewable``, ``selfDeclaredMadeForKids``, ``containsSyntheticMedia``,
        ``license``, ``recordingDate``, ``localizations``, ``localizations_remove``,
        ``brand_partner``.

        Required: ``user``, ``platform``, ``post_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/edit-post
        """
        return self._call("POST", "/uploadposts/posts/edit", dict(params, user=user, platform=platform, post_id=post_id))

    def repost_post(self, user: str, platform: str, post_id: Optional[str] = None, **params) -> Dict:
        """Repost / reshare a post (LinkedIn, X, Threads; Telegram forward or copy with `mode`, `post_ids`, `all_messages`).

        Required: ``user``, ``platform``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/repost
        """
        return self._call("POST", "/uploadposts/posts/repost", dict(params, user=user, platform=platform, post_id=post_id))

    def post_action(self, user: str, platform: str, action: str, **params) -> Dict:
        """Act on a published post: Telegram reactions and forward/copy; Bluesky bookmark/unbookmark, pin/unpin, reply and quote settings, detach/reattach quotes.

        Required: ``user``, ``platform``, ``action``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-post-actions
        """
        return self._call("POST", "/uploadposts/posts/action", dict(params, user=user, platform=platform, action=action))

    def save_post(self, user: str, post_id: str, **params) -> Dict:
        """Save a post: a Pinterest Pin to a board, or a Bluesky bookmark (`platform: "bluesky"`).

        Required: ``user``, ``post_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/save-pin
        """
        return self._call("POST", "/uploadposts/posts/save", dict(params, user=user, post_id=post_id))

    # ---- Best time to post and queue ----
    def get_best_times(self, profile_username: str, platform: str, **params) -> Dict:
        """Best hours to publish for a connected account, with `source` and `confidence` (`timezone`, `top`, `refresh`, `page_urn`, `facebook_page_id`).

        Required: ``profile_username``, ``platform``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/best-times
        """
        return self._call("GET", "/uploadposts/best-times", dict(params, profile_username=profile_username, platform=platform))

    def get_queue_settings(self, profile_username: str, **params) -> Dict:
        """Queue settings, including `slots_mode`, `auto_slots` and `effective_slots`.

        ``configured`` is False while the queue of the profile was never saved
        (``queue_settings`` then shows the defaults).

        Required: ``profile_username``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/queue-system
        """
        return self._call("GET", "/uploadposts/queue/settings", dict(params, profile_username=profile_username))

    def update_queue_settings(self, profile_username: str, **params) -> Dict:
        """Update the queue. `slots: "auto"` (or `slots_mode: "auto"`) fills the best hours automatically (`auto_slots_count`, `auto_platforms`, `refresh`); a `slots` array switches back to fixed slots.

        Required: ``profile_username``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/queue-system
        """
        return self._call("POST", "/uploadposts/queue/settings", dict(params, profile_username=profile_username))

    def get_queue_preview(self, profile_username: str, **params) -> Dict:
        """Upcoming queue slots and what is scheduled in each (`count`, max 50).

        Required: ``profile_username``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/queue-system
        """
        return self._call("GET", "/uploadposts/queue/preview", dict(params, profile_username=profile_username))

    def get_next_queue_slot(self, profile_username: str, **params) -> Dict:
        """Next free queue slot.

        Required: ``profile_username``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/queue-system
        """
        return self._call("GET", "/uploadposts/queue/next-slot", dict(params, profile_username=profile_username))

    def mark_queue_slot_full(self, profile_username: str, slot_datetime: str, **params) -> Dict:
        """Mark a queue slot (ISO 8601, UTC) as full.

        Required: ``profile_username``, ``slot_datetime``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/queue-system
        """
        return self._call("POST", "/uploadposts/queue/slot-full", dict(params, profile_username=profile_username, slot_datetime=slot_datetime))

    def unmark_queue_slot_full(self, profile_username: str, slot_datetime: str, **params) -> Dict:
        """Unmark a queue slot marked as full.

        Required: ``profile_username``, ``slot_datetime``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/queue-system
        """
        return self._call("DELETE", "/uploadposts/queue/slot-full", dict(params, profile_username=profile_username, slot_datetime=slot_datetime))

    # ---- Telegram: chat, members and invite links ----
    def get_telegram_chat_info(self, user: str, **params) -> Dict:
        """Chat details, subscribers/members and administrators (`include_administrators`, `return_bots`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat-insights
        """
        return self._call("GET", "/uploadposts/telegram/chat-info", dict(params, user=user))

    def update_telegram_chat_info(self, user: str, **params) -> Dict:
        """Change the chat title, description, photo (file or `photo_url`), permissions, slow mode, sticker set...

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("PATCH", "/uploadposts/telegram/chat-info", dict(params, user=user))

    def get_telegram_boosts(self, user: str, **params) -> Dict:
        """Boosts of the chat (with `user_id`: that user's boosts).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat-insights
        """
        return self._call("GET", "/uploadposts/telegram/boosts", dict(params, user=user))

    def get_telegram_member(self, user: str, **params) -> Dict:
        """Read one member (`user_id`) or list the administrators.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("GET", "/uploadposts/telegram/members", dict(params, user=user))

    def moderate_telegram_member(self, user: str, **params) -> Dict:
        """Ban, unban, restrict, promote or give a custom title to a member (`action`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("POST", "/uploadposts/telegram/members", dict(params, user=user))

    def create_telegram_invite_link(self, user: str, **params) -> Dict:
        """Create an invite link (name, expiry, member limit, join requests, subscription).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("POST", "/uploadposts/telegram/invite-links", dict(params, user=user))

    def edit_telegram_invite_link(self, user: str, **params) -> Dict:
        """Edit an invite link.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("PATCH", "/uploadposts/telegram/invite-links", dict(params, user=user))

    def revoke_telegram_invite_link(self, user: str, **params) -> Dict:
        """Revoke an invite link.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("DELETE", "/uploadposts/telegram/invite-links", dict(params, user=user))

    def create_telegram_primary_invite_link(self, user: str, **params) -> Dict:
        """Generate a new primary invite link (the previous one stops working).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("POST", "/uploadposts/telegram/invite-links/primary", dict(params, user=user))

    def answer_telegram_join_request(self, user: str, **params) -> Dict:
        """Approve or decline a request to join the chat.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("POST", "/uploadposts/telegram/join-requests", dict(params, user=user))

    def get_telegram_topic_icons(self, user: str, **params) -> Dict:
        """Custom emoji that can be used as forum topic icons.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("GET", "/uploadposts/telegram/topics/icons", dict(params, user=user))

    def create_telegram_topic(self, user: str, **params) -> Dict:
        """Create a forum topic.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("POST", "/uploadposts/telegram/topics", dict(params, user=user))

    def edit_telegram_topic(self, user: str, **params) -> Dict:
        """Edit, close, reopen, hide, unhide or unpin a forum topic.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("PATCH", "/uploadposts/telegram/topics", dict(params, user=user))

    def delete_telegram_topic(self, user: str, **params) -> Dict:
        """Delete a forum topic.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("DELETE", "/uploadposts/telegram/topics", dict(params, user=user))

    def unpin_all_telegram_messages(self, user: str, **params) -> Dict:
        """Unpin every message of the chat (or of a topic).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("POST", "/uploadposts/telegram/unpin-all", dict(params, user=user))

    def leave_telegram_chat(self, user: str, **params) -> Dict:
        """Make the bot leave the connected chat.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("POST", "/uploadposts/telegram/leave", dict(params, user=user))

    def answer_telegram_suggested_post(self, user: str, **params) -> Dict:
        """Approve or decline a suggested post in a channel direct messages chat.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("POST", "/uploadposts/telegram/suggested-posts", dict(params, user=user))

    def get_telegram_user_personal_chat_messages(self, user: str, user_id: Union[int, str], **params) -> Dict:
        """Last messages of a user's personal channel.

        Required: ``user``, ``user_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("GET", "/uploadposts/telegram/users/{user_id}/personal-chat-messages", dict(params, user=user, user_id=user_id))

    def get_telegram_user_profile_audios(self, user: str, user_id: Union[int, str], **params) -> Dict:
        """Profile audios of a Telegram user.

        Required: ``user``, ``user_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("GET", "/uploadposts/telegram/users/{user_id}/profile-audios", dict(params, user=user, user_id=user_id))

    def get_telegram_share_theme_backdrops(self, user: str, **params) -> Dict:
        """Backdrops available for the Telegram share screen theme.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat
        """
        return self._call("GET", "/uploadposts/telegram/share-theme-backdrops", dict(params, user=user))

    def get_telegram_updates_status(self, user: str, **params) -> Dict:
        """Whether update receiving is on for the bot.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-inbox
        """
        return self._call("GET", "/uploadposts/telegram/updates", dict(params, user=user))

    # ---- Telegram: bot profile, commands and stickers ----
    def get_telegram_bot_profile(self, user: str, **params) -> Dict:
        """Bot name, descriptions, photo, menu button and default administrator rights.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-bot-profile
        """
        return self._call("GET", "/uploadposts/telegram/bot-profile", dict(params, user=user))

    def update_telegram_bot_profile(self, user: str, **params) -> Dict:
        """Change the bot profile (`photo`/`animation` as file or URL, `menu_button`, `default_administrator_rights`...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-bot-profile
        """
        return self._call("PATCH", "/uploadposts/telegram/bot-profile", dict(params, user=user))

    def get_telegram_bot_commands(self, user: str, **params) -> Dict:
        """Bot commands for a scope and language.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-bot-profile
        """
        return self._call("GET", "/uploadposts/telegram/bot-commands", dict(params, user=user))

    def set_telegram_bot_commands(self, user: str, **params) -> Dict:
        """Set the bot commands (`commands`, `scope`, `language_code`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-bot-profile
        """
        return self._call("POST", "/uploadposts/telegram/bot-commands", dict(params, user=user))

    def delete_telegram_bot_commands(self, user: str, **params) -> Dict:
        """Delete the bot commands of a scope and language.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-bot-profile
        """
        return self._call("DELETE", "/uploadposts/telegram/bot-commands", dict(params, user=user))

    def get_telegram_sticker_set(self, user: str, **params) -> Dict:
        """Read a sticker set (`name`) or custom emoji stickers.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-stickers
        """
        return self._call("GET", "/uploadposts/telegram/sticker-sets", dict(params, user=user))

    def create_telegram_sticker_set(self, user: str, **params) -> Dict:
        """Create a sticker set.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-stickers
        """
        return self._call("POST", "/uploadposts/telegram/sticker-sets", dict(params, user=user))

    def edit_telegram_sticker_set(self, user: str, **params) -> Dict:
        """Edit a sticker set (add, replace, reorder stickers, title, thumbnail, emoji, keywords...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-stickers
        """
        return self._call("PATCH", "/uploadposts/telegram/sticker-sets", dict(params, user=user))

    def delete_telegram_sticker_set(self, user: str, **params) -> Dict:
        """Delete a sticker set, or a sticker from it.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-stickers
        """
        return self._call("DELETE", "/uploadposts/telegram/sticker-sets", dict(params, user=user))

    def upload_telegram_sticker_file(self, user: str, **params) -> Dict:
        """Upload a sticker file (`sticker` file or `sticker_url`, `sticker_format`, `owner_user_id`); returns its `file_id`.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-stickers
        """
        return self._call("POST", "/uploadposts/telegram/sticker-sets/upload", dict(params, user=user))

    # ---- Telegram: Stars, invoices and gifts ----
    def get_telegram_stars(self, user: str, **params) -> Dict:
        """The bot's Telegram Stars balance.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat-insights
        """
        return self._call("GET", "/uploadposts/telegram/stars", dict(params, user=user))

    def get_telegram_star_transactions(self, user: str, **params) -> Dict:
        """The bot's Telegram Stars transactions (`offset`, `limit`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-chat-insights
        """
        return self._call("GET", "/uploadposts/telegram/stars/transactions", dict(params, user=user))

    def send_telegram_invoice(self, user: str, **params) -> Dict:
        """Send an invoice to the connected chat or to `chat_id` (payments go to your bot).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-payments
        """
        return self._call("POST", "/uploadposts/telegram/invoices", dict(params, user=user))

    def create_telegram_invoice_link(self, user: str, **params) -> Dict:
        """Create an invoice link.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-payments
        """
        return self._call("POST", "/uploadposts/telegram/invoice-links", dict(params, user=user))

    def refund_telegram_star_payment(self, user: str, **params) -> Dict:
        """Refund a Telegram Stars payment (`user_id`, `telegram_payment_charge_id`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-payments
        """
        return self._call("POST", "/uploadposts/telegram/stars/refund", dict(params, user=user))

    def edit_telegram_star_subscription(self, user: str, **params) -> Dict:
        """Cancel or re-enable a user's Stars subscription.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-payments
        """
        return self._call("POST", "/uploadposts/telegram/stars/subscription", dict(params, user=user))

    def get_telegram_available_gifts(self, user: str, **params) -> Dict:
        """Gifts the bot can send.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-payments
        """
        return self._call("GET", "/uploadposts/telegram/gifts", dict(params, user=user))

    def get_telegram_owned_gifts(self, user: str, **params) -> Dict:
        """Gifts owned by a user or a chat.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-payments
        """
        return self._call("GET", "/uploadposts/telegram/gifts/owned", dict(params, user=user))

    def get_telegram_unique_gift(self, user: str, **params) -> Dict:
        """A unique gift by name.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-payments
        """
        return self._call("GET", "/uploadposts/telegram/gifts/unique", dict(params, user=user))

    def get_telegram_unanswered_payments(self, user: str, **params) -> Dict:
        """Payment queries that were not answered in time.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/telegram-payments
        """
        return self._call("GET", "/uploadposts/telegram/payments/unanswered", dict(params, user=user))

    # ---- Bluesky: reads ----
    def get_post_engagement(self, post_id: str, **params) -> Dict:
        """Who liked, reposted or quoted a post (`type`: likes, reposts, quotes; `limit`, `cursor`).

        Required: ``post_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-reads
        """
        return self._call("GET", "/uploadposts/post-engagement", dict(params, post_id=post_id), defaults={'platform': 'bluesky'})

    def get_bluesky_profiles(self, **params) -> Dict:
        """One or several Bluesky profiles (`actor`: handles or DIDs, comma separated, up to 25; without it, the connected account).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-reads
        """
        return self._call("GET", "/uploadposts/bluesky/profile", params)

    def search_bluesky_posts(self, user: str, q: str, **params) -> Dict:
        """Search Bluesky posts (`sort`, `since`, `until`, `author`, `lang`, `tag`, `limit`, `cursor`...).

        Required: ``user``, ``q``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-reads
        """
        return self._call("GET", "/uploadposts/bluesky/search/posts", dict(params, user=user, q=q))

    def search_bluesky_actors(self, q: str, **params) -> Dict:
        """Search Bluesky accounts.

        Required: ``q``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-reads
        """
        return self._call("GET", "/uploadposts/bluesky/search/actors", dict(params, q=q))

    def get_bluesky_followers(self, **params) -> Dict:
        """Followers of an account (`actor`, or the connected one with `user`; `known=true` for followers you follow).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-reads
        """
        return self._call("GET", "/uploadposts/bluesky/followers", params)

    def get_bluesky_follows(self, **params) -> Dict:
        """Accounts an account follows.

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-reads
        """
        return self._call("GET", "/uploadposts/bluesky/follows", params)

    def bluesky_xrpc(self, nsid: str, **params) -> Dict:
        """Read-only gateway to an allow-listed public Bluesky XRPC method (e.g. `app.bsky.feed.getAuthorFeed`); returns Bluesky's answer untouched.

        Required: ``nsid``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-reads
        """
        return self._call("GET", "/uploadposts/bluesky/xrpc/{nsid}", dict(params, nsid=nsid))

    def get_bluesky_labels(self, user: str, **params) -> Dict:
        """Moderation labels on the account and its posts.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-reads
        """
        return self._call("GET", "/uploadposts/bluesky/labels", dict(params, user=user))

    # ---- Bluesky: notifications ----
    def get_bluesky_notifications(self, user: str, **params) -> Dict:
        """List notifications (`reasons`, `priority`, `limit`, `cursor`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-notifications
        """
        return self._call("GET", "/uploadposts/bluesky/notifications", dict(params, user=user))

    def get_bluesky_unread_count(self, user: str, **params) -> Dict:
        """Unread notification count.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-notifications
        """
        return self._call("GET", "/uploadposts/bluesky/notifications/unread-count", dict(params, user=user))

    def mark_bluesky_notifications_seen(self, user: str, **params) -> Dict:
        """Mark notifications as seen (up to `seen_at`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-notifications
        """
        return self._call("POST", "/uploadposts/bluesky/notifications/seen", dict(params, user=user))

    def get_bluesky_notification_preferences(self, user: str, **params) -> Dict:
        """Notification preferences.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-notifications
        """
        return self._call("GET", "/uploadposts/bluesky/notification-preferences", dict(params, user=user))

    def update_bluesky_notification_preferences(self, user: str, **params) -> Dict:
        """Update notification preferences.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-notifications
        """
        return self._call("POST", "/uploadposts/bluesky/notification-preferences", dict(params, user=user))

    def get_bluesky_activity_subscriptions(self, user: str, **params) -> Dict:
        """Accounts whose activity you are subscribed to.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-notifications
        """
        return self._call("GET", "/uploadposts/bluesky/activity-subscriptions", dict(params, user=user))

    def set_bluesky_activity_subscription(self, user: str, **params) -> Dict:
        """Subscribe to (or stop) an account's posts and replies.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-notifications
        """
        return self._call("POST", "/uploadposts/bluesky/activity-subscriptions", dict(params, user=user))

    # ---- Bluesky: profile, settings and drafts ----
    def get_bluesky_own_profile(self, user: str, **params) -> Dict:
        """The connected account's profile record.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("GET", "/uploadposts/bluesky/profile/self", dict(params, user=user))

    def update_bluesky_profile(self, user: str, **params) -> Dict:
        """Update the profile (display name, description, `avatar`/`banner` files, links, pinned post...). Fields not sent stay as they are.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("POST", "/uploadposts/bluesky/profile/self", dict(params, user=user))

    def get_bluesky_status(self, user: str, **params) -> Dict:
        """Read the live status.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("GET", "/uploadposts/bluesky/status", dict(params, user=user))

    def set_bluesky_status(self, user: str, **params) -> Dict:
        """Set the live status.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("POST", "/uploadposts/bluesky/status", dict(params, user=user))

    def clear_bluesky_status(self, user: str, **params) -> Dict:
        """Clear the live status.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("DELETE", "/uploadposts/bluesky/status", dict(params, user=user))

    def get_bluesky_settings(self, user: str, **params) -> Dict:
        """Chat and discovery settings.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("GET", "/uploadposts/bluesky/settings", dict(params, user=user))

    def update_bluesky_settings(self, user: str, **params) -> Dict:
        """Change chat and discovery settings.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("POST", "/uploadposts/bluesky/settings", dict(params, user=user))

    def get_bluesky_preferences(self, user: str, **params) -> Dict:
        """App preferences (content filters, feeds, muted words...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("GET", "/uploadposts/bluesky/preferences", dict(params, user=user))

    def update_bluesky_preferences(self, user: str, **params) -> Dict:
        """Replace some app preferences.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-profile
        """
        return self._call("PUT", "/uploadposts/bluesky/preferences", dict(params, user=user))

    def list_bluesky_drafts(self, user: str, **params) -> Dict:
        """List drafts.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-drafts
        """
        return self._call("GET", "/uploadposts/bluesky/drafts", dict(params, user=user))

    def create_bluesky_draft(self, user: str, **params) -> Dict:
        """Create a draft.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-drafts
        """
        return self._call("POST", "/uploadposts/bluesky/drafts", dict(params, user=user))

    def update_bluesky_draft(self, user: str, draft_id: str, **params) -> Dict:
        """Replace a draft.

        Required: ``user``, ``draft_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-drafts
        """
        return self._call("PATCH", "/uploadposts/bluesky/drafts/{draft_id}", dict(params, user=user, draft_id=draft_id))

    def delete_bluesky_draft(self, user: str, draft_id: str, **params) -> Dict:
        """Delete a draft.

        Required: ``user``, ``draft_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-drafts
        """
        return self._call("DELETE", "/uploadposts/bluesky/drafts/{draft_id}", dict(params, user=user, draft_id=draft_id))

    # ---- Bluesky: chat ----
    def get_bluesky_chat_status(self, user: str, **params) -> Dict:
        """Chat status of the account.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-chat
        """
        return self._call("GET", "/uploadposts/dms/bluesky/status", dict(params, user=user))

    def get_bluesky_chat_preferences(self, user: str, **params) -> Dict:
        """DM notification settings.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-chat
        """
        return self._call("GET", "/uploadposts/dms/bluesky/preferences", dict(params, user=user))

    def update_bluesky_chat_preferences(self, user: str, **params) -> Dict:
        """Change DM notification settings.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-chat
        """
        return self._call("POST", "/uploadposts/dms/bluesky/preferences", dict(params, user=user))

    def export_bluesky_chat(self, user: str, **params) -> Dict:
        """Export the account's chat history.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/bluesky-chat
        """
        return self._call("GET", "/uploadposts/dms/bluesky/export", dict(params, user=user))

    # ---- Google Business: posts and reviews ----
    def list_google_business_posts(self, user: str, **params) -> Dict:
        """List the location's posts (`location_id`, `page_size`, `page_token`). Edit them with editPost and delete them with unpublishPost.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-posts
        """
        return self._call("GET", "/uploadposts/google-business/posts", dict(params, user=user))

    def get_google_business_post(self, user: str, **params) -> Dict:
        """Read one post (`post_id` or `post_name`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-posts
        """
        return self._call("GET", "/uploadposts/google-business/posts/get", dict(params, user=user))

    def list_google_business_reviews(self, user: str, **params) -> Dict:
        """List reviews (`location_id`, `page_size`, `page_token`, `order_by`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-reviews
        """
        return self._call("GET", "/uploadposts/google-business/reviews", dict(params, user=user))

    def get_google_business_review(self, user: str, **params) -> Dict:
        """Read one review (`review_name`, or `review_id` + `location_id`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-reviews
        """
        return self._call("GET", "/uploadposts/google-business/reviews/get", dict(params, user=user))

    def batch_get_google_business_reviews(self, user: str, **params) -> Dict:
        """Reviews of several locations at once (`location_ids`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-reviews
        """
        return self._call("GET", "/uploadposts/google-business/reviews/batch", dict(params, user=user))

    def reply_to_google_business_review(self, user: str, comment: str, **params) -> Dict:
        """Reply to a review, or replace the reply (`review_name`, or `review_id` + `location_id`).

        Required: ``user``, ``comment``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-reviews
        """
        return self._call("PUT", "/uploadposts/google-business/reviews/reply", dict(params, user=user, comment=comment))

    def delete_google_business_review_reply(self, user: str, **params) -> Dict:
        """Delete the reply to a review.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-reviews
        """
        return self._call("DELETE", "/uploadposts/google-business/reviews/reply", dict(params, user=user))

    # ---- Google Business: gallery and performance ----
    def list_google_business_media(self, user: str, **params) -> Dict:
        """List the location's gallery.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-media
        """
        return self._call("GET", "/uploadposts/google-business/media", dict(params, user=user))

    def get_google_business_media(self, user: str, **params) -> Dict:
        """Read one gallery item.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-media
        """
        return self._call("GET", "/uploadposts/google-business/media/get", dict(params, user=user))

    def upload_google_business_media(self, user: str, **params) -> Dict:
        """Upload a photo or video to the gallery: `file` (local path, stream or Buffer) or `source_url`, plus `category`, `description`, `media_format`.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-media
        """
        return self._call("POST", "/uploadposts/google-business/media", dict(params, user=user))

    def update_google_business_media(self, user: str, **params) -> Dict:
        """Change a gallery item's category.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-media
        """
        return self._call("PATCH", "/uploadposts/google-business/media", dict(params, user=user))

    def delete_google_business_media(self, user: str, **params) -> Dict:
        """Delete a gallery item.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-media
        """
        return self._call("DELETE", "/uploadposts/google-business/media", dict(params, user=user))

    def list_google_business_customer_media(self, user: str, **params) -> Dict:
        """Photos uploaded by customers.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-media
        """
        return self._call("GET", "/uploadposts/google-business/media/customers", dict(params, user=user))

    def get_google_business_customer_media(self, user: str, **params) -> Dict:
        """One customer photo.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-media
        """
        return self._call("GET", "/uploadposts/google-business/media/customers/get", dict(params, user=user))

    def get_google_business_performance(self, user: str, **params) -> Dict:
        """Daily metrics for any date range (impressions, calls, website clicks, directions...: `metrics`, `start_date`, `end_date`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-performance
        """
        return self._call("GET", "/uploadposts/google-business/performance", dict(params, user=user))

    def get_google_business_search_keywords(self, user: str, **params) -> Dict:
        """Monthly search keywords that showed the location (`start_month`, `end_month`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-performance
        """
        return self._call("GET", "/uploadposts/google-business/performance/keywords", dict(params, user=user))

    # ---- Google Business: location info ----
    def get_google_business_location_info(self, user: str, **params) -> Dict:
        """Read the location's info (name, address, hours, phones, categories, service area, open status...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-info
        """
        return self._call("GET", "/uploadposts/google-business/location-info", dict(params, user=user))

    def update_google_business_location_info(self, user: str, **params) -> Dict:
        """Edit the location's info. `edit_mode: "legacy"` (default) or `"strict"` (`dry_run`, `confirm`, `include_edit_status`); `validate_only` in both.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-info
        """
        return self._call("PATCH", "/uploadposts/google-business/location-info", dict(params, user=user))

    def get_google_business_google_updates(self, user: str, **params) -> Dict:
        """Changes Google suggested for the location (`diff_fields`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-info
        """
        return self._call("GET", "/uploadposts/google-business/location-info/google-updated", dict(params, user=user))

    def answer_google_business_google_updates(self, user: str, decision: str, fields: List[str], **params) -> Dict:
        """Accept or reject Google's suggested changes, field by field.

        Required: ``user``, ``decision``, ``fields``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-info
        """
        return self._call("POST", "/uploadposts/google-business/location-info/google-updates", dict(params, user=user, decision=decision, fields=fields))

    def get_google_business_location_info_extended(self, user: str, **params) -> Dict:
        """Edit status of each field (experimental).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-info
        """
        return self._call("GET", "/uploadposts/google-business/location-info/extended", dict(params, user=user))

    def list_google_business_locations(self, user: str, **params) -> Dict:
        """List locations with filters (`account`, `filter`, `order_by`, `read_mask`, `page_size`, `page_token`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-info
        """
        return self._call("GET", "/uploadposts/google-business/locations/list", dict(params, user=user))

    def get_google_business_pinned_location(self, profile_username: str, **params) -> Dict:
        """Locations available to a profile and the one pinned for its uploads.

        Required: ``profile_username``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-location
        """
        return self._call("GET", "/uploadposts/users/google-business-location", dict(params, profile_username=profile_username))

    def pin_google_business_location(self, profile_username: str, gbp_location_id: str, **params) -> Dict:
        """Pin the location a profile publishes to (instead of passing gbpLocationId on every upload).

        Required: ``profile_username``, ``gbp_location_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-location
        """
        return self._call("POST", "/uploadposts/users/google-business-location", dict(params, profile_username=profile_username, gbp_location_id=gbp_location_id))

    def clear_google_business_location_pin(self, profile_username: str, **params) -> Dict:
        """Clear the pinned location.

        Required: ``profile_username``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-location
        """
        return self._call("DELETE", "/uploadposts/users/google-business-location", dict(params, profile_username=profile_username))

    # ---- Google Business: catalogs, attributes, Place Actions, menus, services and lodging ----
    def search_google_business_categories(self, **params) -> Dict:
        """Search categories (`region_code`, `language_code`, `query`).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-catalogs
        """
        return self._call("GET", "/uploadposts/google-business/categories", params)

    def batch_get_google_business_categories(self, **params) -> Dict:
        """Category details: service types and more-hours types (`names`).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-catalogs
        """
        return self._call("GET", "/uploadposts/google-business/categories/batch", params)

    def search_google_business_chains(self, **params) -> Dict:
        """Search chains (`name`).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-catalogs
        """
        return self._call("GET", "/uploadposts/google-business/chains", params)

    def get_google_business_chain(self, **params) -> Dict:
        """One chain (`chain`).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-catalogs
        """
        return self._call("GET", "/uploadposts/google-business/chains/get", params)

    def search_google_business_google_locations(self, user: str, **params) -> Dict:
        """Is the business already on Google? Search Google's listings.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-catalogs
        """
        return self._call("POST", "/uploadposts/google-business/google-locations/search", dict(params, user=user))

    def get_google_business_recommended_locations(self, user: str, **params) -> Dict:
        """Locations Google recommends for the account.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-catalogs
        """
        return self._call("GET", "/uploadposts/google-business/google-locations/recommended", dict(params, user=user))

    def report_google_business_google_location(self, user: str, **params) -> Dict:
        """Report a wrong listing to Google.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-catalogs
        """
        return self._call("POST", "/uploadposts/google-business/google-locations/report", dict(params, user=user))

    def get_google_business_available_attributes(self, user: str, **params) -> Dict:
        """Attributes the location can use.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-attributes
        """
        return self._call("GET", "/uploadposts/google-business/attributes/available", dict(params, user=user))

    def get_google_business_attributes(self, user: str, **params) -> Dict:
        """Current attributes of the location.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-attributes
        """
        return self._call("GET", "/uploadposts/google-business/attributes", dict(params, user=user))

    def update_google_business_attributes(self, user: str, **params) -> Dict:
        """Update attributes.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-attributes
        """
        return self._call("PATCH", "/uploadposts/google-business/attributes", dict(params, user=user))

    def get_google_business_attributes_google_updated(self, user: str, **params) -> Dict:
        """Attributes as Google shows them.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-attributes
        """
        return self._call("GET", "/uploadposts/google-business/attributes/google-updated", dict(params, user=user))

    def get_google_business_attributes_extended(self, user: str, **params) -> Dict:
        """Attributes with their edit status (experimental).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-attributes
        """
        return self._call("GET", "/uploadposts/google-business/attributes/extended", dict(params, user=user))

    def get_google_business_place_action_types(self, user: str, **params) -> Dict:
        """Place Action types (booking, ordering, shopping links...) the location can use.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-place-actions
        """
        return self._call("GET", "/uploadposts/google-business/place-actions/types", dict(params, user=user))

    def list_google_business_place_actions(self, user: str, **params) -> Dict:
        """List Place Action links.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-place-actions
        """
        return self._call("GET", "/uploadposts/google-business/place-actions", dict(params, user=user))

    def get_google_business_place_action(self, user: str, **params) -> Dict:
        """Read one Place Action link (`link`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-place-actions
        """
        return self._call("GET", "/uploadposts/google-business/place-actions/get", dict(params, user=user))

    def create_google_business_place_action(self, user: str, **params) -> Dict:
        """Create a Place Action link.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-place-actions
        """
        return self._call("POST", "/uploadposts/google-business/place-actions", dict(params, user=user))

    def update_google_business_place_action(self, user: str, **params) -> Dict:
        """Edit or switch off a Place Action link.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-place-actions
        """
        return self._call("PATCH", "/uploadposts/google-business/place-actions", dict(params, user=user))

    def delete_google_business_place_action(self, user: str, **params) -> Dict:
        """Delete a Place Action link.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-place-actions
        """
        return self._call("DELETE", "/uploadposts/google-business/place-actions", dict(params, user=user))

    def get_google_business_food_menus(self, user: str, **params) -> Dict:
        """Food menus of the location.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-menus-services
        """
        return self._call("GET", "/uploadposts/google-business/food-menus", dict(params, user=user))

    def update_google_business_food_menus(self, user: str, **params) -> Dict:
        """Replace the food menus.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-menus-services
        """
        return self._call("PUT", "/uploadposts/google-business/food-menus", dict(params, user=user))

    def get_google_business_services(self, user: str, **params) -> Dict:
        """Services of the location.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-menus-services
        """
        return self._call("GET", "/uploadposts/google-business/services", dict(params, user=user))

    def update_google_business_services(self, user: str, **params) -> Dict:
        """Replace the services.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-menus-services
        """
        return self._call("PUT", "/uploadposts/google-business/services", dict(params, user=user))

    def get_google_business_lodging(self, user: str, **params) -> Dict:
        """Lodging data of a hotel (`read_mask`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-lodging
        """
        return self._call("GET", "/uploadposts/google-business/lodging", dict(params, user=user))

    def update_google_business_lodging(self, user: str, **params) -> Dict:
        """Update lodging data.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-lodging
        """
        return self._call("PATCH", "/uploadposts/google-business/lodging", dict(params, user=user))

    def get_google_business_lodging_google_updated(self, user: str, **params) -> Dict:
        """Lodging data as Google shows it.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-lodging
        """
        return self._call("GET", "/uploadposts/google-business/lodging/google-updated", dict(params, user=user))

    # ---- Google Business: accounts and verification (reads) ----
    def list_google_business_accounts(self, user: str, **params) -> Dict:
        """Google Business accounts and location groups (`type`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-accounts
        """
        return self._call("GET", "/uploadposts/google-business/accounts", dict(params, user=user))

    def get_google_business_account(self, user: str, **params) -> Dict:
        """Read one account (`account`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-accounts
        """
        return self._call("GET", "/uploadposts/google-business/accounts/get", dict(params, user=user))

    def create_google_business_account(self, user: str, **params) -> Dict:
        """Create a location group or user group (`type`, `account_name`, `confirm`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-accounts
        """
        return self._call("POST", "/uploadposts/google-business/accounts", dict(params, user=user))

    def list_google_business_admins(self, user: str, **params) -> Dict:
        """Admins of an account or a location (`scope`, `location_id`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-accounts
        """
        return self._call("GET", "/uploadposts/google-business/admins", dict(params, user=user))

    def list_google_business_invitations(self, user: str, **params) -> Dict:
        """Pending invitations of an account.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-accounts
        """
        return self._call("GET", "/uploadposts/google-business/invitations", dict(params, user=user))

    def get_google_business_verification_state(self, user: str, **params) -> Dict:
        """Whether the location is verified and in good standing.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-verification
        """
        return self._call("GET", "/uploadposts/google-business/verification/state", dict(params, user=user))

    def get_google_business_verification_options(self, user: str, **params) -> Dict:
        """Verification methods available for the location.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-verification
        """
        return self._call("POST", "/uploadposts/google-business/verification/options", dict(params, user=user))

    def list_google_business_verifications(self, user: str, **params) -> Dict:
        """Past verifications of the location.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/google-business-verification
        """
        return self._call("GET", "/uploadposts/google-business/verifications", dict(params, user=user))

    # ---- YouTube: videos, thumbnail and quota ----
    def get_youtube_videos(self, user: str, **params) -> Dict:
        """Full details of videos: status, processing, statistics, translations, paid placement... (`ids`, `chart` or `my_rating`; `parts`, `include_owner_details`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-videos
        """
        return self._call("GET", "/uploadposts/youtube/videos", dict(params, user=user))

    def get_youtube_quota(self, **params) -> Dict:
        """Your account's daily allowance for the YouTube management endpoints and what is left.

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-videos
        """
        return self._call("GET", "/uploadposts/youtube/quota", params)

    def set_youtube_thumbnail(self, user: str, video_id: str, **params) -> Dict:
        """Set a video's thumbnail: `thumbnail` (local file, stream or Buffer) or `thumbnail_url`.

        Required: ``user``, ``video_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-thumbnail
        """
        return self._call("POST", "/uploadposts/youtube/thumbnail", dict(params, user=user, video_id=video_id))

    # ---- YouTube: playlists ----
    def list_youtube_playlists(self, user: str, **params) -> Dict:
        """List the channel's playlists (or `ids`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("GET", "/uploadposts/youtube/playlists", dict(params, user=user))

    def create_youtube_playlist(self, user: str, **params) -> Dict:
        """Create a playlist (`title`, `description`, `privacy_status`, `default_language`, `localizations`...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("POST", "/uploadposts/youtube/playlists", dict(params, user=user))

    def update_youtube_playlist(self, user: str, playlist_id: str, **params) -> Dict:
        """Edit a playlist (only what you send changes).

        Required: ``user``, ``playlist_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("PATCH", "/uploadposts/youtube/playlists/{playlist_id}", dict(params, user=user, playlist_id=playlist_id))

    def delete_youtube_playlist(self, user: str, playlist_id: str, **params) -> Dict:
        """Delete a playlist (needs `confirm: true`; the videos stay).

        Required: ``user``, ``playlist_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("DELETE", "/uploadposts/youtube/playlists/{playlist_id}", dict(params, user=user, playlist_id=playlist_id))

    def list_youtube_playlist_items(self, user: str, playlist_id: str, **params) -> Dict:
        """Videos of a playlist.

        Required: ``user``, ``playlist_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("GET", "/uploadposts/youtube/playlists/{playlist_id}/items", dict(params, user=user, playlist_id=playlist_id))

    def add_youtube_playlist_item(self, user: str, playlist_id: str, **params) -> Dict:
        """Add a video to a playlist (`video_id`, `position`, `note`).

        Required: ``user``, ``playlist_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("POST", "/uploadposts/youtube/playlists/{playlist_id}/items", dict(params, user=user, playlist_id=playlist_id))

    def update_youtube_playlist_item(self, user: str, playlist_id: str, item_id: str, **params) -> Dict:
        """Reorder a playlist video or change its note.

        Required: ``user``, ``playlist_id``, ``item_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("PATCH", "/uploadposts/youtube/playlists/{playlist_id}/items/{item_id}", dict(params, user=user, playlist_id=playlist_id, item_id=item_id))

    def delete_youtube_playlist_item(self, user: str, playlist_id: str, item_id: str, **params) -> Dict:
        """Remove a video from a playlist (needs `confirm: true`).

        Required: ``user``, ``playlist_id``, ``item_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("DELETE", "/uploadposts/youtube/playlists/{playlist_id}/items/{item_id}", dict(params, user=user, playlist_id=playlist_id, item_id=item_id))

    def get_youtube_playlist_image(self, user: str, playlist_id: str, **params) -> Dict:
        """The playlist's custom image.

        Required: ``user``, ``playlist_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("GET", "/uploadposts/youtube/playlists/{playlist_id}/image", dict(params, user=user, playlist_id=playlist_id))

    def set_youtube_playlist_image(self, user: str, playlist_id: str, **params) -> Dict:
        """Add the playlist image: `image` (local file, stream or Buffer) or `image_url`.

        Required: ``user``, ``playlist_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("POST", "/uploadposts/youtube/playlists/{playlist_id}/image", dict(params, user=user, playlist_id=playlist_id))

    def replace_youtube_playlist_image(self, user: str, playlist_id: str, **params) -> Dict:
        """Replace the playlist image (same fields, needs `confirm: true`).

        Required: ``user``, ``playlist_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("PUT", "/uploadposts/youtube/playlists/{playlist_id}/image", dict(params, user=user, playlist_id=playlist_id))

    def delete_youtube_playlist_image(self, user: str, playlist_id: str, **params) -> Dict:
        """Remove the playlist image (needs `confirm: true`).

        Required: ``user``, ``playlist_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-playlists
        """
        return self._call("DELETE", "/uploadposts/youtube/playlists/{playlist_id}/image", dict(params, user=user, playlist_id=playlist_id))

    # ---- YouTube: captions ----
    def list_youtube_captions(self, user: str, video_id: str, **params) -> Dict:
        """Caption tracks of a video.

        Required: ``user``, ``video_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-captions
        """
        return self._call("GET", "/uploadposts/youtube/captions", dict(params, user=user, video_id=video_id))

    def upload_youtube_caption(self, user: str, video_id: str, **params) -> Dict:
        """Add a caption track: `file` (local file, stream or Buffer) or `file_url`, plus `language`, `name`, `is_draft`.

        Required: ``user``, ``video_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-captions
        """
        return self._call("POST", "/uploadposts/youtube/captions", dict(params, user=user, video_id=video_id))

    def update_youtube_caption(self, user: str, caption_id: str, **params) -> Dict:
        """Replace a track's file and/or publish a draft (`is_draft: false`).

        Required: ``user``, ``caption_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-captions
        """
        return self._call("PUT", "/uploadposts/youtube/captions/{caption_id}", dict(params, user=user, caption_id=caption_id))

    def download_youtube_caption(self, user: str, caption_id: str, **params) -> Dict:
        """Download a track (`tfmt`: srt, vtt, sbv, scc, ttml; `tlang` to translate). Returns the file's text.

        Required: ``user``, ``caption_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-captions
        """
        return self._call("GET", "/uploadposts/youtube/captions/{caption_id}/download", dict(params, user=user, caption_id=caption_id), raw=True)

    def delete_youtube_caption(self, user: str, caption_id: str, **params) -> Dict:
        """Delete a track (needs `confirm: true`).

        Required: ``user``, ``caption_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-captions
        """
        return self._call("DELETE", "/uploadposts/youtube/captions/{caption_id}", dict(params, user=user, caption_id=caption_id))

    # ---- YouTube: comments inbox ----
    def list_youtube_comments(self, user: str, **params) -> Dict:
        """Comment threads of a video (`video_id`), of the whole channel (`scope: "channel"`) or by `ids`; `moderation_status`, `order`, `search_terms`...

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-comments
        """
        return self._call("GET", "/uploadposts/youtube/comments", dict(params, user=user))

    def list_youtube_comment_replies(self, user: str, **params) -> Dict:
        """Replies to a comment (`parent_id`) or comments by `ids`.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-comments
        """
        return self._call("GET", "/uploadposts/youtube/comments/replies", dict(params, user=user))

    def create_youtube_comment(self, user: str, text: str, **params) -> Dict:
        """Reply to a comment (`parent_id`) or comment on a video (`video_id`); `idempotency_key` optional.

        Required: ``user``, ``text``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-comments
        """
        return self._call("POST", "/uploadposts/youtube/comments", dict(params, user=user, text=text))

    def update_youtube_comment(self, user: str, comment_id: str, **params) -> Dict:
        """Edit your own comment (`text`).

        Required: ``user``, ``comment_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-comments
        """
        return self._call("PATCH", "/uploadposts/youtube/comments/{comment_id}", dict(params, user=user, comment_id=comment_id))

    def delete_youtube_comment(self, user: str, comment_id: str, **params) -> Dict:
        """Delete your own comment (needs `confirm: true`).

        Required: ``user``, ``comment_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-comments
        """
        return self._call("DELETE", "/uploadposts/youtube/comments/{comment_id}", dict(params, user=user, comment_id=comment_id))

    def moderate_youtube_comments(self, user: str, comment_ids: str, status: str, **params) -> Dict:
        """Approve, hold or reject comments of your channel (`rejected` needs `confirm: true`; `ban_author`).

        Required: ``user``, ``comment_ids``, ``status``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-comments
        """
        return self._call("POST", "/uploadposts/youtube/comments/moderate", dict(params, user=user, comment_ids=comment_ids, status=status))

    # ---- YouTube: search and catalogs ----
    def search_youtube(self, user: str, **params) -> Dict:
        """Search videos, channels and playlists (`q`, `for_mine`, `channel_id`, `type`, `order`...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-search-catalogs
        """
        return self._call("GET", "/uploadposts/youtube/search", dict(params, user=user))

    def get_youtube_categories(self, **params) -> Dict:
        """Video categories of a region (`region`, `hl`, `assignable_only`).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-search-catalogs
        """
        return self._call("GET", "/uploadposts/youtube/categories", params)

    def get_youtube_languages(self, **params) -> Dict:
        """Languages YouTube supports (`hl`).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-search-catalogs
        """
        return self._call("GET", "/uploadposts/youtube/languages", params)

    def get_youtube_regions(self, **params) -> Dict:
        """Regions (countries) YouTube supports (`hl`).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-search-catalogs
        """
        return self._call("GET", "/uploadposts/youtube/regions", params)

    def get_youtube_abuse_reasons(self, **params) -> Dict:
        """Reasons for an abuse report (`hl`).

        Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-search-catalogs
        """
        return self._call("GET", "/uploadposts/youtube/abuse-reasons", params)

    # ---- YouTube: subscriptions, ratings, reports and activity ----
    def list_youtube_subscriptions(self, user: str, **params) -> Dict:
        """Channels the connected channel subscribes to (or its subscribers).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel-actions
        """
        return self._call("GET", "/uploadposts/youtube/subscriptions", dict(params, user=user))

    def subscribe_youtube_channel(self, user: str, **params) -> Dict:
        """Subscribe the connected channel to a channel (`channel_id`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel-actions
        """
        return self._call("POST", "/uploadposts/youtube/subscriptions", dict(params, user=user))

    def unsubscribe_youtube_channel(self, user: str, subscription_id: str, **params) -> Dict:
        """Unsubscribe.

        Required: ``user``, ``subscription_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel-actions
        """
        return self._call("DELETE", "/uploadposts/youtube/subscriptions/{subscription_id}", dict(params, user=user, subscription_id=subscription_id))

    def rate_youtube_video(self, user: str, video_id: str, **params) -> Dict:
        """Like, dislike or remove the rating of a video (`rating`: like, dislike, none).

        Required: ``user``, ``video_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel-actions
        """
        return self._call("POST", "/uploadposts/youtube/videos/{video_id}/rate", dict(params, user=user, video_id=video_id))

    def get_youtube_rating(self, user: str, ids: str, **params) -> Dict:
        """The channel's rating of up to 50 videos.

        Required: ``user``, ``ids``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel-actions
        """
        return self._call("GET", "/uploadposts/youtube/videos/rating", dict(params, user=user, ids=ids))

    def report_youtube_video_abuse(self, user: str, video_id: str, reason_id: str, **params) -> Dict:
        """Report a video (needs `confirm: true`; it cannot be withdrawn).

        Required: ``user``, ``video_id``, ``reason_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel-actions
        """
        return self._call("POST", "/uploadposts/youtube/videos/{video_id}/report-abuse", dict(params, user=user, video_id=video_id, reason_id=reason_id))

    def get_youtube_activities(self, user: str, **params) -> Dict:
        """Activity of the channel (uploads, likes, playlist additions...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel-actions
        """
        return self._call("GET", "/uploadposts/youtube/activities", dict(params, user=user))

    # ---- YouTube: channel settings ----
    def get_youtube_channel(self, user: str, **params) -> Dict:
        """Read the connected channel (settings, branding, translations, statistics).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("GET", "/uploadposts/youtube/channel", dict(params, user=user))

    def update_youtube_channel(self, user: str, **params) -> Dict:
        """Change the channel settings or translations (only what you send changes).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("PATCH", "/uploadposts/youtube/channel", dict(params, user=user))

    def lookup_youtube_channel(self, user: str, **params) -> Dict:
        """Public data of any channel (`for_handle`, `channel_id`...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("GET", "/uploadposts/youtube/channel/lookup", dict(params, user=user))

    def set_youtube_channel_banner(self, user: str, **params) -> Dict:
        """Upload and apply the banner: `image` (local file, stream or Buffer) or `image_url`.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("POST", "/uploadposts/youtube/channel/banner", dict(params, user=user))

    def list_youtube_channel_sections(self, user: str, **params) -> Dict:
        """Sections of the channel page.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("GET", "/uploadposts/youtube/channel/sections", dict(params, user=user))

    def create_youtube_channel_section(self, user: str, **params) -> Dict:
        """Create a section.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("POST", "/uploadposts/youtube/channel/sections", dict(params, user=user))

    def update_youtube_channel_section(self, user: str, section_id: str, **params) -> Dict:
        """Edit or move a section.

        Required: ``user``, ``section_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("PATCH", "/uploadposts/youtube/channel/sections/{section_id}", dict(params, user=user, section_id=section_id))

    def delete_youtube_channel_section(self, user: str, section_id: str, **params) -> Dict:
        """Delete a section (needs `confirm: true`).

        Required: ``user``, ``section_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("DELETE", "/uploadposts/youtube/channel/sections/{section_id}", dict(params, user=user, section_id=section_id))

    def set_youtube_watermark(self, user: str, **params) -> Dict:
        """Set the watermark: `image` (local file, stream or Buffer) or `image_url`, `timing_type`, `offset_ms`, `duration_ms` (needs `confirm: true`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("POST", "/uploadposts/youtube/channel/watermark", dict(params, user=user))

    def remove_youtube_watermark(self, user: str, **params) -> Dict:
        """Remove the watermark (needs `confirm: true`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-channel
        """
        return self._call("DELETE", "/uploadposts/youtube/channel/watermark", dict(params, user=user))

    # ---- YouTube: live broadcasts and streams ----
    def list_youtube_broadcasts(self, user: str, **params) -> Dict:
        """List live broadcasts (`status`, `ids`...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("GET", "/uploadposts/youtube/live/broadcasts", dict(params, user=user))

    def create_youtube_broadcast(self, user: str, **params) -> Dict:
        """Create a broadcast (`title`, `scheduled_start_time`, `privacy_status`...).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("POST", "/uploadposts/youtube/live/broadcasts", dict(params, user=user))

    def get_youtube_broadcast(self, user: str, broadcast_id: str, **params) -> Dict:
        """One broadcast.

        Required: ``user``, ``broadcast_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("GET", "/uploadposts/youtube/live/broadcasts/{broadcast_id}", dict(params, user=user, broadcast_id=broadcast_id))

    def update_youtube_broadcast(self, user: str, broadcast_id: str, **params) -> Dict:
        """Edit a broadcast.

        Required: ``user``, ``broadcast_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("PATCH", "/uploadposts/youtube/live/broadcasts/{broadcast_id}", dict(params, user=user, broadcast_id=broadcast_id))

    def delete_youtube_broadcast(self, user: str, broadcast_id: str, **params) -> Dict:
        """Delete a broadcast (needs `confirm: true`).

        Required: ``user``, ``broadcast_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("DELETE", "/uploadposts/youtube/live/broadcasts/{broadcast_id}", dict(params, user=user, broadcast_id=broadcast_id))

    def bind_youtube_broadcast(self, user: str, broadcast_id: str, **params) -> Dict:
        """Bind a stream to the broadcast (`stream_id`), or unbind it.

        Required: ``user``, ``broadcast_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("POST", "/uploadposts/youtube/live/broadcasts/{broadcast_id}/bind", dict(params, user=user, broadcast_id=broadcast_id))

    def transition_youtube_broadcast(self, user: str, broadcast_id: str, status: str, **params) -> Dict:
        """Go `testing`, `live` or `complete` (`live` and `complete` need `confirm: true`).

        Required: ``user``, ``broadcast_id``, ``status``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("POST", "/uploadposts/youtube/live/broadcasts/{broadcast_id}/transition", dict(params, user=user, broadcast_id=broadcast_id, status=status))

    def insert_youtube_cuepoint(self, user: str, broadcast_id: str, **params) -> Dict:
        """Insert an ad break.

        Required: ``user``, ``broadcast_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("POST", "/uploadposts/youtube/live/broadcasts/{broadcast_id}/cuepoint", dict(params, user=user, broadcast_id=broadcast_id))

    def list_youtube_streams(self, user: str, **params) -> Dict:
        """List streams.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("GET", "/uploadposts/youtube/live/streams", dict(params, user=user))

    def create_youtube_stream(self, user: str, **params) -> Dict:
        """Create a stream (its key is a secret).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("POST", "/uploadposts/youtube/live/streams", dict(params, user=user))

    def get_youtube_stream(self, user: str, stream_id: str, **params) -> Dict:
        """One stream.

        Required: ``user``, ``stream_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("GET", "/uploadposts/youtube/live/streams/{stream_id}", dict(params, user=user, stream_id=stream_id))

    def update_youtube_stream(self, user: str, stream_id: str, **params) -> Dict:
        """Edit a stream.

        Required: ``user``, ``stream_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("PATCH", "/uploadposts/youtube/live/streams/{stream_id}", dict(params, user=user, stream_id=stream_id))

    def delete_youtube_stream(self, user: str, stream_id: str, **params) -> Dict:
        """Delete a stream (needs `confirm: true`; encoders using its key stop).

        Required: ``user``, ``stream_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live
        """
        return self._call("DELETE", "/uploadposts/youtube/live/streams/{stream_id}", dict(params, user=user, stream_id=stream_id))

    # ---- YouTube: live chat, polls and moderation ----
    def get_youtube_live_chat(self, user: str, **params) -> Dict:
        """Read the live chat (`broadcast_id` or `live_chat_id`, `page_token`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("GET", "/uploadposts/youtube/live/chat", dict(params, user=user))

    def send_youtube_live_chat_message(self, user: str, **params) -> Dict:
        """Post a message or a poll in the live chat (`idempotency_key` optional).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("POST", "/uploadposts/youtube/live/chat", dict(params, user=user))

    def close_youtube_live_chat_poll(self, user: str, message_id: str, **params) -> Dict:
        """Close a poll.

        Required: ``user``, ``message_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("POST", "/uploadposts/youtube/live/chat/polls/{message_id}/close", dict(params, user=user, message_id=message_id))

    def delete_youtube_live_chat_message(self, user: str, message_id: str, **params) -> Dict:
        """Delete a chat message (needs `confirm: true`).

        Required: ``user``, ``message_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("DELETE", "/uploadposts/youtube/live/chat/messages/{message_id}", dict(params, user=user, message_id=message_id))

    def list_youtube_live_moderators(self, user: str, **params) -> Dict:
        """Moderators of the live chat.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("GET", "/uploadposts/youtube/live/moderators", dict(params, user=user))

    def add_youtube_live_moderator(self, user: str, **params) -> Dict:
        """Add a moderator (`channel_id`).

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("POST", "/uploadposts/youtube/live/moderators", dict(params, user=user))

    def remove_youtube_live_moderator(self, user: str, moderator_id: str, **params) -> Dict:
        """Remove a moderator (the `id` from the list; needs `confirm: true`).

        Required: ``user``, ``moderator_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("DELETE", "/uploadposts/youtube/live/moderators/{moderator_id}", dict(params, user=user, moderator_id=moderator_id))

    def ban_youtube_live_chat_user(self, user: str, channel_id: str, type: str, **params) -> Dict:
        """Ban a user from the chat (`permanent` or `temporary` with `ban_duration_seconds`; needs `confirm: true`).

        Required: ``user``, ``channel_id``, ``type``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("POST", "/uploadposts/youtube/live/bans", dict(params, user=user, channel_id=channel_id, type=type))

    def unban_youtube_live_chat_user(self, user: str, ban_id: str, **params) -> Dict:
        """Lift a ban.

        Required: ``user``, ``ban_id``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("DELETE", "/uploadposts/youtube/live/bans/{ban_id}", dict(params, user=user, ban_id=ban_id))

    def list_youtube_super_chats(self, user: str, **params) -> Dict:
        """Super Chats and Super Stickers received.

        Required: ``user``. Any other API field goes in ``**params``
        with its API name. Docs: https://docs.upload-post.com/api/youtube-live-chat
        """
        return self._call("GET", "/uploadposts/youtube/live/super-chats", dict(params, user=user))

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

    def resolve_linkedin_organization(self, user: str, url: str) -> Dict:
        """
        Turn any LinkedIn company Page into the ``urn`` and exact ``name`` a
        mention needs.

        LinkedIn only links a company mention (``@[Name](urn:li:organization:ID)``)
        when the name matches the Page's full name exactly, capitals included,
        or it is published as plain text. This works for any company, showcase
        or school Page, not only the ones you administer. Paste the returned
        ``mention`` into the post text as is. Cached lookups answer with
        ``cached: True``; new ones count against 60 per hour per account.

        People cannot be resolved: LinkedIn does not let apps look members up,
        and person ids are specific to each LinkedIn app.

        Errors (``UploadPostError.error_code``): 400 ``invalid_parameter``,
        400 ``linkedin_person_not_resolvable`` (a ``/in/`` URL or
        ``urn:li:person``), 401 ``linkedin_reauth_required``, 403
        ``linkedin_permission_missing`` (reconnect LinkedIn approving the
        company Page permission), 404 ``organization_not_found``, 429
        ``rate_limited`` / ``linkedin_rate_limited``, 502 ``linkedin_unavailable``.

        Args:
            user: Profile username whose LinkedIn connection makes the lookup.
            url: The Page URL (``https://www.linkedin.com/company/<vanity>/``,
                also ``/showcase/`` and ``/school/``), the vanity name (with or
                without ``@``), the numeric id or ``urn:li:organization:ID``.

        Returns:
            ``{"success": True, "urn", "id", "name", "vanity_name", "mention",
            "cached"}``.
        """
        return self._request(
            "/uploadposts/linkedin/resolve-organization", "GET",
            params={"user": user, "url": url},
        )

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

    # ==================== Comments ====================

    def get_post_comments(
        self,
        user: str,
        platform: str = "instagram",
        post_id: Optional[str] = None,
        post_url: Optional[str] = None,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        comment_id: Optional[str] = None
    ) -> Dict:
        """
        Get comments on a post, or the replies hanging from one of them.

        Pass comment_id to read that comment's replies instead of the post's
        top-level comments. It is the same question - what was said here - so it
        is the same endpoint with one more parameter, not a method per platform.

        Replies (``comment_id``) work on TikTok, Threads, YouTube, Instagram,
        Facebook and LinkedIn (company Page posts only); X and Bluesky answer
        400 ``platform_not_supported``. ``post_id`` is still required with
        ``comment_id``. Per platform:

        - Instagram: the numeric comment id from the listing.
        - Facebook: the ``{post}_{comment}`` id from the listing; ``post_id``
          (``{page_id}_{post_id}``) picks the Page whose token reads it.
        - LinkedIn: prefer the ``comment_urn`` from the listing
          (``urn:li:comment:(urn:li:activity:...,...)``, one LinkedIn call). A
          bare id is looked up among the post's first 250 comments, else 404
          ``linkedin_comment_not_found``. ``after`` is a number (the offset in
          ``pagination.next_cursor``).

        Error codes (``UploadPostError.error_code``): 400
        ``invalid_comment_id`` (wrong format, checked before calling the
        network), 400 ``invalid_cursor`` (LinkedIn), 404 ``comment_not_found``
        (Instagram/Facebook do not know the comment; one with no replies is a
        200 with an empty list), 404 ``linkedin_comment_not_found``, 403
        ``linkedin_personal_not_supported`` (personal LinkedIn profile), 403
        ``linkedin_page_access_denied`` (the member lost the Page admin role).

        On TikTok this needs the `comments` capability on the connection (see
        `capabilities` on the TikTok account returned by list_users()). TikTok
        grants it at connect time, so an account connected earlier has to be
        reconnected.

        Args:
            user: Profile username.
            platform: Platform name (instagram, facebook, youtube, linkedin,
                tiktok, threads, x, bluesky...).
            post_id: Post/media ID (provide post_id or post_url). Required on
                TikTok, which has no post URL lookup. LinkedIn: the post URN.
            post_url: Full post URL (provide post_id or post_url).
            limit: Maximum number of comments to return (1-50). LinkedIn's
                top-level listing ignores it; LinkedIn replies apply it.
            after: Pagination cursor (``pagination.next_cursor``) for the next
                page of comments.
            comment_id: Read the replies to this comment instead of the post's
                top-level comments. Keyword-only in practice: it goes last so
                the existing positional order keeps working.

        Returns:
            Comments data including comment IDs, text, timestamps, and user
            info, plus ``pagination``.
        """
        params = {"platform": platform, "user": user}
        if post_id:
            params["post_id"] = post_id
        if post_url:
            params["post_url"] = post_url
        if comment_id:
            params["comment_id"] = comment_id
        if limit is not None:
            params["limit"] = limit
        if after is not None:
            params["after"] = after
        return self._request("/uploadposts/comments", "GET", params=params)

    def reply_to_comment(
        self,
        user: str,
        comment_id: str,
        message: str,
        buttons: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Send a private reply (DM) to the author of an Instagram comment.

        Args:
            user: Profile username.
            comment_id: Comment ID from get_post_comments.
            message: Reply message text.
            buttons: Optional list of web_url buttons (max 3) rendered in the Instagram
                DM. Each item is a dict like {"title": "Open", "url": "https://..."}.

        Returns:
            Reply result with recipient_id and message_id.
        """
        json_data = {
            "platform": "instagram",
            "user": user,
            "comment_id": comment_id,
            "message": message
        }
        if buttons is not None:
            json_data["buttons"] = buttons
        return self._request("/uploadposts/comments/reply", "POST", json_data=json_data)

    def public_reply_to_comment(
        self,
        user: str,
        comment_id: str,
        message: str
    ) -> Dict:
        """
        Post a public reply to an Instagram comment (visible under the original comment).

        Args:
            user: Profile username.
            comment_id: Comment ID from get_post_comments.
            message: Reply message text.

        Returns:
            Reply result with the new comment ID.
        """
        return self._request("/uploadposts/comments/public-reply", "POST", json_data={
            "platform": "instagram",
            "user": user,
            "comment_id": comment_id,
            "message": message
        })

    def create_comment(
        self,
        user: str,
        platform: str,
        message: str,
        post_id: Optional[str] = None,
        post_url: Optional[str] = None,
        comment_id: Optional[str] = None
    ) -> Dict:
        """
        Create a comment on a post, or reply to an existing comment.

        On TikTok this needs the `comments` capability on the connection (see
        `capabilities` on the TikTok account returned by list_users()). TikTok
        grants it at connect time, so an account connected earlier has to be
        reconnected.

        Args:
            user: Profile username.
            platform: Platform name (instagram, facebook, youtube, linkedin,
                tiktok).
            message: Comment text.
            post_id: Post/media ID to comment on.
            post_url: Full post URL to comment on.
            comment_id: Existing comment ID to reply to.

        One of post_id, post_url or comment_id is required.

        Returns:
            Creation result with the new comment ID.
        """
        json_data = {
            "platform": platform,
            "user": user,
            "message": message
        }
        if post_id is not None:
            json_data["post_id"] = post_id
        if post_url is not None:
            json_data["post_url"] = post_url
        if comment_id is not None:
            json_data["comment_id"] = comment_id
        return self._request("/uploadposts/comments/create", "POST", json_data=json_data)

    def delete_comment(
        self,
        user: str,
        platform: str,
        comment_id: str,
        post_id: Optional[str] = None
    ) -> Dict:
        """
        Delete a comment on a post.

        On TikTok this needs the `comments` capability on the connection (see
        `capabilities` on the TikTok account returned by list_users()). TikTok
        grants it at connect time, so an account connected earlier has to be
        reconnected.

        Args:
            user: Profile username.
            platform: Platform name (instagram, facebook, youtube, linkedin,
                tiktok).
            comment_id: Comment ID to delete.
            post_id: Post URN (required for LinkedIn).

        Returns:
            Deletion result.
        """
        json_data = {
            "platform": platform,
            "user": user,
            "comment_id": comment_id
        }
        if post_id is not None:
            json_data["post_id"] = post_id
        return self._request("/uploadposts/comments/delete", "DELETE", json_data=json_data)

    def comment_action(
        self,
        user: str,
        platform: str,
        comment_id: str,
        action: str,
        post_id: Optional[str] = None
    ) -> Dict:
        """
        Moderate a comment: hide, like or pin it - and undo any of the three.

        One method for every platform, because it is one question: do this to
        that comment. Each action carries its own inverse:

            action              post_id
            hide / unhide       required
            like / unlike       not sent (the platform likes the comment alone)
            pin / unpin         required

        On TikTok this needs the `comments` capability on the connection (see
        `capabilities` on the TikTok account returned by list_users()). TikTok
        grants it at connect time, so an account connected earlier has to be
        reconnected.

        Args:
            user: Profile username.
            platform: Platform name (tiktok).
            comment_id: Comment to act on.
            action: What to do: "hide", "unhide", "like", "unlike", "pin" or
                "unpin".
            post_id: Native post ID. Required for hide/unhide and pin/unpin;
                never sent for like/unlike.

        Returns:
            {"success": True, "platform": ..., "action": ...,
             "comment_id": ..., "result": {...}}
        """
        json_data: Dict[str, Any] = {
            "platform": platform,
            "user": user,
            "comment_id": comment_id,
            "action": action,
        }
        # Liking takes the comment alone; hiding and pinning need the post too.
        if action not in ("like", "unlike") and post_id:
            json_data["post_id"] = post_id
        return self._request(
            "/uploadposts/comments/action", "POST", json_data=json_data
        )

    # ==================== Direct messages ====================

    def send_dm(
        self,
        user: str,
        platform: str,
        recipient_id: Optional[str] = None,
        message: Optional[str] = None,
        conversation_id: Optional[str] = None,
        attachments: Optional[Union[Dict, List[Dict]]] = None,
        reply_to: Optional[str] = None,
        sender_action: Optional[str] = None,
        message_id: Optional[str] = None,
        reaction: Optional[Union[str, Dict]] = None,
        buttons: Optional[List[Dict]] = None,
        quick_replies: Optional[List[Dict]] = None,
        **fields: Any,
    ) -> Dict:
        """
        Send a direct message, or a DM action (mark read, react...).

        One method for every messaging platform: ``instagram``, ``facebook``
        (Messenger), ``whatsapp`` and ``bluesky``. Instagram and Messenger only
        let you write inside the 24-hour window the person opened by writing to
        you. Messages count against the plan's daily DM allowance; sender
        actions do not.

        Telegram (``platform="telegram"``): sends from your own connected bot
        to a person who started it (``recipient_id`` = their user id), with
        text, media, buttons (``reply_markup``) and sender actions. Reading
        Telegram conversations needs update receiving, not available yet.

        Bluesky:

        - ``recipient_id`` is a handle (``alice.bsky.social`` or ``@alice...``),
          a DID (``did:plc:...``) or a bsky.app profile link. Or pass
          ``conversation_id`` instead (also for group conversations).
        - ``message`` up to 1000 characters (as Bluesky counts them); links,
          ``#hashtags`` and ``@handle`` mentions become clickable.
        - ``attachments``: one Bluesky post to share,
          ``{"type": "post", "url": "https://bsky.app/profile/<handle>/post/<id>"}``.
        - ``reply_to``: id of a message in the same conversation.
        - ``sender_action``: ``mark_seen``/``mark_read`` (up to ``message_id``),
          ``react``/``unreact`` (``reaction`` emoji on ``message_id``),
          ``delete`` (for you only), ``accept`` (a message request), ``mute``,
          ``unmute``, ``leave``.
        - Needs an app password created with "Allow access to your direct
          messages"; otherwise 403 ``bluesky_dm_scope_missing``. Other codes:
          403 ``bluesky_recipient_unavailable`` (with ``reason``), 404
          ``bluesky_recipient_not_found`` / ``bluesky_conversation_not_found`` /
          ``bluesky_post_not_found``, 400 ``bluesky_message_too_long`` /
          ``bluesky_rejected``, 401 ``bluesky_reauth_required``, 429
          ``bluesky_rate_limited`` (``retry_after``), 502/503
          ``bluesky_chat_unavailable`` / ``bluesky_edge_rate_limited``.
        - 504 ``bluesky_send_unconfirmed``: the DM may have gone out. Do NOT
          retry automatically; read the conversation first
          (``error.response["conversation_id"]``).

        Buttons, quick replies, templates and typing indicators do not exist in
        Bluesky chat and are refused with 400.

        Args:
            user: Profile username.
            platform: ``instagram``, ``facebook``, ``whatsapp`` or ``bluesky``.
            recipient_id: Who to write to (Instagram/Messenger scoped id,
                WhatsApp phone number, Bluesky handle or DID).
            message: The text. Optional with a sender action, a shared post or
                another rich body.
            conversation_id: Bluesky: send to this conversation.
            attachments: Attachment(s); on Bluesky one shared post.
            reply_to: Id of the message to reply to.
            sender_action: Platform action instead of a message (Instagram:
                ``mark_seen``, ``typing_on``, ``typing_off``, ``react``,
                ``unreact``; WhatsApp: ``mark_read``, ``typing_on``; Bluesky:
                see above).
            message_id: Message the action applies to.
            reaction: Emoji for a reaction (WhatsApp: a dict with
                ``message_id`` and ``emoji``).
            buttons: Up to 3 ``{"title", "url"}`` link buttons (Instagram,
                Messenger).
            quick_replies: Quick replies (Instagram, Messenger).
            **fields: Any other body field of ``/dms/send``, sent as is
                (``template``, ``tag``, ``generic_template``, ``location``,
                ``contacts``, ``list``, ``cta_url``, ``header``, ``footer``,
                ``page_id``...). ``None`` values are dropped.

        Returns:
            On Bluesky ``{"success": True, "platform": "bluesky",
            "recipient_id", "conversation_id", "message_id", "created_time",
            "message"}``; the other platforms return their message id.
        """
        body: Dict[str, Any] = {"platform": platform, "user": user}
        for key, value in (("recipient_id", recipient_id), ("message", message),
                           ("conversation_id", conversation_id),
                           ("attachments", attachments), ("reply_to", reply_to),
                           ("sender_action", sender_action),
                           ("message_id", message_id), ("reaction", reaction),
                           ("buttons", buttons), ("quick_replies", quick_replies)):
            if value is not None:
                body[key] = value
        for key, value in fields.items():
            if value is not None:
                body[key] = value
        return self._request("/uploadposts/dms/send", "POST", json_data=body)

    def get_dm_conversations(
        self,
        user: str,
        platform: str,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        since: Optional[Union[str, int]] = None,
        participant_id: Optional[str] = None,
        messages_limit: Optional[int] = None,
        conversation_id: Optional[str] = None,
        messages_cursor: Optional[str] = None,
        status: Optional[str] = None,
        read_state: Optional[str] = None,
        **params: Any,
    ) -> Dict:
        """
        List DM conversations, newest first, with their latest messages.

        Same shape on every platform: ``conversations[]`` with
        ``participants.data`` (the connected account flagged ``is_me``) and
        ``messages.data``, plus ``pagination``.

        Bluesky adds per conversation ``status`` (``accepted``/``request``),
        ``unread_count``, ``muted``, ``kind`` (``direct``/``group``) and
        ``account``; per message ``direction`` (``in``/``out``), ``type``,
        ``attachments`` (shared post), ``reactions`` and ``reply_to``. It
        returns at most 25 conversations per page; if a page takes too long,
        the rest come with only their latest message and
        ``messages_truncated: True`` (read them with ``conversation_id``).

        Args:
            user: Profile username.
            platform: ``instagram``, ``facebook``, ``whatsapp`` or ``bluesky``.
            limit: Conversations per page (1-50; Bluesky caps at 25).
            cursor: ``pagination.next_cursor`` from the previous page.
            since: Only conversations active since this Unix timestamp or ISO
                8601 date.
            participant_id: Only the 1:1 conversation with this person
                (Bluesky: handle or DID; never created by reading).
            messages_limit: Messages per conversation.
            conversation_id: Bluesky: only this conversation.
            messages_cursor: Bluesky, with ``conversation_id``: older messages
                (``messages.paging.next_cursor``).
            status: Bluesky: ``request`` or ``accepted``.
            read_state: Bluesky: ``unread`` for conversations with unread
                messages only.
            **params: Any other query parameter, sent as is (e.g.
                ``facebook_page_id``). ``None`` values are dropped.

        Returns:
            ``{"success": True, "conversations": [...], "pagination": {...}}``.
        """
        query: Dict[str, Any] = {"platform": platform, "user": user}
        for key, value in (("limit", limit), ("cursor", cursor), ("since", since),
                           ("participant_id", participant_id),
                           ("messages_limit", messages_limit),
                           ("conversation_id", conversation_id),
                           ("messages_cursor", messages_cursor),
                           ("status", status), ("read_state", read_state)):
            if value is not None:
                query[key] = value
        for key, value in params.items():
            if value is not None:
                query[key] = value
        return self._request("/uploadposts/dms/conversations", "GET", params=query)

    # ==================== AutoDM: per-post monitors ====================

    def start_autodm(
        self,
        profile_username: str,
        reply_message: str,
        platform: Optional[str] = None,
        post_url: Optional[str] = None,
        post_id: Optional[str] = None,
        reply_messages: Optional[List[str]] = None,
        buttons: Optional[List[Dict[str, str]]] = None,
        monitoring_interval: Optional[int] = None,
        trigger_keywords: Optional[Union[str, List[str]]] = None,
    ) -> Dict:
        """
        Start a per-post monitor: it answers every new comment on one post,
        with a private DM on Instagram or a public reply on TikTok, YouTube,
        Facebook, Threads and Bluesky. Monitors stop after 15 days and a
        profile can create 2 per day. For the whole Instagram account use
        create_autodm_rule() instead.

        Args:
            profile_username: Profile username.
            reply_message: DM text (Instagram) or public reply.
            platform: instagram (default), tiktok, youtube, facebook, threads
                or bluesky.
            post_url: Post URL (required on Instagram).
            post_id: Post id on the other platforms (or post_url).
            reply_messages: Public replies only: up to 5 texts, rotated.
            buttons: Instagram only: up to 3 ``{"title", "url"}`` buttons.
            monitoring_interval: Minutes between checks (min and default 15).
            trigger_keywords: Only answer comments containing one of these.

        Returns:
            Monitor result with ``monitor_id``.
        """
        body = {"profile_username": profile_username, "reply_message": reply_message}
        for key, value in (
            ("platform", platform), ("post_url", post_url), ("post_id", post_id),
            ("reply_messages", reply_messages), ("buttons", buttons),
            ("monitoring_interval", monitoring_interval), ("trigger_keywords", trigger_keywords),
        ):
            if value is not None:
                body[key] = value
        return self._request("/uploadposts/autodms/start", "POST", json_data=body)

    def _autodm_monitor_action(self, action: str, monitor_id: str) -> Dict:
        return self._request(f"/uploadposts/autodms/{action}", "POST",
                             json_data={"monitor_id": monitor_id})

    def stop_autodm(self, monitor_id: str) -> Dict:
        """Stop a per-post monitor (it stays listed with ``include_inactive``)."""
        return self._autodm_monitor_action("stop", monitor_id)

    def pause_autodm(self, monitor_id: str) -> Dict:
        """Pause a per-post monitor."""
        return self._autodm_monitor_action("pause", monitor_id)

    def resume_autodm(self, monitor_id: str) -> Dict:
        """Resume a paused per-post monitor."""
        return self._autodm_monitor_action("resume", monitor_id)

    def delete_autodm(self, monitor_id: str) -> Dict:
        """Delete a per-post monitor."""
        return self._autodm_monitor_action("delete", monitor_id)

    def get_autodm_status(self, include_inactive: Optional[bool] = None) -> Dict:
        """List per-post monitors and their stats (``include_inactive`` adds stopped/expired ones)."""
        params = {}
        if include_inactive is not None:
            params["include_inactive"] = str(bool(include_inactive)).lower()
        return self._request("/uploadposts/autodms/status", "GET", params=params)

    def get_autodm_logs(self, monitor_id: str) -> Dict:
        """Get the log of one per-post monitor."""
        return self._request("/uploadposts/autodms/logs", "GET", params={"monitor_id": monitor_id})

    # ==================== AutoDM: account-wide rules (Instagram) ====================

    def create_autodm_rule(
        self,
        profile_username: str,
        reply_message: str,
        triggers: Optional[List[str]] = None,
        trigger_keywords: Optional[List[str]] = None,
        buttons: Optional[List[Dict]] = None,
        per_user_cooldown_hours: Optional[int] = None,
    ) -> Dict:
        """
        Create an account-wide AutoDM rule for the profile's Instagram account.

        Unlike a per-post monitor, a rule covers every post and reel of the
        account (present and future), never expires and does not count towards
        the 2-monitors-per-day limit. Up to 10 rules per Instagram account. It
        works only from Meta's real-time notifications: creating it subscribes
        the account; if Meta refuses, nothing is created (502
        ``webhook_subscription_failed``: reconnect Instagram).

        Triggers:

        - ``comment`` (default): a top-level comment on any post -> private
          reply. A post with its own monitor is answered by that monitor only.
        - ``story_reply``: someone replies to one of your stories -> DM.
        - ``story_mention``: someone mentions you in their story -> DM.
        - ``dm_keyword``: a DM containing one of ``trigger_keywords`` -> DM
          (requires ``trigger_keywords``).

        Pace: at most 25 DMs per account every 15 minutes plus the plan's daily
        DM allowance; what does not fit is queued for up to 24 hours.

        Errors (``UploadPostError.error_code``): 400 (invalid fields,
        ``reconnect_required``), 409 ``duplicate_rule`` / ``rule_limit_reached``
        / ``rule_creation_in_progress``, 502 ``webhook_subscription_failed``,
        503 ``account_rules_disabled``.

        Args:
            profile_username: Profile with the Instagram account connected.
            reply_message: The DM text (max 1,000 characters; 640 with buttons).
            triggers: Any of ``comment``, ``story_reply``, ``story_mention``,
                ``dm_keyword``. Default ``["comment"]``.
            trigger_keywords: Up to 20; only events whose text contains one
                fire the rule (case- and accent-insensitive). Not applied to
                ``story_mention``. Omit for no filter; blank keywords are
                rejected.
            buttons: Up to 3 ``{"title", "url"}`` link buttons.
            per_user_cooldown_hours: The same person gets at most one DM from
                this rule in this many hours (whole number 0-720, default 24).
                For story replies, story mentions and keyword DMs it is never
                less than 24 (``message_cooldown_hours`` in the response).

        Returns:
            ``{"success": True, "rule": {...}}`` with ``rule_id``, ``status``,
            ``stats``, ``pending`` and ``webhook`` (``subscribed``,
            ``receiving_events``, ``last_event_at``, ``hint``, ``error``).
        """
        body: Dict[str, Any] = {
            "profile_username": profile_username,
            "reply_message": reply_message,
        }
        if triggers is not None:
            body["triggers"] = triggers
        if trigger_keywords is not None:
            body["trigger_keywords"] = trigger_keywords
        if buttons is not None:
            body["buttons"] = buttons
        if per_user_cooldown_hours is not None:
            body["per_user_cooldown_hours"] = per_user_cooldown_hours
        return self._request("/uploadposts/autodms/rules", "POST", json_data=body)

    def list_autodm_rules(self, profile_username: Optional[str] = None) -> Dict:
        """
        List the account-wide AutoDM rules, with their webhook status.

        ``status`` is ``active``, ``paused``, ``reconnect_required``,
        ``stopped`` (with ``stop_reason``: ``account_moved``,
        ``account_disconnected``, ``profile_unlinked``, ``profile_deleted``,
        ``user_missing``) or ``disabled``. Check ``webhook.receiving_events``
        and ``webhook.hint``: a rule only acts on notifications Meta delivers.

        Args:
            profile_username: Only the rules of this profile.

        Returns:
            ``{"success": True, "enabled": True, "rules": [...], "total": N}``.
        """
        params = {"profile_username": profile_username} if profile_username else None
        return self._request("/uploadposts/autodms/rules", "GET", params=params)

    def pause_autodm_rule(self, rule_id: str) -> Dict:
        """
        Pause an account-wide AutoDM rule (it answers nothing while paused).

        Args:
            rule_id: ``rule_id`` from create_autodm_rule / list_autodm_rules.

        Returns:
            ``{"success": True, "message": "Rule paused", "rule_id": ...}``.
        """
        return self._request("/uploadposts/autodms/rules/pause", "POST",
                             json_data={"rule_id": rule_id})

    def resume_autodm_rule(self, rule_id: str) -> Dict:
        """
        Resume a paused (or stopped) account-wide AutoDM rule.

        Subscribes the account to Meta's notifications again if needed (502
        ``webhook_subscription_failed`` as on create). A stopped rule whose
        Instagram account is no longer on its profile answers 409
        ``rule_stopped`` with ``stop_reason``.

        Args:
            rule_id: ``rule_id`` of the rule.

        Returns:
            ``{"success": True, "message": "Rule resumed", "rule_id": ...}``.
        """
        return self._request("/uploadposts/autodms/rules/resume", "POST",
                             json_data={"rule_id": rule_id})

    def delete_autodm_rule(self, rule_id: str) -> Dict:
        """
        Delete an account-wide AutoDM rule and its queued events.

        Args:
            rule_id: ``rule_id`` of the rule.

        Returns:
            ``{"success": True, "message": "Rule deleted", "rule_id": ...}``.
        """
        return self._request("/uploadposts/autodms/rules/delete", "POST",
                             json_data={"rule_id": rule_id})

    # ==================== TikTok ====================

    def get_tiktok_trending_music(
        self,
        profile: str,
        genre: Optional[str] = None,
        country_code: Optional[str] = None,
        date_range: Optional[str] = None
    ) -> Dict:
        """
        Get trending tracks from the TikTok Commercial Music Library.

        Available on connections that declare the `music` capability (see
        `capabilities` on the TikTok account returned by list_users()). The
        returned track 'id' is what you pass as 'tiktok_music_id' on an upload
        - not 'commercial_music_id', which TikTok rejects on public posts.

        Args:
            profile: Profile username.
            genre: Genre filter (e.g. "ALL", "POP"). Defaults to ALL upstream.
            country_code: ISO country code. Defaults to US upstream.
            date_range: Trending window: "1DAY", "7DAY", "30DAY" or "90DAY".
                        Defaults to 7DAY upstream.

        Returns:
            Trending tracks.
        """
        params: Dict[str, Any] = {"profile": profile}
        if genre:
            params["genre"] = genre
        if country_code:
            params["country_code"] = country_code
        if date_range:
            params["date_range"] = date_range
        return self._request("/uploadposts/tiktok/music/trending", "GET", params=params)

    def search_tiktok_music(
        self,
        profile: str,
        q: Optional[str] = None,
        genre: Optional[str] = None,
        country_code: Optional[str] = None,
        date_range: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Search the TikTok Commercial Music Library by song title or artist.

        TikTok itself has no music search endpoint - its only catalogue read is
        the trending chart for a genre/country/period. Upload-Post caches those
        charts and matches your text against them, so this searches the trending
        charts rather than TikTok's entire catalogue. Matching is case- and
        accent-insensitive and every word must match.

        Returns the same track objects as get_tiktok_trending_music(), so the
        'id' is again what you pass as 'tiktok_music_id' on an upload.

        Args:
            profile: Profile username.
            q: Text to match against titles and artists (max 80 characters).
               Omit it to get the chart in trending order.
            genre: Genre filter (e.g. "ALL", "POP"). Defaults to ALL upstream.
            country_code: ISO country code choosing which chart is searched.
                          Defaults to US upstream.
            date_range: Chart window: "1DAY", "7DAY", "30DAY" or "90DAY".
                        Defaults to 7DAY upstream.
            limit: Maximum tracks to return (capped at 100 upstream).

        Returns:
            Matching tracks, plus a 'catalog' block describing how many tracks
            the search actually ran against.
        """
        params: Dict[str, Any] = {"profile": profile}
        if q:
            params["q"] = q
        if genre:
            params["genre"] = genre
        if country_code:
            params["country_code"] = country_code
        if date_range:
            params["date_range"] = date_range
        if limit is not None:
            params["limit"] = limit
        return self._request("/uploadposts/tiktok/music/search", "GET", params=params)

    def get_tiktok_publishing_settings(self, profile: str) -> Dict:
        """
        Get what the connected TikTok account is allowed to publish.

        The point of this call is 'privacy_level_options': TikTok narrows the
        four privacy values per account (a private account has no
        PUBLIC_TO_EVERYONE), and sending one the account does not have fails the
        upload with error_code="tiktok_privacy_unavailable". Ask here to offer
        only the values that will work, instead of the full enum.

        Args:
            profile: Profile username.

        Returns:
            'privacy_level_options', 'max_video_post_duration_sec' and the
            account's comment/duet/stitch switches.
        """
        return self._request(
            "/uploadposts/tiktok/settings", "GET", params={"profile": profile}
        )

    def get_tiktok_locations(self, profile: str, query: str) -> Dict:
        """
        Search TikTok locations (places) to tag on a post.

        Available on connections that declare the `location` capability (see
        `capabilities` on the TikTok account returned by list_users()). TikTok
        requires the id and the name together, so pass the returned
        'location_id' as 'tiktok_location_id' and 'location_name' as
        'tiktok_location_name' on the upload.

        Args:
            profile: Profile username.
            query: Search query (max 100 characters).

        Returns:
            Matching locations (up to 20).
        """
        return self._request(
            "/uploadposts/tiktok/locations",
            "GET",
            params={"profile": profile, "q": query}
        )

    # ==================== Google Business ====================

    def get_google_business_locations(self, profile: Optional[str] = None) -> Dict:
        """
        Get Google Business Profile locations for a connected account.

        Args:
            profile: Profile username.

        Returns:
            List of Google Business locations.
        """
        params = {"profile": profile} if profile else None
        return self._request("/uploadposts/google-business/locations", "GET", params=params)

    def select_google_business_location(self, location_id: str, profile: Optional[str] = None) -> Dict:
        """
        Select a specific Google Business Profile location for a profile.

        Args:
            location_id: The location ID to select (e.g. "accounts/123/locations/456").
            profile: Profile username.

        Returns:
            Selection result with google_business_id and display_name.
        """
        # The API pins a location per profile (POST /users/google-business-location);
        # the old /google-business/locations/select route never existed.
        if not profile:
            raise UploadPostError(
                "select_google_business_location needs the profile: pass "
                "gbp_location_id on the upload, or pin_google_business_location(profile, location_id)."
            )
        return self.pin_google_business_location(profile, location_id)

    # ==================== Generated from the OpenAPI spec ====================
    #
    # One method per API operation that has no hand-written method above. Written
    # by codegen/generate.py from codegen/openapi.json: do not edit by hand, edit
    # the spec (or codegen/sdk-map.json) and run `python3 codegen/generate.py`.

    def _op(self, operation_id: str, params: Dict, **args) -> Any:
        """Run one operation of the OpenAPI spec (behind every generated method).

        Keywords go by their API name: path parameters into the URL, query
        parameters into the query string and the rest into the JSON body. A file
        field given as a local path, bytes or an open file turns the body into
        multipart/form-data. ``None`` values are not sent.
        """
        method, route, meta = self._OPENAPI_OPERATIONS[operation_id]
        body = {k: v for k, v in params.items() if v is not None}
        body.update({k: v for k, v in args.items() if v is not None})
        headers = {}
        if meta.get("bearer"):
            token = body.pop("token", None)
            if not token:
                raise UploadPostError("token (the profile JWT) is required")
            headers["Authorization"] = f"Bearer {token}"
        endpoint = route
        for name in re.findall(r"\{(\w+)\}", route):
            value = body.pop(name, None)
            if value is None or value == "":
                raise UploadPostError(f"{name} is required")
            endpoint = endpoint.replace("{%s}" % name, quote(str(value), safe=""))
        query = {}
        for key in list(body):
            if method == "GET" or key in meta.get("q", ()) or (method == "DELETE" and not meta.get("b")):
                query[key] = self._query_value(body.pop(key))

        kwargs: Dict[str, Any] = {"params": query or None}
        if headers:
            kwargs["headers"] = headers
        opened: List = []
        try:
            if method != "GET" and (body or meta.get("b") or method in ("POST", "PUT", "PATCH")):
                files: List[tuple] = []
                file_fields = set(meta.get("f", ())) | self._FILE_FIELDS
                for key in list(body):
                    if key not in file_fields:
                        continue
                    values = body[key] if isinstance(body[key], (list, tuple)) else [body[key]]
                    parts = []
                    for value in values:
                        if isinstance(value, (bytes, bytearray)):
                            parts.append((key, (key.rstrip("[]") or key, bytes(value))))
                        elif hasattr(value, "read"):
                            parts.append((key, (os.path.basename(getattr(value, "name", key)) or key, value)))
                        elif isinstance(value, (str, Path)) and not str(value).lower().startswith(("http://", "https://")) \
                                and Path(value).is_file():
                            fh = Path(value).open("rb")
                            opened.append(fh)
                            parts.append((key, (Path(value).name, fh)))
                        else:
                            parts = None
                            break
                    if parts:
                        files.extend(parts)
                        body.pop(key)
                if files or meta.get("mp"):
                    kwargs["data"] = [(k, self._form_value(v)) for k, v in body.items()]
                    kwargs["files"] = files or None
                elif body or method != "DELETE":
                    kwargs["json"] = body
            response = self.session.request(method, f"{self.BASE_URL}{endpoint}", **kwargs)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise self._api_error(e) from e
        finally:
            for fh in opened:
                fh.close()
        if meta.get("raw") == "binary":
            return response.content
        if meta.get("raw") == "text":
            return response.text
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as e:
            raise UploadPostError(f"API answered something that is not JSON: {response.text[:200]}",
                                  status_code=response.status_code) from e

    # Operations behind the generated methods: operationId -> (HTTP method, path,
    # details). Details: q = query parameters, b = body fields, f = file fields,
    # mp = multipart only, bearer = profile JWT instead of the API key, raw = the
    # answer is a file, na = not generally available yet (HTTP 503 until on).
    # <openapi:methods>
    _OPENAPI_OPERATIONS = {
        "sendTelegramGift": ("POST", "/uploadposts/telegram/gifts", {"b": ["user", "user_id", "chat_id", "gift_id", "max_star_count", "pay_for_upgrade", "text", "text_parse_mode", "text_entities", "confirm", "idempotency_key"], "na": True}),
        "giftTelegramPremium": ("POST", "/uploadposts/telegram/gifts/premium", {"b": ["user", "user_id", "month_count", "star_count", "text", "confirm", "idempotency_key"], "na": True}),
        "getTelegramPaymentSettings": ("GET", "/uploadposts/telegram/payments/settings", {"q": ["user"]}),
        "updateTelegramPaymentSettings": ("PUT", "/uploadposts/telegram/payments/settings", {"b": ["user", "pre_checkout", "max_total_amount", "allowed_payload_prefixes", "error_message", "shipping", "shipping_options", "shipping_countries", "only_upload_post_invoices", "confirm"]}),
        "setTelegramUpdates": ("POST", "/uploadposts/telegram/updates", {"b": ["user", "enabled", "replace_existing_webhook", "forward_url", "business_chats", "auto_answer_callbacks", "extra_updates"], "na": True}),
        "answerTelegramQuery": ("POST", "/uploadposts/telegram/answer", {"b": ["user", "type", "query_id", "text", "show_alert", "url", "cache_time", "results", "is_personal", "next_offset", "button", "result", "web_app_url", "data", "ok", "shipping_options", "error_message"]}),
        "getTelegramBusinessConnections": ("GET", "/uploadposts/telegram/business-connections", {"q": ["user", "business_connection_id"], "na": True}),
        "getTelegramBusinessProfile": ("GET", "/uploadposts/telegram/business-profile", {"q": ["user", "business_connection_id"], "na": True}),
        "updateTelegramBusinessProfile": ("PATCH", "/uploadposts/telegram/business-profile", {"b": ["user", "business_connection_id", "first_name", "last_name", "username", "bio", "media_url", "is_public", "remove_photo", "gift_settings"], "na": True}),
        "postTelegramStory": ("POST", "/uploadposts/telegram/business-stories", {"b": ["user", "business_connection_id", "media_url", "active_period", "caption", "parse_mode", "caption_entities", "areas", "post_to_chat_page", "protect_content", "story_id"], "na": True}),
        "editTelegramStory": ("PATCH", "/uploadposts/telegram/business-stories", {"b": ["user", "business_connection_id", "media_url", "active_period", "caption", "parse_mode", "caption_entities", "areas", "post_to_chat_page", "protect_content", "story_id"], "na": True}),
        "deleteTelegramStory": ("DELETE", "/uploadposts/telegram/business-stories", {"b": ["user", "business_connection_id", "media_url", "active_period", "caption", "parse_mode", "caption_entities", "areas", "post_to_chat_page", "protect_content", "story_id"], "na": True}),
        "repostTelegramStory": ("POST", "/uploadposts/telegram/business-stories/repost", {"b": ["user", "business_connection_id", "from_chat_id", "from_story_id", "active_period", "post_to_chat_page", "protect_content"], "na": True}),
        "getTelegramBusinessGifts": ("GET", "/uploadposts/telegram/business-gifts", {"q": ["user", "business_connection_id"], "na": True}),
        "manageTelegramBusinessGift": ("POST", "/uploadposts/telegram/business-gifts", {"b": ["user", "business_connection_id", "action", "owned_gift_id", "confirm", "keep_original_details", "star_count", "idempotency_key", "new_owner_chat_id"], "na": True}),
        "getTelegramBusinessStars": ("GET", "/uploadposts/telegram/business-stars", {"q": ["user", "business_connection_id"], "na": True}),
        "transferTelegramBusinessStars": ("POST", "/uploadposts/telegram/business-stars/transfer", {"b": ["user", "business_connection_id", "star_count", "idempotency_key", "confirm"], "na": True}),
        "analyzeShorts": ("POST", "/uploadposts/analyze-shorts", {"b": ["video", "platforms", "language"], "f": ["video"], "mp": True}),
        "rewriteCaptions": ("POST", "/uploadposts/rewrite-captions", {"b": ["content", "language", "platforms"]}),
        "createMediaUpload": ("POST", "/uploadposts/media-uploads", {"b": ["media_type", "filename", "content_type", "content_length", "source"]}),
        "completeMediaUpload": ("POST", "/uploadposts/media-uploads/{upload_id}/complete", {}),
        "getMediaUpload": ("GET", "/uploadposts/media-uploads/{upload_id}", {"q": ["include_url"]}),
        "deleteMediaUpload": ("DELETE", "/uploadposts/media-uploads/{upload_id}", {}),
        "getScheduledPost": ("GET", "/uploadposts/schedule/{job_id}", {}),
        "getScheduledPostThumbnail": ("GET", "/uploadposts/schedule/{job_id}/thumbnail", {}),
        "getScheduledPostPreview": ("GET", "/uploadposts/schedule/{job_id}/preview", {}),
        "createPinterestBoard": ("POST", "/uploadposts/pinterest/boards", {"q": ["profile", "user"], "b": ["user", "name", "description", "privacy", "profile"]}),
        "queryYoutubeAnalytics": ("GET", "/uploadposts/youtube/analytics/query", {"q": ["user", "start_date", "end_date", "metrics", "dimensions", "filters", "sort", "max_results", "start_index", "report"], "na": True}),
        "listYoutubeAnalyticsReports": ("GET", "/uploadposts/youtube/analytics/reports", {"q": ["user"], "na": True}),
        "listYoutubeAnalyticsGroups": ("GET", "/uploadposts/youtube/analytics/groups", {"q": ["user", "ids", "page_token"], "na": True}),
        "listYoutubeAnalyticsGroupItems": ("GET", "/uploadposts/youtube/analytics/groups/{group_id}/items", {"q": ["user"], "na": True}),
        "getYoutubeAnalyticsUsage": ("GET", "/uploadposts/youtube/analytics/usage", {"na": True}),
        "listYoutubeReportTypes": ("GET", "/uploadposts/youtube/reporting/report-types", {"q": ["user", "page_token", "page_size"], "na": True}),
        "listYoutubeReportingJobs": ("GET", "/uploadposts/youtube/reporting/jobs", {"q": ["user", "page_token", "page_size"], "na": True}),
        "createYoutubeReportingJob": ("POST", "/uploadposts/youtube/reporting/jobs", {"b": ["user", "report_type_id", "name"], "na": True}),
        "getYoutubeReportingJob": ("GET", "/uploadposts/youtube/reporting/jobs/{job_id}", {"q": ["user"], "na": True}),
        "deleteYoutubeReportingJob": ("DELETE", "/uploadposts/youtube/reporting/jobs/{job_id}", {"b": ["user", "confirm"], "na": True}),
        "listYoutubeReports": ("GET", "/uploadposts/youtube/reporting/jobs/{job_id}/reports", {"q": ["user", "created_after", "start_time_at_or_after", "start_time_before", "page_token", "page_size"], "na": True}),
        "getYoutubeReport": ("GET", "/uploadposts/youtube/reporting/jobs/{job_id}/reports/{report_id}", {"q": ["user"], "na": True}),
        "downloadYoutubeReport": ("GET", "/uploadposts/youtube/reporting/jobs/{job_id}/reports/{report_id}/download", {"q": ["user"], "raw": 'text', "na": True}),
        "getYoutubePush": ("GET", "/uploadposts/youtube/push", {"q": ["user"], "na": True}),
        "enableYoutubePush": ("POST", "/uploadposts/youtube/push", {"b": ["user"], "na": True}),
        "disableYoutubePush": ("DELETE", "/uploadposts/youtube/push", {"b": ["user"], "na": True}),
        "getInstagramPublishingLimit": ("GET", "/uploadposts/instagram/publishing_limit", {"q": ["profile", "refresh"]}),
        "getThreadsPublishingLimit": ("GET", "/uploadposts/threads/publishing_limit", {"q": ["user", "profile", "refresh"]}),
        "listPinterestBoardSections": ("GET", "/uploadposts/pinterest/boards/{board_id}/sections", {"q": ["profile"]}),
        "createPinterestBoardSection": ("POST", "/uploadposts/pinterest/boards/{board_id}/sections", {"q": ["profile", "user"], "b": ["user", "name", "profile"]}),
        "getFacebookPageInfo": ("GET", "/uploadposts/facebook/page-info", {"q": ["user", "page_id"]}),
        "updateFacebookPageInfo": ("PATCH", "/uploadposts/facebook/page-info", {"b": ["user", "page_id", "validate_only", "about", "description", "website", "phone", "emails", "hours", "picture_url", "cover_url"]}),
        "listRedditSubreddits": ("GET", "/uploadposts/reddit/subreddits", {"q": ["profile"]}),
        "getRedditPostTypes": ("GET", "/uploadposts/reddit/post-types", {"q": ["profile", "subreddit"]}),
        "listRedditFlairs": ("GET", "/uploadposts/reddit/flairs", {"q": ["profile", "subreddit"]}),
        "getRedditDetailedPosts": ("GET", "/uploadposts/reddit/detailed-posts/", {"q": ["profile_username"]}),
        "getUserProfile": ("GET", "/uploadposts/users/{username}", {}),
        "renameUserProfile": ("PATCH", "/uploadposts/users/{username}", {"b": ["display_name"]}),
        "disconnectSocialAccount": ("DELETE", "/uploadposts/users/social", {"b": ["profile_username", "social_platform"]}),
        "connectDiscordCredentials": ("POST", "/uploadposts/users/discord/credentials", {"b": ["profile_username", "webhook_url", "name"]}),
        "connectTelegramCredentials": ("POST", "/uploadposts/users/telegram/credentials", {"b": ["profile_username", "bot_token", "chat_id", "receive_updates", "replace_existing_webhook", "forward_url", "auto_answer_callbacks", "extra_updates", "name"]}),
        "connectSlackCredentials": ("POST", "/uploadposts/users/slack/credentials", {"b": ["profile_username", "webhook_url", "name"]}),
        "connectMastodonCredentials": ("POST", "/uploadposts/users/mastodon/credentials", {"b": ["profile_username", "instance_url", "access_token", "name"]}),
        "connectNostrCredentials": ("POST", "/uploadposts/users/nostr/credentials", {"b": ["profile_username", "private_key", "relays", "name"]}),
        "connectLemmyCredentials": ("POST", "/uploadposts/users/lemmy/credentials", {"b": ["profile_username", "instance_url", "username", "password", "community", "name"]}),
        "connectDevToCredentials": ("POST", "/uploadposts/users/devto/credentials", {"b": ["profile_username", "api_key", "name"]}),
        "connectHashnodeCredentials": ("POST", "/uploadposts/users/hashnode/credentials", {"b": ["profile_username", "pat", "publication_id", "name"]}),
        "connectWordPressCredentials": ("POST", "/uploadposts/users/wordpress/credentials", {"b": ["profile_username", "site_url", "username", "application_password", "name"]}),
        "connectWhopCredentials": ("POST", "/uploadposts/users/whop/credentials", {"b": ["profile_username", "api_key", "experience_id", "name"]}),
        "connectListmonkCredentials": ("POST", "/uploadposts/users/listmonk/credentials", {"b": ["profile_username", "instance_url", "username", "password", "list_id", "name"]}),
        "listFacebookPageChoices": ("GET", "/uploadposts/users/facebook-page", {"q": ["profile_username"]}),
        "setFacebookPage": ("POST", "/uploadposts/users/facebook-page", {"b": ["profile_username", "facebook_page_id"]}),
        "clearFacebookPage": ("DELETE", "/uploadposts/users/facebook-page", {"b": ["profile_username"]}),
        "listLinkedInPageChoices": ("GET", "/uploadposts/users/linkedin-page", {"q": ["profile_username"]}),
        "setLinkedInPage": ("POST", "/uploadposts/users/linkedin-page", {"b": ["profile_username", "linkedin_page_id"]}),
        "clearLinkedInPage": ("DELETE", "/uploadposts/users/linkedin-page", {"b": ["profile_username"]}),
        "connectBlueskyCredentials": ("POST", "/uploadposts/users/bluesky/credentials", {"b": ["profile_username", "handle", "password"]}),
        "setYoutubeOAuthClient": ("POST", "/uploadposts/users/youtube/credentials", {"b": ["profile_username", "client_id", "client_secret"]}),
        "getCurrentUser": ("GET", "/uploadposts/me", {}),
        "startOAuthConnection": ("POST", "/uploadposts/oauth/{platform}/start", {"b": ["profile", "redirect_url"]}),
        "createFfmpegJob": ("POST", "/uploadposts/ffmpeg/jobs/upload", {"b": ["files", "full_command", "output_extension", "publish", "file", "file1", "file2"], "f": ["file", "file1", "file2"]}),
        "getFfmpegJobStatus": ("GET", "/uploadposts/ffmpeg/jobs/{job_id}", {}),
        "downloadFfmpegResult": ("GET", "/uploadposts/ffmpeg/jobs/{job_id}/download", {"raw": 'binary'}),
        "getFfmpegConsumption": ("GET", "/uploadposts/ffmpeg/consumption", {}),
        "listWebhookSubscriptions": ("GET", "/uploadposts/webhooks/subscriptions", {"q": ["status", "source", "url"], "na": True}),
        "createWebhookSubscription": ("POST", "/uploadposts/webhooks/subscriptions", {"b": ["url", "events", "profile_username", "source", "name"], "na": True}),
        "getWebhookSubscription": ("GET", "/uploadposts/webhooks/subscriptions/{subscription_id}", {"na": True}),
        "deleteWebhookSubscription": ("DELETE", "/uploadposts/webhooks/subscriptions/{subscription_id}", {"na": True}),
        "testWebhookSubscription": ("POST", "/uploadposts/webhooks/subscriptions/{subscription_id}/test", {"b": ["event"], "na": True}),
        "testNotifications": ("POST", "/uploadposts/users/notifications/test", {"b": ["platform", "media_type", "title", "caption", "profile_username", "message", "result"]}),
        "deleteCommentPost": ("POST", "/uploadposts/comments/delete", {"b": ["platform", "user", "comment_id", "post_id"]}),
        "deleteBlueskyChatAccount": ("POST", "/uploadposts/dms/bluesky/account/delete", {"b": ["user", "confirm", "confirm_handle"], "na": True}),
        "listBlueskyMutualGroups": ("GET", "/uploadposts/dms/bluesky/groups", {"q": ["user", "subject", "limit", "cursor"], "na": True}),
        "createBlueskyGroup": ("POST", "/uploadposts/dms/bluesky/groups", {"b": ["user", "name", "members", "idempotency_key"], "na": True}),
        "editBlueskyGroup": ("PATCH", "/uploadposts/dms/bluesky/groups/{conversation_id}", {"b": ["user", "name", "locked"], "na": True}),
        "listBlueskyGroupMembers": ("GET", "/uploadposts/dms/bluesky/groups/{conversation_id}/members", {"q": ["user"], "na": True}),
        "addBlueskyGroupMembers": ("POST", "/uploadposts/dms/bluesky/groups/{conversation_id}/members", {"b": ["user", "members"], "na": True}),
        "removeBlueskyGroupMembers": ("DELETE", "/uploadposts/dms/bluesky/groups/{conversation_id}/members", {"b": ["user", "members"], "na": True}),
        "manageBlueskyJoinLink": ("POST", "/uploadposts/dms/bluesky/groups/{conversation_id}/join-link", {"b": ["user", "action", "require_approval", "join_rule"], "na": True}),
        "listBlueskyJoinRequests": ("GET", "/uploadposts/dms/bluesky/groups/{conversation_id}/join-requests", {"q": ["user"], "na": True}),
        "answerBlueskyJoinRequest": ("POST", "/uploadposts/dms/bluesky/groups/{conversation_id}/join-requests", {"b": ["user", "action", "member"], "na": True}),
        "previewBlueskyJoinLinks": ("GET", "/uploadposts/dms/bluesky/join-links", {"q": ["user", "codes"], "na": True}),
        "joinBlueskyGroup": ("POST", "/uploadposts/dms/bluesky/join-links", {"b": ["user", "code"], "na": True}),
        "downloadDmMedia": ("GET", "/uploadposts/dms/media", {"q": ["platform", "user", "media_id"], "raw": 'binary'}),
        "blueskyGraphAction": ("POST", "/uploadposts/bluesky/graph", {"b": ["user", "action", "actor", "list", "post_id", "only_reposts", "only_quoteposts"], "na": True}),
        "listBlueskyLists": ("GET", "/uploadposts/bluesky/lists", {"q": ["user", "purposes", "cursor"], "na": True}),
        "createBlueskyList": ("POST", "/uploadposts/bluesky/lists", {"b": ["user", "name", "purpose", "description", "avatar", "avatar_url", "remove_avatar"], "f": ["avatar"], "na": True}),
        "getBlueskyList": ("GET", "/uploadposts/bluesky/lists/{list_id}", {"q": ["user"], "na": True}),
        "updateBlueskyList": ("PATCH", "/uploadposts/bluesky/lists/{list_id}", {"b": ["user", "name", "purpose", "description", "avatar", "avatar_url", "remove_avatar"], "f": ["avatar"], "na": True}),
        "deleteBlueskyList": ("DELETE", "/uploadposts/bluesky/lists/{list_id}", {"b": ["user", "confirm"], "na": True}),
        "listBlueskyListMembers": ("GET", "/uploadposts/bluesky/lists/{list_id}/members", {"q": ["user"], "na": True}),
        "addBlueskyListMember": ("POST", "/uploadposts/bluesky/lists/{list_id}/members", {"b": ["user", "actor"], "na": True}),
        "removeBlueskyListMember": ("DELETE", "/uploadposts/bluesky/lists/{list_id}/members", {"b": ["user", "actor"], "na": True}),
        "optOutBlueskyList": ("POST", "/uploadposts/bluesky/lists/opt-out", {"b": ["user", "list"], "na": True}),
        "removeOptOutBlueskyList": ("DELETE", "/uploadposts/bluesky/lists/opt-out", {"b": ["user", "list"], "na": True}),
        "listBlueskyStarterPacks": ("GET", "/uploadposts/bluesky/starter-packs", {"q": ["user"], "na": True}),
        "createBlueskyStarterPack": ("POST", "/uploadposts/bluesky/starter-packs", {"b": ["user", "name", "description", "feeds", "list", "members"], "na": True}),
        "getBlueskyStarterPack": ("GET", "/uploadposts/bluesky/starter-packs/{pack_id}", {"q": ["user"], "na": True}),
        "updateBlueskyStarterPack": ("PATCH", "/uploadposts/bluesky/starter-packs/{pack_id}", {"b": ["user", "name", "description", "feeds", "list", "members"], "na": True}),
        "deleteBlueskyStarterPack": ("DELETE", "/uploadposts/bluesky/starter-packs/{pack_id}", {"b": ["user", "confirm", "delete_list"], "na": True}),
        "listBlueskyFeeds": ("GET", "/uploadposts/bluesky/feeds", {"q": ["user"], "na": True}),
        "createBlueskyFeed": ("POST", "/uploadposts/bluesky/feeds", {"b": ["user", "rkey", "did", "display_name", "description", "avatar", "accepts_interactions", "content_mode"], "f": ["avatar"], "na": True}),
        "updateBlueskyFeed": ("PATCH", "/uploadposts/bluesky/feeds/{rkey}", {"b": ["user", "did", "display_name", "description", "avatar", "accepts_interactions", "content_mode"], "f": ["avatar"], "na": True}),
        "deleteBlueskyFeed": ("DELETE", "/uploadposts/bluesky/feeds/{rkey}", {"b": ["user", "confirm"], "na": True}),
        "reportOnBluesky": ("POST", "/uploadposts/bluesky/report", {"b": ["user", "post_id", "actor", "reason_type", "reason", "confirm"], "na": True}),
        "listPostApprovals": ("GET", "/uploadposts/approvals", {"q": ["status", "profile_username", "author", "limit", "before", "count_only"], "na": True}),
        "getPostApproval": ("GET", "/uploadposts/approvals/{approval_id}", {"na": True}),
        "editPostApproval": ("PATCH", "/uploadposts/approvals/{approval_id}", {"b": ["title", "caption", "description", "platform_content", "fields", "scheduled_date", "timezone", "cover_image_base64", "remove_cover"], "na": True}),
        "withdrawPostApproval": ("DELETE", "/uploadposts/approvals/{approval_id}", {"na": True}),
        "approvePostApproval": ("POST", "/uploadposts/approvals/{approval_id}/approve", {"b": ["version", "comment", "scheduled_date", "timezone", "publish_now"], "na": True}),
        "rejectPostApproval": ("POST", "/uploadposts/approvals/{approval_id}/reject", {"b": ["comment"], "na": True}),
        "listClientPostApprovals": ("GET", "/uploadposts/approvals/client", {"bearer": True, "na": True}),
        "approveClientPostApproval": ("POST", "/uploadposts/approvals/client/{approval_id}/approve", {"b": ["version", "comment"], "bearer": True, "na": True}),
        "rejectClientPostApproval": ("POST", "/uploadposts/approvals/client/{approval_id}/reject", {"b": ["comment"], "bearer": True, "na": True}),
        "getTeamRoles": ("GET", "/uploadposts/teams/roles", {}),
        "listTeamAudit": ("GET", "/uploadposts/teams/audit", {"q": ["actor", "action", "profile_username", "target_id", "since", "until", "limit", "cursor"]}),
        "sendFeedback": ("POST", "/uploadposts/feedback", {"b": ["message", "category", "endpoint", "request_id", "agent"]}),
        "updateGoogleBusinessAccount": ("PATCH", "/uploadposts/google-business/accounts", {"b": ["user", "account", "account_name", "validate_only", "confirm"], "na": True}),
        "createGoogleBusinessAdmin": ("POST", "/uploadposts/google-business/admins", {"b": ["user", "scope", "account", "location_id", "admin", "admin_account", "role", "confirm"], "na": True}),
        "updateGoogleBusinessAdmin": ("PATCH", "/uploadposts/google-business/admins", {"b": ["user", "admin_name", "role", "confirm"], "na": True}),
        "deleteGoogleBusinessAdmin": ("DELETE", "/uploadposts/google-business/admins", {"b": ["user", "admin_name", "confirm"], "na": True}),
        "acceptGoogleBusinessInvitation": ("POST", "/uploadposts/google-business/invitations/accept", {"b": ["user", "invitation", "confirm"], "na": True}),
        "declineGoogleBusinessInvitation": ("POST", "/uploadposts/google-business/invitations/decline", {"b": ["user", "invitation", "confirm"], "na": True}),
        "transferGoogleBusinessLocation": ("POST", "/uploadposts/google-business/locations/transfer", {"b": ["user", "location_id", "destination_account", "confirm"], "na": True}),
        "createGoogleBusinessLocation": ("POST", "/uploadposts/google-business/locations/create", {"b": ["user", "account", "location", "language_code", "title", "primary_category", "request_id", "dry_run", "confirm"], "na": True}),
        "deleteGoogleBusinessLocation": ("DELETE", "/uploadposts/google-business/locations/delete", {"b": ["user", "location_id", "confirm"], "na": True}),
        "getGoogleBusinessNotificationSettings": ("GET", "/uploadposts/google-business/notifications", {"q": ["user", "account"], "na": True}),
        "updateGoogleBusinessNotificationSettings": ("PUT", "/uploadposts/google-business/notifications", {"b": ["user", "account", "enabled", "types", "confirm", "force", "confirm_other_tool"], "na": True}),
        "startGoogleBusinessVerification": ("POST", "/uploadposts/google-business/verification/start", {"b": ["user", "location_id", "method", "phone_number", "email_address", "mailer_contact", "trusted_partner_token", "token", "language_code", "context", "confirm"], "na": True}),
        "completeGoogleBusinessVerification": ("POST", "/uploadposts/google-business/verification/complete", {"b": ["user", "location_id", "verification_name", "verification_id", "pin"], "na": True}),
        "generateGoogleBusinessVerificationToken": ("POST", "/uploadposts/google-business/verification/token", {"b": ["user", "location_id"], "na": True}),
        "connectChatgptAdsAccount": ("POST", "/uploadposts/ads/chatgpt/connect", {"b": ["api_key", "profile_username", "name", "default"]}),
        "listChatgptAdsAccounts": ("GET", "/uploadposts/ads/chatgpt/accounts", {}),
        "disconnectChatgptAdsAccount": ("DELETE", "/uploadposts/ads/chatgpt/accounts/{ad_account_id}", {"q": ["profile_username"]}),
        "getChatgptAdsAccount": ("GET", "/uploadposts/ads/chatgpt/account", {"q": ["ad_account_id", "profile_username"]}),
        "listChatgptAdsCampaigns": ("GET", "/uploadposts/ads/chatgpt/campaigns", {"q": ["limit", "after", "before", "order", "ad_account_id", "profile_username"]}),
        "createChatgptAdsCampaign": ("POST", "/uploadposts/ads/chatgpt/campaigns", {"q": ["ad_account_id", "profile_username"], "b": ["name", "budget", "budget_micros", "status", "description", "start_time", "end_time", "bidding_type", "conversion_event_setting_ids", "mode", "product_feed_id", "locations", "custom_audience_ids", "excluded_custom_audience_ids", "targeting", "ad_account_id", "profile_username"]}),
        "getChatgptAdsCampaign": ("GET", "/uploadposts/ads/chatgpt/campaigns/{campaign_id}", {"q": ["ad_account_id", "profile_username"]}),
        "updateChatgptAdsCampaign": ("POST", "/uploadposts/ads/chatgpt/campaigns/{campaign_id}", {"q": ["ad_account_id", "profile_username"], "b": ["name", "budget", "budget_micros", "status", "description", "start_time", "end_time", "locations", "custom_audience_ids", "excluded_custom_audience_ids", "targeting", "ad_account_id", "profile_username"]}),
        "activateChatgptAdsCampaign": ("POST", "/uploadposts/ads/chatgpt/campaigns/{campaign_id}/activate", {"q": ["ad_account_id", "profile_username"]}),
        "pauseChatgptAdsCampaign": ("POST", "/uploadposts/ads/chatgpt/campaigns/{campaign_id}/pause", {"q": ["ad_account_id", "profile_username"]}),
        "archiveChatgptAdsCampaign": ("POST", "/uploadposts/ads/chatgpt/campaigns/{campaign_id}/archive", {"q": ["ad_account_id", "profile_username"]}),
        "getChatgptAdsCampaignInsights": ("GET", "/uploadposts/ads/chatgpt/campaigns/{campaign_id}/insights", {"q": ["since", "until", "time_granularity", "aggregation_level", "fields", "segments", "filters", "sort", "time_ranges", "limit", "after", "before", "ad_account_id", "profile_username"]}),
        "listChatgptAdsAdGroups": ("GET", "/uploadposts/ads/chatgpt/adgroups", {"q": ["campaign_id", "limit", "after", "before", "order", "ad_account_id", "profile_username"]}),
        "createChatgptAdsAdGroup": ("POST", "/uploadposts/ads/chatgpt/adgroups", {"q": ["ad_account_id", "profile_username"], "b": ["campaign_id", "name", "max_bid", "max_bid_micros", "billing_event_type", "bidding_config", "status", "description", "context_hints", "product_set", "ad_account_id", "profile_username"]}),
        "getChatgptAdsAdGroup": ("GET", "/uploadposts/ads/chatgpt/adgroups/{ad_group_id}", {"q": ["ad_account_id", "profile_username"]}),
        "updateChatgptAdsAdGroup": ("POST", "/uploadposts/ads/chatgpt/adgroups/{ad_group_id}", {"q": ["ad_account_id", "profile_username"], "b": ["name", "max_bid", "max_bid_micros", "billing_event_type", "bidding_config", "status", "description", "context_hints", "product_set", "ad_account_id", "profile_username"]}),
        "activateChatgptAdsAdGroup": ("POST", "/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/activate", {"q": ["ad_account_id", "profile_username"]}),
        "pauseChatgptAdsAdGroup": ("POST", "/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/pause", {"q": ["ad_account_id", "profile_username"]}),
        "archiveChatgptAdsAdGroup": ("POST", "/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/archive", {"q": ["ad_account_id", "profile_username"]}),
        "getChatgptAdsAdGroupInsights": ("GET", "/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/insights", {"q": ["since", "until", "time_granularity", "aggregation_level", "fields", "segments", "filters", "sort", "time_ranges", "limit", "after", "before", "ad_account_id", "profile_username"]}),
        "listChatgptAdsAds": ("GET", "/uploadposts/ads/chatgpt/ads", {"q": ["ad_group_id", "limit", "after", "before", "order", "ad_account_id", "profile_username"]}),
        "createChatgptAdsAd": ("POST", "/uploadposts/ads/chatgpt/ads", {"q": ["ad_account_id", "profile_username"], "b": ["ad_group_id", "name", "title", "body", "target_url", "file_id", "price", "type", "status", "creative", "ad_account_id", "profile_username"]}),
        "getChatgptAdsAd": ("GET", "/uploadposts/ads/chatgpt/ads/{ad_id}", {"q": ["ad_account_id", "profile_username"]}),
        "updateChatgptAdsAd": ("POST", "/uploadposts/ads/chatgpt/ads/{ad_id}", {"q": ["ad_account_id", "profile_username"], "b": ["name", "status", "creative", "ad_account_id", "profile_username"]}),
        "activateChatgptAdsAd": ("POST", "/uploadposts/ads/chatgpt/ads/{ad_id}/activate", {"q": ["ad_account_id", "profile_username"]}),
        "pauseChatgptAdsAd": ("POST", "/uploadposts/ads/chatgpt/ads/{ad_id}/pause", {"q": ["ad_account_id", "profile_username"]}),
        "archiveChatgptAdsAd": ("POST", "/uploadposts/ads/chatgpt/ads/{ad_id}/archive", {"q": ["ad_account_id", "profile_username"]}),
        "getChatgptAdsAdInsights": ("GET", "/uploadposts/ads/chatgpt/ads/{ad_id}/insights", {"q": ["since", "until", "time_granularity", "aggregation_level", "fields", "segments", "filters", "sort", "time_ranges", "limit", "after", "before", "ad_account_id", "profile_username"]}),
        "previewChatgptAdsAd": ("POST", "/uploadposts/ads/chatgpt/ads/{ad_id}/preview", {"q": ["ad_account_id", "profile_username"]}),
        "uploadChatgptAdsCreative": ("POST", "/uploadposts/ads/chatgpt/creatives", {"q": ["ad_account_id", "profile_username"], "b": ["image_url", "ad_account_id", "profile_username", "file"], "f": ["file"]}),
        "getChatgptAdsAccountInsights": ("GET", "/uploadposts/ads/chatgpt/insights", {"q": ["since", "until", "time_granularity", "aggregation_level", "fields", "segments", "filters", "sort", "time_ranges", "limit", "after", "before", "ad_account_id", "profile_username"]}),
        "promoteChatgptAds": ("POST", "/uploadposts/ads/chatgpt/promote", {"q": ["ad_account_id", "profile_username"], "b": ["title", "body", "target_url", "image_url", "file_id", "budget", "budget_micros", "max_bid", "max_bid_micros", "name", "status", "bidding_type", "billing_event_type", "start_time", "end_time", "description", "conversion_event_setting_ids", "locations", "custom_audience_ids", "excluded_custom_audience_ids", "targeting", "context_hints", "price", "ad_group_name", "ad_name", "ad_account_id", "profile_username"]}),
    }

    # ---- Telegram ----
    def send_telegram_gift(self, user: str, gift_id: str, max_star_count: int, confirm: bool, idempotency_key: str, **params) -> Dict:
        """Send a gift from the bot's Stars.

        Not generally available yet. Off by default: answers `503` with
        `telegram_stars_spend_disabled` until the feature is available.

        sendGift. Spends the bot's Stars. Requires confirm=true and max_star_count
        (checked against the current price).

        ``POST /api/uploadposts/telegram/gifts``

        Args:
            user: Profile username.
            user_id (int, optional)
            chat_id (str, optional)
            gift_id
            max_star_count
            pay_for_upgrade (bool, optional)
            text (str, optional)
            text_parse_mode (str, optional)
            text_entities (List[Dict[str, Any]], optional)
            confirm
            idempotency_key
            **params: Any other API field, by its API name.
        """
        return self._op("sendTelegramGift", params, user=user, gift_id=gift_id, max_star_count=max_star_count, confirm=confirm, idempotency_key=idempotency_key)

    def gift_telegram_premium(self, user: str, user_id: int, month_count: int, star_count: int, confirm: bool, idempotency_key: str, **params) -> Dict:
        """Gift Telegram Premium from the bot's Stars.

        Not generally available yet. Off by default: answers `503` with
        `telegram_stars_spend_disabled` until the feature is available.

        Spends the bot's Stars.

        ``POST /api/uploadposts/telegram/gifts/premium``

        Args:
            user: Profile username.
            user_id
            month_count
            star_count
            text (str, optional)
            confirm
            idempotency_key
            **params: Any other API field, by its API name.
        """
        return self._op("giftTelegramPremium", params, user=user, user_id=user_id, month_count=month_count, star_count=star_count, confirm=confirm, idempotency_key=idempotency_key)

    def get_telegram_payment_settings(self, user: str, **params) -> Dict:
        """Automatic pre-checkout rules.

        **The automatic answers need the bot's updates turned on (POST
        /api/uploadposts/telegram/updates).**

        ``GET /api/uploadposts/telegram/payments/settings``

        Args:
            user: Profile username with Telegram connected.
            **params: Any other API field, by its API name.
        """
        return self._op("getTelegramPaymentSettings", params, user=user)

    def update_telegram_payment_settings(self, user: str, **params) -> Dict:
        """Set automatic pre-checkout rules.

        **The automatic answers need the bot's updates turned on (POST
        /api/uploadposts/telegram/updates).**

        ``PUT /api/uploadposts/telegram/payments/settings``

        Args:
            user: Profile username.
            pre_checkout (str, optional)
            max_total_amount (Dict[str, Any], optional): Required for approve:
                maximum order total per currency, e.g. {"XTR": 500}. Setting
                pre_checkout to off without it clears the stored value.
            allowed_payload_prefixes (List[str], optional)
            error_message (str, optional)
            shipping (str, optional)
            shipping_options (List[Dict[str, Any]], optional)
            shipping_countries (List[str], optional)
            only_upload_post_invoices (bool, optional)
            confirm (bool, optional): Required to save a rule that answers (approve,
                reject, shipping static).
            **params: Any other API field, by its API name.
        """
        return self._op("updateTelegramPaymentSettings", params, user=user)

    def set_telegram_updates(self, user: str, enabled: bool, **params) -> Dict:
        """Turn Telegram updates on or off.

        Not generally available yet. Off by default: answers `503` with
        `telegram_updates_unavailable` until the feature is available.

        Opt-in per bot. A webhook that is not Upload-Post's is never replaced without
        replace_existing_webhook=true (409 telegram_webhook_in_use otherwise). With no
        webhook, the answer warns that a getUpdates integration stops receiving.

        ``POST /api/uploadposts/telegram/updates``

        Args:
            user: Profile username.
            enabled: true to receive, false to stop.
            replace_existing_webhook (bool, optional): Replace a webhook that is not
                Upload-Post's.
            forward_url (str, optional): https URL that also gets every raw update,
                signed with your webhook secret (required), one attempt.
            business_chats (bool, optional): Also receive and keep the chats of the
                connected Telegram Business account (default false).
            auto_answer_callbacks (bool, optional): Empty answerCallbackQuery if you
                did not answer a button press in ~8 s.
            extra_updates (List[str], optional)
            **params: Any other API field, by its API name.
        """
        return self._op("setTelegramUpdates", params, user=user, enabled=enabled)

    def answer_telegram_query(self, user: str, type: str, **params) -> Dict:
        """Answer a Telegram query.

        Answer a callback_query, inline_query, join request, guest/widget query,
        shipping or pre-checkout query received as a telegram_update event. 410
        telegram_query_expired when Telegram's time is up.

        ``POST /api/uploadposts/telegram/answer``

        Args:
            user: Profile username.
            type
            query_id (str, optional): The query id (or the official field:
                callback_query_id, inline_query_id...).
            text (str, optional): callback: 0-200 characters.
            show_alert (bool, optional): callback.
            url (str, optional): callback.
            cache_time (int, optional): callback / inline.
            results (List[Dict[str, Any]], optional): inline: up to 50
                InlineQueryResult.
            is_personal (bool, optional): inline.
            next_offset (str, optional): inline.
            button (Dict[str, Any], optional): inline: InlineQueryResultsButton.
            result (Any, optional): join_request: approve|decline|queue. guest:
                InlineQueryResult.
            web_app_url (str, optional): join_request_web_app: https URL.
            data (str, optional): widget: up to 1024 bytes.
            ok (bool, optional): shipping / pre_checkout.
            shipping_options (List[Dict[str, Any]], optional)
            error_message (str, optional): shipping / pre_checkout when ok is false.
            **params: Any other API field, by its API name.
        """
        return self._op("answerTelegramQuery", params, user=user, type=type)

    def get_telegram_business_connections(self, user: str, **params) -> Dict:
        """Telegram Business connections.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        Connections of the bot with Telegram Business accounts (rights, enabled).

        ``GET /api/uploadposts/telegram/business-connections``

        Args:
            user: Profile username.
            business_connection_id (str, optional): Optional when the bot has one
                active Business connection.
            **params: Any other API field, by its API name.
        """
        return self._op("getTelegramBusinessConnections", params, user=user)

    def get_telegram_business_profile(self, user: str, **params) -> Dict:
        """Telegram Business account.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        The connected account.

        ``GET /api/uploadposts/telegram/business-profile``

        Args:
            user: Profile username.
            business_connection_id (str, optional): Optional when the bot has one
                active Business connection.
            **params: Any other API field, by its API name.
        """
        return self._op("getTelegramBusinessProfile", params, user=user)

    def update_telegram_business_profile(self, user: str, **params) -> Dict:
        """Update the Telegram Business profile.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        first_name/last_name, username, bio, photo (multipart or media_url, is_public),
        remove_photo, gift_settings.

        ``PATCH /api/uploadposts/telegram/business-profile``

        Args:
            user: Profile username.
            business_connection_id (str, optional)
            first_name (str, optional): 1-64.
            last_name (str, optional): 0-64.
            username (str, optional): 0-32.
            bio (str, optional): 0-140.
            media_url (str, optional): Public URL of the new photo (JPG) or
                animation (MP4).
            is_public (bool, optional)
            remove_photo (bool, optional)
            gift_settings (Dict[str, Any], optional): {show_gift_button,
                accepted_gift_types}.
            **params: Any other API field, by its API name.
        """
        return self._op("updateTelegramBusinessProfile", params, user=user)

    def post_telegram_story(self, user: str, **params) -> Dict:
        """Post a Telegram story.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        postStory on behalf of the Business account. Photos 1080x1920 up to 10 MB;
        videos 720x1280 H.265 up to 30 MB, 60 s.

        ``POST /api/uploadposts/telegram/business-stories``

        Args:
            user: Profile username.
            business_connection_id (str, optional)
            media_url (str, optional): Or a multipart 'file'.
            active_period (int, optional): 6, 12, 24 or 48 (hours) or the seconds.
            caption (str, optional): 0-2048.
            parse_mode (str, optional)
            caption_entities (List[Dict[str, Any]], optional)
            areas (List[Dict[str, Any]], optional)
            post_to_chat_page (bool, optional)
            protect_content (bool, optional)
            story_id (int, optional): PATCH / DELETE.
            **params: Any other API field, by its API name.
        """
        return self._op("postTelegramStory", params, user=user)

    def edit_telegram_story(self, user: str, **params) -> Dict:
        """Edit a Telegram story.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        editStory.

        ``PATCH /api/uploadposts/telegram/business-stories``

        Args:
            user: Profile username.
            business_connection_id (str, optional)
            media_url (str, optional): Or a multipart 'file'.
            active_period (int, optional): 6, 12, 24 or 48 (hours) or the seconds.
            caption (str, optional): 0-2048.
            parse_mode (str, optional)
            caption_entities (List[Dict[str, Any]], optional)
            areas (List[Dict[str, Any]], optional)
            post_to_chat_page (bool, optional)
            protect_content (bool, optional)
            story_id (int, optional): PATCH / DELETE.
            **params: Any other API field, by its API name.
        """
        return self._op("editTelegramStory", params, user=user)

    def delete_telegram_story(self, user: str, story_id: int, **params) -> Dict:
        """Delete a Telegram story.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        deleteStory.

        ``DELETE /api/uploadposts/telegram/business-stories``

        Args:
            user: Profile username.
            business_connection_id (str, optional)
            media_url (str, optional): Or a multipart 'file'.
            active_period (int, optional): 6, 12, 24 or 48 (hours) or the seconds.
            caption (str, optional): 0-2048.
            parse_mode (str, optional)
            caption_entities (List[Dict[str, Any]], optional)
            areas (List[Dict[str, Any]], optional)
            post_to_chat_page (bool, optional)
            protect_content (bool, optional)
            story_id: PATCH / DELETE.
            **params: Any other API field, by its API name.
        """
        return self._op("deleteTelegramStory", params, user=user, story_id=story_id)

    def repost_telegram_story(self, user: str, from_chat_id: int, from_story_id: int, active_period: int, **params) -> Dict:
        """Repost a Telegram story.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        repostStory from another Business account of the same bot.

        ``POST /api/uploadposts/telegram/business-stories/repost``

        Args:
            user
            business_connection_id (str, optional)
            from_chat_id
            from_story_id
            active_period
            post_to_chat_page (bool, optional)
            protect_content (bool, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("repostTelegramStory", params, user=user, from_chat_id=from_chat_id, from_story_id=from_story_id, active_period=active_period)

    def get_telegram_business_gifts(self, user: str, **params) -> Dict:
        """Telegram Business gifts.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        getBusinessAccountGifts with Telegram's filters.

        ``GET /api/uploadposts/telegram/business-gifts``

        Args:
            user: Profile username.
            business_connection_id (str, optional): Optional when the bot has one
                active Business connection.
            **params: Any other API field, by its API name.
        """
        return self._op("getTelegramBusinessGifts", params, user=user)

    def manage_telegram_business_gift(self, user: str, action: str, owned_gift_id: str, confirm: bool, idempotency_key: str, **params) -> Dict:
        """Convert, upgrade, transfer or delete a gift.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        Irreversible: requires confirm=true and an idempotency_key (a repeat with the
        same key returns the first answer).

        ``POST /api/uploadposts/telegram/business-gifts``

        Args:
            user
            business_connection_id (str, optional)
            action
            owned_gift_id
            confirm: Must be true.
            keep_original_details (bool, optional): upgrade.
            star_count (int, optional): upgrade / transfer.
            idempotency_key: Required. Unique string (max 128): a repeat with the
                same key returns the first answer.
            new_owner_chat_id (int, optional): transfer.
            **params: Any other API field, by its API name.
        """
        return self._op("manageTelegramBusinessGift", params, user=user, action=action, owned_gift_id=owned_gift_id, confirm=confirm, idempotency_key=idempotency_key)

    def get_telegram_business_stars(self, user: str, **params) -> Dict:
        """Telegram Business Stars balance.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        getBusinessAccountStarBalance.

        ``GET /api/uploadposts/telegram/business-stars``

        Args:
            user: Profile username.
            business_connection_id (str, optional): Optional when the bot has one
                active Business connection.
            **params: Any other API field, by its API name.
        """
        return self._op("getTelegramBusinessStars", params, user=user)

    def transfer_telegram_business_stars(self, user: str, star_count: int, idempotency_key: str, confirm: bool, **params) -> Dict:
        """Move Stars to the bot.

        Not generally available yet. Off by default: answers `503` with
        `telegram_business_unavailable` until the feature is available.

        transferBusinessAccountStars (1-10000). Requires confirm=true and an
        idempotency_key.

        ``POST /api/uploadposts/telegram/business-stars/transfer``

        Args:
            user
            business_connection_id (str, optional)
            star_count: 1-10000.
            idempotency_key: Required. Unique string (max 128): a repeat with the
                same key returns the first answer.
            confirm: Must be true.
            **params: Any other API field, by its API name.
        """
        return self._op("transferTelegramBusinessStars", params, user=user, star_count=star_count, idempotency_key=idempotency_key, confirm=confirm)

    # ---- Content Upload ----
    def analyze_shorts(self, video: Any, **params) -> Dict:
        """AI titles and captions for a short video.

        Watches the video and writes a title/description (YouTube) and captions
        (Instagram, TikTok, Facebook). Counts against the monthly AI Shorts quota (a
        failed analysis is not counted).

        ``POST /api/uploadposts/analyze-shorts``

        Args:
            video: Max 100 MB and 5 minutes.
            platforms (str, optional): Comma-separated: youtube, instagram, tiktok,
                facebook.
            language (str, optional): Output language (default: the video's).
            **params: Any other API field, by its API name.
        """
        return self._op("analyzeShorts", params, video=video)

    def rewrite_captions(self, content: Dict[str, Any], language: str, **params) -> Dict:
        """Translate or rewrite captions with AI.

        Rewrites texts with the same shape analyze-shorts returns into another language.
        Uses the AI Shorts quota.

        ``POST /api/uploadposts/rewrite-captions``

        Args:
            content
            language
            platforms (List[str], optional): Subset of the platforms in content
                (default all).
            **params: Any other API field, by its API name.
        """
        return self._op("rewriteCaptions", params, content=content, language=language)

    def create_media_upload(self, filename: str, content_length: int, **params) -> Dict:
        """Get a signed URL to upload a file.

        For clients that cannot send large files in a multipart request (AI agents, the
        MCP server): create the upload, PUT the bytes to upload_url with the returned
        headers, call /complete, then pass media_url to the upload endpoints. Files
        expire after staging_ttl_hours. Per-file size, files in progress and monthly
        files/bytes depend on the plan.

        ``POST /api/uploadposts/media-uploads``

        Args:
            media_type (str, optional)
            filename: With an allowed extension (video: mp4, mov, m4v, webm, mpeg,
                mpg, avi, mkv; image: jpg, jpeg, png, webp, gif; document: pdf, ppt,
                pptx, doc, docx).
            content_type (str, optional): MIME type matching media_type.
            content_length: Size in bytes.
            source (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("createMediaUpload", params, filename=filename, content_length=content_length)

    def complete_media_upload(self, upload_id: str, **params) -> Dict:
        """Confirm a signed upload.

        Checks the uploaded object (size, type) and returns media_url.

        ``POST /api/uploadposts/media-uploads/{upload_id}/complete``

        Args:
            upload_id: Upload id.
            **params: Any other API field, by its API name.
        """
        return self._op("completeMediaUpload", params, upload_id=upload_id)

    def get_media_upload(self, upload_id: str, **params) -> Dict:
        """Get a signed upload.

        ``GET /api/uploadposts/media-uploads/{upload_id}``

        Args:
            upload_id: Upload id.
            include_url (bool, optional): Include media_url (when uploaded).
            **params: Any other API field, by its API name.
        """
        return self._op("getMediaUpload", params, upload_id=upload_id)

    def delete_media_upload(self, upload_id: str, **params) -> Dict:
        """Delete a signed upload.

        ``DELETE /api/uploadposts/media-uploads/{upload_id}``

        Args:
            upload_id: Upload id.
            **params: Any other API field, by its API name.
        """
        return self._op("deleteMediaUpload", params, upload_id=upload_id)

    # ---- Upload Management ----
    def get_scheduled_post(self, job_id: str, **params) -> Dict:
        """Get a scheduled post.

        The options a scheduled post was scheduled with (limited to what PATCH can
        change), signed media URLs and whether it can still be edited.

        ``GET /api/uploadposts/schedule/{job_id}``

        Args:
            job_id: The unique job identifier.
            **params: Any other API field, by its API name.
        """
        return self._op("getScheduledPost", params, job_id=job_id)

    def get_scheduled_post_thumbnail(self, job_id: str, **params) -> Dict:
        """Get a scheduled post's thumbnail.

        Signed URL of a small JPEG of the post's video or first image. A post without
        one gets it built once and kept. Call it only for posts you display; the list
        already carries most thumbnails.

        ``GET /api/uploadposts/schedule/{job_id}/thumbnail``

        Args:
            job_id: The unique job identifier.
            **params: Any other API field, by its API name.
        """
        return self._op("getScheduledPostThumbnail", params, job_id=job_id)

    def get_scheduled_post_preview(self, job_id: str, **params) -> Dict:
        """Preview URLs of a scheduled post.

        Signed, short-lived URLs of the media, cover and thumbnail of one scheduled job
        (the listing only says has_preview).

        ``GET /api/uploadposts/schedule/{job_id}/preview``

        Args:
            job_id: The unique job identifier.
            **params: Any other API field, by its API name.
        """
        return self._op("getScheduledPostPreview", params, job_id=job_id)

    # ---- Platform Integration ----
    def create_pinterest_board(self, name: str, **params) -> Dict:
        """Create a Pinterest board.

        Without a profile the first profile of the account with a Pinterest account is
        used.

        ``POST /api/uploadposts/pinterest/boards``

        Args:
            profile (str, optional): Profile username (alias user); default the
                first profile with Pinterest.
            user (str, optional): Alias of profile.
            name
            description (str, optional)
            privacy (str, optional): SECRET is rejected (400).
            **params: Any other API field, by its API name.
        """
        return self._op("createPinterestBoard", params, name=name)

    def query_youtube_analytics(self, user: str, start_date: str, end_date: str, metrics: str, **params) -> Dict:
        """Run a YouTube Analytics channel report.

        Not generally available yet. Answers 503 youtube_analytics_disabled until it is
        enabled. reports.query for the profile's channel with any dimensions, metrics,
        filters and sort of YouTube's channel reports. Validated against the official
        report tables before it reaches YouTube (invalid combinations: 400
        youtube_analytics_unsupported_query with hints, nothing spent). Revenue and ad
        metrics are not available. Answers are cached (12 h; 7 days for ranges that
        ended more than 5 days ago). Each uncached call counts 1 request of the
        account's daily Analytics allowance. Data has a 48-72 h delay.

        ``GET /api/uploadposts/youtube/analytics/query``

        Args:
            user: Profile username with a YouTube channel connected.
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            metrics: Comma-separated metrics.
            dimensions (str, optional): Comma-separated dimensions.
            filters (str, optional): dimension==value joined with ';'
                (video/playlist accept up to 500 comma-separated IDs).
            sort (str, optional): Comma-separated; '-' for descending.
            max_results (int, optional)
            start_index (int, optional)
            report (str, optional): Optional report ID from GET
                /uploadposts/youtube/analytics/reports.
            **params: Any other API field, by its API name.
        """
        return self._op("queryYoutubeAnalytics", params, user=user, start_date=start_date, end_date=end_date, metrics=metrics)

    def list_youtube_analytics_reports(self, user: str, **params) -> Dict:
        """YouTube Analytics report catalog.

        Not generally available yet. Answers 503 youtube_analytics_disabled until it is
        enabled. The 47 YouTube channel reports with their dimensions, metrics, filters,
        sort options and row limits. Does not call YouTube.

        ``GET /api/uploadposts/youtube/analytics/reports``

        Args:
            user: Profile username with a YouTube channel connected.
            **params: Any other API field, by its API name.
        """
        return self._op("listYoutubeAnalyticsReports", params, user=user)

    def list_youtube_analytics_groups(self, user: str, **params) -> Dict:
        """List YouTube Analytics groups.

        Not generally available yet. Answers 503 youtube_analytics_disabled until it is
        enabled. groups.list of the channel (mine=true, or ids). Cached 30 minutes; 1
        request of the Analytics allowance per uncached call.

        ``GET /api/uploadposts/youtube/analytics/groups``

        Args:
            user: Profile username with a YouTube channel connected.
            ids (str, optional): Up to 50 group IDs, comma separated.
            page_token (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("listYoutubeAnalyticsGroups", params, user=user)

    def list_youtube_analytics_group_items(self, group_id: str, user: str, **params) -> Dict:
        """List the items of a YouTube Analytics group.

        Not generally available yet. Answers 503 youtube_analytics_disabled until it is
        enabled. groupItems.list. Cached 30 minutes.

        ``GET /api/uploadposts/youtube/analytics/groups/{group_id}/items``

        Args:
            group_id: Group ID.
            user: Profile username with a YouTube channel connected.
            **params: Any other API field, by its API name.
        """
        return self._op("listYoutubeAnalyticsGroupItems", params, group_id=group_id, user=user)

    def get_youtube_analytics_usage(self, **params) -> Dict:
        """Daily allowance of YouTube Analytics and bulk reports.

        Not generally available yet. Off by default: answers `503` with
        `youtube_feature_disabled` until the feature is available.

        The caller's own usage today of the Analytics and bulk reports allowances. While
        Analytics and bulk reports are not generally available yet, each service shows
        enabled: false.

        ``GET /api/uploadposts/youtube/analytics/usage``

        Any API field goes in ``**params`` by its API name.
        """
        return self._op("getYoutubeAnalyticsUsage", params)

    def list_youtube_report_types(self, user: str, **params) -> Dict:
        """List YouTube bulk report types.

        Not generally available yet. Answers 503 youtube_reporting_disabled until it is
        enabled. reportTypes.list for the channel (one page, cached 24 h).
        can_create_job marks the channel/playlist types that can be scheduled.

        ``GET /api/uploadposts/youtube/reporting/report-types``

        Args:
            user: Profile username with a YouTube channel connected.
            page_token (str, optional)
            page_size (int, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("listYoutubeReportTypes", params, user=user)

    def list_youtube_reporting_jobs(self, user: str, **params) -> Dict:
        """List YouTube reporting jobs.

        Not generally available yet. Answers 503 youtube_reporting_disabled until it is
        enabled. jobs.list of the channel (one page). used_by_upload_post marks the job
        behind Upload-Post's thumbnail impressions.

        ``GET /api/uploadposts/youtube/reporting/jobs``

        Args:
            user: Profile username with a YouTube channel connected.
            page_token (str, optional)
            page_size (int, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("listYoutubeReportingJobs", params, user=user)

    def create_youtube_reporting_job(self, user: str, report_type_id: str, **params) -> Dict:
        """Create a YouTube reporting job.

        Not generally available yet. Answers 503 youtube_reporting_disabled until it is
        enabled. jobs.create: YouTube then generates one CSV per day (first ones within
        ~48 h, covering the previous 30 days). One job per report type and up to 20 per
        channel.

        ``POST /api/uploadposts/youtube/reporting/jobs``

        Args:
            user
            report_type_id
            name (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("createYoutubeReportingJob", params, user=user, report_type_id=report_type_id)

    def get_youtube_reporting_job(self, job_id: str, user: str, **params) -> Dict:
        """Get a YouTube reporting job.

        Not generally available yet. Answers 503 youtube_reporting_disabled until it is
        enabled. jobs.get.

        ``GET /api/uploadposts/youtube/reporting/jobs/{job_id}``

        Args:
            job_id: Job ID.
            user: Profile username with a YouTube channel connected.
            **params: Any other API field, by its API name.
        """
        return self._op("getYoutubeReportingJob", params, job_id=job_id, user=user)

    def delete_youtube_reporting_job(self, job_id: str, user: str, confirm: bool, **params) -> Dict:
        """Delete a YouTube reporting job.

        Not generally available yet. Answers 503 youtube_reporting_disabled until it is
        enabled. jobs.delete: stops the daily reports. Requires confirm: true. A
        channel_reach_basic_a1 job (used by Upload-Post for thumbnail impressions)
        cannot be deleted (409 youtube_reporting_job_in_use). 502
        youtube_write_outcome_unknown: list the jobs to check.

        ``DELETE /api/uploadposts/youtube/reporting/jobs/{job_id}``

        Args:
            job_id: Job ID.
            user
            confirm
            **params: Any other API field, by its API name.
        """
        return self._op("deleteYoutubeReportingJob", params, job_id=job_id, user=user, confirm=confirm)

    def list_youtube_reports(self, job_id: str, user: str, **params) -> Dict:
        """List the reports of a YouTube reporting job.

        Not generally available yet. Answers 503 youtube_reporting_disabled until it is
        enabled. jobs.reports.list (one page). Each item has download_path.

        ``GET /api/uploadposts/youtube/reporting/jobs/{job_id}/reports``

        Args:
            job_id: Job ID.
            user: Profile username with a YouTube channel connected.
            created_after (str, optional): RFC 3339
            start_time_at_or_after (str, optional): RFC 3339
            start_time_before (str, optional): RFC 3339
            page_token (str, optional)
            page_size (int, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("listYoutubeReports", params, job_id=job_id, user=user)

    def get_youtube_report(self, job_id: str, report_id: str, user: str, **params) -> Dict:
        """Get a YouTube report.

        Not generally available yet. Answers 503 youtube_reporting_disabled until it is
        enabled. jobs.reports.get (metadata).

        ``GET /api/uploadposts/youtube/reporting/jobs/{job_id}/reports/{report_id}``

        Args:
            job_id: Job ID.
            report_id: Report ID.
            user: Profile username with a YouTube channel connected.
            **params: Any other API field, by its API name.
        """
        return self._op("getYoutubeReport", params, job_id=job_id, report_id=report_id, user=user)

    def download_youtube_report(self, job_id: str, report_id: str, user: str, **params) -> str:
        """Download a YouTube report (CSV).

        Not generally available yet. Answers 503 youtube_reporting_disabled until it is
        enabled. The report's CSV file, streamed. Up to 100 MB; up to 2 downloads at a
        time per account. Counts 2 requests of the bulk reports allowance.

        ``GET /api/uploadposts/youtube/reporting/jobs/{job_id}/reports/{report_id}/download``
        Returns the file as text.

        Args:
            job_id: Job ID.
            report_id: Report ID.
            user: Profile username with a YouTube channel connected.
            **params: Any other API field, by its API name.
        """
        return self._op("downloadYoutubeReport", params, job_id=job_id, report_id=report_id, user=user)

    def get_youtube_push(self, user: str, **params) -> Dict:
        """YouTube new video notifications status.

        Not generally available yet. Answers 503 youtube_feature_disabled until it is
        enabled. State of the push subscription of the profile's channel (null when
        off). No YouTube quota.

        ``GET /api/uploadposts/youtube/push``

        Args:
            user: Profile username with a YouTube channel connected.
            **params: Any other API field, by its API name.
        """
        return self._op("getYoutubePush", params, user=user)

    def enable_youtube_push(self, user: str, **params) -> Dict:
        """Turn on YouTube new video notifications.

        Not generally available yet. Answers 503 youtube_feature_disabled until it is
        enabled. Requires a webhook listing youtube_video_published and/or
        youtube_video_updated. No YouTube quota.

        ``POST /api/uploadposts/youtube/push``

        Args:
            user: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("enableYoutubePush", params, user=user)

    def disable_youtube_push(self, user: str, **params) -> Dict:
        """Turn off YouTube new video notifications.

        Not generally available yet. Answers 503 youtube_feature_disabled until it is
        enabled. No YouTube quota.

        ``DELETE /api/uploadposts/youtube/push``

        Args:
            user: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("disableYoutubePush", params, user=user)

    def get_instagram_publishing_limit(self, profile: str, **params) -> Dict:
        """Instagram publishing quota.

        Instagram content publishing usage of the connected account (Instagram allows a
        limited number of posts per 24 h). Cached; refresh=true skips the cache.

        ``GET /api/uploadposts/instagram/publishing_limit``

        Args:
            profile: Profile username (alias user).
            refresh (bool, optional): Skip the cache.
            **params: Any other API field, by its API name.
        """
        return self._op("getInstagramPublishingLimit", params, profile=profile)

    def get_threads_publishing_limit(self, **params) -> Dict:
        """Threads publishing quota.

        Send user or profile (one is required: 400 without both).

        ``GET /api/uploadposts/threads/publishing_limit``

        Args:
            user (str, optional): Profile username (or use profile).
            profile (str, optional): Alias of user.
            refresh (bool, optional): Skip the cache.
            **params: Any other API field, by its API name.
        """
        return self._op("getThreadsPublishingLimit", params)

    def list_pinterest_board_sections(self, board_id: str, **params) -> Dict:
        """List the sections of a Pinterest board.

        ``GET /api/uploadposts/pinterest/boards/{board_id}/sections``

        Args:
            board_id: Board id.
            profile (str, optional): Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("listPinterestBoardSections", params, board_id=board_id)

    def create_pinterest_board_section(self, board_id: str, name: str, **params) -> Dict:
        """Create a section in a Pinterest board.

        Without a profile the first profile of the account with a Pinterest account is
        used.

        ``POST /api/uploadposts/pinterest/boards/{board_id}/sections``

        Args:
            board_id: Board id.
            profile (str, optional): Profile username (alias user); default the
                first profile with Pinterest.
            user (str, optional): Alias of profile.
            name
            **params: Any other API field, by its API name.
        """
        return self._op("createPinterestBoardSection", params, board_id=board_id, name=name)

    def get_facebook_page_info(self, user: str, **params) -> Dict:
        """Read a Facebook Page's public info.

        ``GET /api/uploadposts/facebook/page-info``

        Args:
            user: Profile username.
            page_id (str, optional): Page id (required if the account manages
                several Pages).
            **params: Any other API field, by its API name.
        """
        return self._op("getFacebookPageInfo", params, user=user)

    def update_facebook_page_info(self, user: str, **params) -> Dict:
        """Update a Facebook Page's public info.

        Only the fields sent change. validate_only: true checks without writing. Needs
        Meta's pages_manage_metadata permission (pending App Review: 403
        facebook_permission_missing until then). POST is accepted as an alias.

        ``PATCH /api/uploadposts/facebook/page-info``

        Args:
            user
            page_id (str, optional)
            validate_only (bool, optional)
            about (str, optional)
            description (str, optional)
            website (str, optional)
            phone (str, optional)
            emails (Any, optional)
            hours (Any, optional): At most 2 ranges per day.
            picture_url (str, optional)
            cover_url (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("updateFacebookPageInfo", params, user=user)

    def list_reddit_subreddits(self, profile: str, **params) -> Dict:
        """Subreddits the Reddit account belongs to.

        ``GET /api/uploadposts/reddit/subreddits``

        Args:
            profile: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("listRedditSubreddits", params, profile=profile)

    def get_reddit_post_types(self, profile: str, subreddit: str, **params) -> Dict:
        """Post types a subreddit allows.

        ``GET /api/uploadposts/reddit/post-types``

        Args:
            profile: Profile username.
            subreddit: Subreddit name without r/.
            **params: Any other API field, by its API name.
        """
        return self._op("getRedditPostTypes", params, profile=profile, subreddit=subreddit)

    def list_reddit_flairs(self, profile: str, subreddit: str, **params) -> Dict:
        """Post flairs of a subreddit.

        Pass the id as reddit_flair_id when publishing; editable flairs take
        reddit_flair_text.

        ``GET /api/uploadposts/reddit/flairs``

        Args:
            profile: Profile username.
            subreddit: Subreddit name without r/.
            **params: Any other API field, by its API name.
        """
        return self._op("listRedditFlairs", params, profile=profile, subreddit=subreddit)

    def get_reddit_detailed_posts(self, profile_username: str, **params) -> Dict:
        """Get Reddit detailed posts.

        Retrieve detailed posts from a Reddit account connected to a profile, including
        complete media information. Supports automatic pagination up to 2000 posts. The
        path ends with a slash (`/detailed-posts/`); without it the API answers a 308
        redirect.

        ``GET /api/uploadposts/reddit/detailed-posts/``

        Args:
            profile_username: Username of the profile with a connected Reddit
                account.
            **params: Any other API field, by its API name.
        """
        return self._op("getRedditDetailedPosts", params, profile_username=profile_username)

    # ---- User Management ----
    def get_user_profile(self, username: str, **params) -> Dict:
        """Get a specific user profile.

        Retrieve information for a single user profile by username.

        ``GET /api/uploadposts/users/{username}``

        Args:
            username: The username of the profile to retrieve.
            **params: Any other API field, by its API name.
        """
        return self._op("getUserProfile", params, username=username)

    def rename_user_profile(self, username: str, display_name: str, **params) -> Dict:
        """Rename a user profile.

        Set the profile's display_name, the label shown in the dashboard. The username
        does not change: it stays the `user` value of every API call, so history,
        scheduled posts, analytics and existing integrations keep working. An empty
        string or null removes the display name. display_name is the only editable
        field; any other field returns 400 FIELD_NOT_EDITABLE.

        ``PATCH /api/uploadposts/users/{username}``

        Args:
            username: The username of the profile to rename. It is not changed.
            display_name: New label. Trimmed; no line breaks. Empty string or null
                clears it.
            **params: Any other API field, by its API name.
        """
        return self._op("renameUserProfile", params, username=username, display_name=display_name)

    def disconnect_social_account(self, profile_username: str, social_platform: str, **params) -> Dict:
        """Disconnect a social account from a profile.

        Unlink one social platform from a user profile. Other platforms connected to the
        same profile are not touched. The stored credentials are deleted only if no
        other profile of your account still uses that social account. Fires the
        `social_account_disconnected` webhook with `reason: "manual_disconnect"`.
        Disconnecting a platform that is already disconnected returns 200.

        ``DELETE /api/uploadposts/users/social``

        Args:
            profile_username: The profile to disconnect the account from.
            social_platform: The platform key as it appears in the profile's
                `social_accounts` object (e.g. `instagram`, `tiktok`, `facebook`,
                `youtube`, `linkedin`, `x`).
            **params: Any other API field, by its API name.
        """
        return self._op("disconnectSocialAccount", params, profile_username=profile_username, social_platform=social_platform)

    def connect_discord_credentials(self, profile_username: str, webhook_url: str, **params) -> Dict:
        """Connect Discord with credentials.

        Discord channel incoming webhook (no OAuth). No OAuth and no browser redirect:
        Upload-Post validates the credentials, encrypts the secret and links the account
        to the profile. Also accepted with the profile JWT of the white-label connect
        page.

        ``POST /api/uploadposts/users/discord/credentials``

        Args:
            profile_username
            webhook_url: https://discord.com/api/webhooks/...
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectDiscordCredentials", params, profile_username=profile_username, webhook_url=webhook_url)

    def connect_telegram_credentials(self, profile_username: str, bot_token: str, chat_id: str, **params) -> Dict:
        """Connect Telegram with credentials.

        Telegram bot token + target chat. Upload-Post validates both (getMe, getChat)
        and stores the token encrypted. No OAuth and no browser redirect: Upload-Post
        validates the credentials, encrypts the secret and links the account to the
        profile. Also accepted with the profile JWT of the white-label connect page.

        ``POST /api/uploadposts/users/telegram/credentials``

        Args:
            profile_username
            bot_token
            chat_id: Public channel @username or numeric chat id.
            receive_updates (bool, optional): Also receive the bot's DMs and other
                updates (same options as POST /uploadposts/telegram/updates).
            replace_existing_webhook (bool, optional)
            forward_url (str, optional)
            auto_answer_callbacks (bool, optional)
            extra_updates (List[str], optional)
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectTelegramCredentials", params, profile_username=profile_username, bot_token=bot_token, chat_id=chat_id)

    def connect_slack_credentials(self, profile_username: str, webhook_url: str, **params) -> Dict:
        """Connect Slack with credentials.

        Slack channel Incoming Webhook URL (text only). No OAuth and no browser
        redirect: Upload-Post validates the credentials, encrypts the secret and links
        the account to the profile. Also accepted with the profile JWT of the
        white-label connect page.

        ``POST /api/uploadposts/users/slack/credentials``

        Args:
            profile_username
            webhook_url
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectSlackCredentials", params, profile_username=profile_username, webhook_url=webhook_url)

    def connect_mastodon_credentials(self, profile_username: str, instance_url: str, access_token: str, **params) -> Dict:
        """Connect Mastodon with credentials.

        Mastodon instance access token. No OAuth and no browser redirect: Upload-Post
        validates the credentials, encrypts the secret and links the account to the
        profile. Also accepted with the profile JWT of the white-label connect page.

        ``POST /api/uploadposts/users/mastodon/credentials``

        Args:
            profile_username
            instance_url
            access_token
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectMastodonCredentials", params, profile_username=profile_username, instance_url=instance_url, access_token=access_token)

    def connect_nostr_credentials(self, profile_username: str, private_key: str, **params) -> Dict:
        """Connect Nostr with credentials.

        Nostr private key (nsec or hex) and optional relays. No OAuth and no browser
        redirect: Upload-Post validates the credentials, encrypts the secret and links
        the account to the profile. Also accepted with the profile JWT of the
        white-label connect page.

        ``POST /api/uploadposts/users/nostr/credentials``

        Args:
            profile_username
            private_key
            relays (str, optional): Comma-separated wss:// relays (defaults used if
                omitted).
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectNostrCredentials", params, profile_username=profile_username, private_key=private_key)

    def connect_lemmy_credentials(self, profile_username: str, instance_url: str, username: str, password: str, community: str, **params) -> Dict:
        """Connect Lemmy with credentials.

        Lemmy instance, login and target community. No OAuth and no browser redirect:
        Upload-Post validates the credentials, encrypts the secret and links the account
        to the profile. Also accepted with the profile JWT of the white-label connect
        page.

        ``POST /api/uploadposts/users/lemmy/credentials``

        Args:
            profile_username
            instance_url
            username
            password
            community
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectLemmyCredentials", params, profile_username=profile_username, instance_url=instance_url, username=username, password=password, community=community)

    def connect_devto_credentials(self, profile_username: str, api_key: str, **params) -> Dict:
        """Connect Dev.to with credentials.

        Dev.to API key. No OAuth and no browser redirect: Upload-Post validates the
        credentials, encrypts the secret and links the account to the profile. Also
        accepted with the profile JWT of the white-label connect page.

        ``POST /api/uploadposts/users/devto/credentials``

        Args:
            profile_username
            api_key
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectDevToCredentials", params, profile_username=profile_username, api_key=api_key)

    def connect_hashnode_credentials(self, profile_username: str, pat: str, publication_id: str, **params) -> Dict:
        """Connect Hashnode with credentials.

        Hashnode Personal Access Token and publication id. No OAuth and no browser
        redirect: Upload-Post validates the credentials, encrypts the secret and links
        the account to the profile. Also accepted with the profile JWT of the
        white-label connect page.

        ``POST /api/uploadposts/users/hashnode/credentials``

        Args:
            profile_username
            pat
            publication_id
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectHashnodeCredentials", params, profile_username=profile_username, pat=pat, publication_id=publication_id)

    def connect_wordpress_credentials(self, profile_username: str, site_url: str, username: str, application_password: str, **params) -> Dict:
        """Connect WordPress with credentials.

        Self-hosted WordPress site, username and Application Password. No OAuth and no
        browser redirect: Upload-Post validates the credentials, encrypts the secret and
        links the account to the profile. Also accepted with the profile JWT of the
        white-label connect page.

        ``POST /api/uploadposts/users/wordpress/credentials``

        Args:
            profile_username
            site_url
            username
            application_password
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectWordPressCredentials", params, profile_username=profile_username, site_url=site_url, username=username, application_password=application_password)

    def connect_whop_credentials(self, profile_username: str, api_key: str, experience_id: str, **params) -> Dict:
        """Connect Whop with credentials.

        Whop API key (forum:post:create) and experience id. No OAuth and no browser
        redirect: Upload-Post validates the credentials, encrypts the secret and links
        the account to the profile. Also accepted with the profile JWT of the
        white-label connect page.

        ``POST /api/uploadposts/users/whop/credentials``

        Args:
            profile_username
            api_key
            experience_id
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectWhopCredentials", params, profile_username=profile_username, api_key=api_key, experience_id=experience_id)

    def connect_listmonk_credentials(self, profile_username: str, instance_url: str, username: str, password: str, list_id: str, **params) -> Dict:
        """Connect Listmonk with credentials.

        Listmonk instance, login and list id (each post sends a campaign). No OAuth and
        no browser redirect: Upload-Post validates the credentials, encrypts the secret
        and links the account to the profile. Also accepted with the profile JWT of the
        white-label connect page.

        ``POST /api/uploadposts/users/listmonk/credentials``

        Args:
            profile_username
            instance_url
            username
            password
            list_id
            name (str, optional): Display name of the connection.
            **params: Any other API field, by its API name.
        """
        return self._op("connectListmonkCredentials", params, profile_username=profile_username, instance_url=instance_url, username=username, password=password, list_id=list_id)

    def list_facebook_page_choices(self, profile_username: str, **params) -> Dict:
        """List the Facebook Pages a profile can publish to.

        Every Facebook Page of the profile's connected account and the one selected for
        publishing.

        ``GET /api/uploadposts/users/facebook-page``

        Args:
            profile_username: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("listFacebookPageChoices", params, profile_username=profile_username)

    def set_facebook_page(self, profile_username: str, facebook_page_id: str, **params) -> Dict:
        """Select the Facebook Page used when publishing.

        ``POST /api/uploadposts/users/facebook-page``

        Args:
            profile_username
            facebook_page_id
            **params: Any other API field, by its API name.
        """
        return self._op("setFacebookPage", params, profile_username=profile_username, facebook_page_id=facebook_page_id)

    def clear_facebook_page(self, profile_username: str, **params) -> Dict:
        """Clear the selected Facebook Page.

        Back to the default (the first one of the account).

        ``DELETE /api/uploadposts/users/facebook-page``

        Args:
            profile_username
            **params: Any other API field, by its API name.
        """
        return self._op("clearFacebookPage", params, profile_username=profile_username)

    def list_linkedin_page_choices(self, profile_username: str, **params) -> Dict:
        """List the LinkedIn Pages a profile can publish to.

        Every LinkedIn Page of the profile's connected account and the one selected for
        publishing.

        ``GET /api/uploadposts/users/linkedin-page``

        Args:
            profile_username: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("listLinkedInPageChoices", params, profile_username=profile_username)

    def set_linkedin_page(self, profile_username: str, linkedin_page_id: str, **params) -> Dict:
        """Select the LinkedIn Page used when publishing.

        ``POST /api/uploadposts/users/linkedin-page``

        Args:
            profile_username
            linkedin_page_id
            **params: Any other API field, by its API name.
        """
        return self._op("setLinkedInPage", params, profile_username=profile_username, linkedin_page_id=linkedin_page_id)

    def clear_linkedin_page(self, profile_username: str, **params) -> Dict:
        """Clear the selected LinkedIn Page.

        Back to the default (the first one of the account).

        ``DELETE /api/uploadposts/users/linkedin-page``

        Args:
            profile_username
            **params: Any other API field, by its API name.
        """
        return self._op("clearLinkedInPage", params, profile_username=profile_username)

    def connect_bluesky_credentials(self, profile_username: str, handle: str, password: str, **params) -> Dict:
        """Connect Bluesky with an app password.

        Logs in to Bluesky with the handle and an app password, stores the password
        encrypted and links the account to the profile. Also accepted with the profile
        JWT of the connect page.

        ``POST /api/uploadposts/users/bluesky/credentials``

        Args:
            profile_username
            handle
            password: Bluesky app password (one with DM access to use Bluesky DMs).
            **params: Any other API field, by its API name.
        """
        return self._op("connectBlueskyCredentials", params, profile_username=profile_username, handle=handle, password=password)

    def set_youtube_oauth_client(self, profile_username: str, client_id: str, client_secret: str, **params) -> Dict:
        """Use your own Google OAuth client for a profile's YouTube.

        Stores (encrypted) the client_id and client_secret of your own Google Cloud
        OAuth client; that profile then authorizes YouTube against it (its own API
        quota).

        ``POST /api/uploadposts/users/youtube/credentials``

        Args:
            profile_username
            client_id
            client_secret
            **params: Any other API field, by its API name.
        """
        return self._op("setYoutubeOAuthClient", params, profile_username=profile_username, client_id=client_id, client_secret=client_secret)

    # ---- Authentication ----
    def get_current_user(self, **params) -> Dict:
        """Get current user.

        Verify the validity of your API key and retrieve basic account information
        including email and subscription plan.

        ``GET /api/uploadposts/me``

        Any API field goes in ``**params`` by its API name.
        """
        return self._op("getCurrentUser", params)

    def start_oauth_connection(self, platform: str, **params) -> Dict:
        """Connect API: start connecting a social account.

        Build your own connect page: returns the platform's authorize_url for a profile.
        Send the user there; Upload-Post finishes the OAuth and sends them back to
        redirect_url. Authenticate with the API key (then `profile` is required) or with
        the profile JWT of POST /uploadposts/users/generate-jwt (profile taken from the
        token). The state is single-use: a retry needs a new start.

        ``POST /api/uploadposts/oauth/{platform}/start``

        Args:
            platform: Platform to connect.
            profile (str, optional): Profile username (API key auth only).
            redirect_url (str, optional): Absolute http(s) URL to return to.
            **params: Any other API field, by its API name.
        """
        return self._op("startOAuthConnection", params, platform=platform)

    # ---- FFmpeg Editor ----
    def create_ffmpeg_job(self, full_command: str, output_extension: str, **params) -> Dict:
        """Create FFmpeg job.

        Submit a media processing job using an FFmpeg command template. Supports single
        or multiple input files via multipart upload or JSON with URLs. Jobs are
        asynchronous — poll the status endpoint until finished.

        ``POST /api/uploadposts/ffmpeg/jobs/upload``

        Args:
            files (List[str], optional): Array of input file URLs. Referenced as
                {input0}, {input1}, etc.
            full_command: FFmpeg command template using {input0}, {input1}, etc. and
                {output} placeholders.
            output_extension: Desired output file extension.
            publish (bool, optional): Whether to publish the result.
            file (Any, optional): Primary media file to process. Referenced as
                {input} or {input0}.
            file1 (Any, optional): Second input file. Referenced as {input1}.
            file2 (Any, optional): Third input file. Referenced as {input2}.
            **params: Any other API field, by its API name.
        """
        return self._op("createFfmpegJob", params, full_command=full_command, output_extension=output_extension)

    def get_ffmpeg_job_status(self, job_id: str, **params) -> Dict:
        """Get FFmpeg job status.

        Poll the status of an FFmpeg processing job. Statuses: PENDING, PROCESSING,
        FINISHED, ERROR.

        ``GET /api/uploadposts/ffmpeg/jobs/{job_id}``

        Args:
            job_id: The unique job identifier.
            **params: Any other API field, by its API name.
        """
        return self._op("getFfmpegJobStatus", params, job_id=job_id)

    def download_ffmpeg_result(self, job_id: str, **params) -> bytes:
        """Download FFmpeg result.

        Download the processed file when job status is FINISHED. Returns binary media
        with appropriate Content-Type and Content-Disposition headers.

        ``GET /api/uploadposts/ffmpeg/jobs/{job_id}/download``
        Returns the file as bytes.

        Args:
            job_id: The unique job identifier.
            **params: Any other API field, by its API name.
        """
        return self._op("downloadFfmpegResult", params, job_id=job_id)

    def get_ffmpeg_consumption(self, **params) -> Dict:
        """Get FFmpeg consumption.

        Check your current FFmpeg usage, remaining quota, and processing history for the
        current month.

        ``GET /api/uploadposts/ffmpeg/consumption``

        Any API field goes in ``**params`` by its API name.
        """
        return self._op("getFfmpegConsumption", params)

    # ---- Webhooks ----
    def list_webhook_subscriptions(self, **params) -> Dict:
        """List webhook subscriptions.

        Not generally available yet. While webhook subscriptions are switched off for
        your account every route of this group answers `503` with `reason:
        webhook_subscriptions_disabled`.

        Newest first, active and disabled. An n8n trigger checks whether its
        subscription exists with `?url=<its url>&status=active`.

        ``GET /api/uploadposts/webhooks/subscriptions``

        Args:
            status (str, optional): Only active or disabled ones.
            source (str, optional): Only this source label (e.g. n8n).
            url (str, optional): Only this exact URL.
            **params: Any other API field, by its API name.
        """
        return self._op("listWebhookSubscriptions", params)

    def create_webhook_subscription(self, url: str, events: List[str], **params) -> Dict:
        """Create a webhook subscription.

        Not generally available yet. While webhook subscriptions are switched off for
        your account every route of this group answers `503` with `reason:
        webhook_subscriptions_disabled`.

        Adds a destination that receives the listed events, besides the account webhook.
        Idempotent: the same url + events + profile_username returns the existing
        subscription (200, `created: false`) and reactivates it if it was disabled
        (`reactivated: true`); `name` and `source` are updated when sent. At most 10
        active subscriptions per account. Team members (X-Act-As-User) cannot create
        them.

        ``POST /api/uploadposts/webhooks/subscriptions``

        Args:
            url: Public https URL.
            events: Event names. youtube_video_* only while YouTube push is on and
                post_approval_* only while post approvals are on; otherwise 400
                invalid_events with allowed_events.
            profile_username (str, optional): Only events of this profile.
            source (str, optional)
            name (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("createWebhookSubscription", params, url=url, events=events)

    def get_webhook_subscription(self, subscription_id: str, **params) -> Dict:
        """Get a webhook subscription.

        Not generally available yet. While webhook subscriptions are switched off for
        your account every route of this group answers `503` with `reason:
        webhook_subscriptions_disabled`.

        ``GET /api/uploadposts/webhooks/subscriptions/{subscription_id}``

        Args:
            subscription_id: Subscription id (whsub_...).
            **params: Any other API field, by its API name.
        """
        return self._op("getWebhookSubscription", params, subscription_id=subscription_id)

    def delete_webhook_subscription(self, subscription_id: str, **params) -> Dict:
        """Delete a webhook subscription.

        Not generally available yet. While webhook subscriptions are switched off for
        your account every route of this group answers `503` with `reason:
        webhook_subscriptions_disabled`.

        Stops sending to it right away. A second DELETE answers 404 (an integration can
        treat 404 as already deleted).

        ``DELETE /api/uploadposts/webhooks/subscriptions/{subscription_id}``

        Args:
            subscription_id: Subscription id (whsub_...).
            **params: Any other API field, by its API name.
        """
        return self._op("deleteWebhookSubscription", params, subscription_id=subscription_id)

    def test_webhook_subscription(self, subscription_id: str, **params) -> Dict:
        """Send a test event to a subscription.

        Not generally available yet. While webhook subscriptions are switched off for
        your account every route of this group answers `503` with `reason:
        webhook_subscriptions_disabled`.

        Sends one signed sample now, with the keys of the real event and `test: true`.
        Logged as a test delivery: never retried and never counted towards disabling the
        subscription. `ok` tells whether the destination answered 2xx. For the post
        approval events the sample has the shape of the real event ({event, user_email,
        profile_username, approval: {...}, created_at}).

        ``POST /api/uploadposts/webhooks/subscriptions/{subscription_id}/test``

        Args:
            subscription_id: Subscription id (whsub_...).
            event (str, optional): One of the subscription's events; default its
                first event.
            **params: Any other API field, by its API name.
        """
        return self._op("testWebhookSubscription", params, subscription_id=subscription_id)

    def test_notifications(self, **params) -> Dict:
        """Send a test notification.

        Sends a sample upload_completed through the configured channels (logged as a
        test delivery, never retried). Only our own outcome per channel is returned,
        never the destination's answer.

        ``POST /api/uploadposts/users/notifications/test``

        Args:
            platform (str, optional)
            media_type (str, optional)
            title (str, optional)
            caption (str, optional)
            profile_username (str, optional)
            message (str, optional): Telegram text (default: built from the other
                fields).
            result (Dict[str, Any], optional)
            **params: Any other API field, by its API name.
        """
        return self._op("testNotifications", params)

    # ---- Instagram Interactions ----
    def delete_comment_post(self, platform: str, user: str, comment_id: str, **params) -> Dict:
        """Delete a comment (POST alias).

        POST alias of DELETE /uploadposts/comments/delete, for clients that cannot send
        a body with DELETE. Same body and behavior.

        ``POST /api/uploadposts/comments/delete``

        Args:
            platform: Target platform.
            user: Profile username as configured in Upload-Post.
            comment_id: ID of the comment to delete.
            post_id (str, optional): Required for LinkedIn only — the post URN
                (urn:li:ugcPost:...) the comment belongs to.
            **params: Any other API field, by its API name.
        """
        return self._op("deleteCommentPost", params, platform=platform, user=user, comment_id=comment_id)

    def delete_bluesky_chat_account(self, user: str, confirm: bool, confirm_handle: str, **params) -> Dict:
        """Delete the Bluesky chat account.

        Not generally available yet. Answers `403` `bluesky_chat_delete_disabled`.

        Deletes every conversation and message of the account's Bluesky chat account
        (not the Bluesky account). Needs confirm: true and confirm_handle; not enabled
        yet (403 bluesky_chat_delete_disabled). Account owner only; every attempt is
        recorded.

        ``POST /api/uploadposts/dms/bluesky/account/delete``

        Args:
            user: Profile username.
            confirm
            confirm_handle
            **params: Any other API field, by its API name.
        """
        return self._op("deleteBlueskyChatAccount", params, user=user, confirm=confirm, confirm_handle=confirm_handle)

    def list_bluesky_mutual_groups(self, user: str, subject: str, **params) -> Dict:
        """Bluesky groups shared with someone.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        Experimental on Bluesky: answers carry experimental: true; 403
        bluesky_dm_experimental_disabled while not enabled.

        ``GET /api/uploadposts/dms/bluesky/groups``

        Args:
            user: Profile username as configured in Upload-Post.
            subject
            limit (int, optional)
            cursor (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("listBlueskyMutualGroups", params, user=user, subject=subject)

    def create_bluesky_group(self, user: str, name: str, members: List[str], **params) -> Dict:
        """Create a Bluesky group chat.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        Members get a request to accept. Every invited member counts as one DM (all or
        nothing); at most 10 members by handle per request. Idempotent for 10 minutes
        per idempotency_key (or name + members). Experimental on Bluesky: answers carry
        experimental: true; 403 bluesky_dm_experimental_disabled while not enabled.

        ``POST /api/uploadposts/dms/bluesky/groups``

        Args:
            user: Profile username.
            name
            members
            idempotency_key (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("createBlueskyGroup", params, user=user, name=name, members=members)

    def edit_bluesky_group(self, conversation_id: str, user: str, **params) -> Dict:
        """Rename, lock or unlock a Bluesky group.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        Owner only. Experimental on Bluesky: answers carry experimental: true; 403
        bluesky_dm_experimental_disabled while not enabled.

        ``PATCH /api/uploadposts/dms/bluesky/groups/{conversation_id}``

        Args:
            conversation_id
            user: Profile username.
            name (str, optional)
            locked (bool, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("editBlueskyGroup", params, conversation_id=conversation_id, user=user)

    def list_bluesky_group_members(self, conversation_id: str, user: str, **params) -> Dict:
        """Bluesky group members.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        Experimental on Bluesky: answers carry experimental: true; 403
        bluesky_dm_experimental_disabled while not enabled.

        ``GET /api/uploadposts/dms/bluesky/groups/{conversation_id}/members``

        Args:
            conversation_id
            user: Profile username as configured in Upload-Post.
            **params: Any other API field, by its API name.
        """
        return self._op("listBlueskyGroupMembers", params, conversation_id=conversation_id, user=user)

    def add_bluesky_group_members(self, conversation_id: str, user: str, members: List[str], **params) -> Dict:
        """Add members to a Bluesky group.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        Owner only. One DM of quota per added member. Experimental on Bluesky: answers
        carry experimental: true; 403 bluesky_dm_experimental_disabled while not
        enabled.

        ``POST /api/uploadposts/dms/bluesky/groups/{conversation_id}/members``

        Args:
            conversation_id
            user: Profile username.
            members
            **params: Any other API field, by its API name.
        """
        return self._op("addBlueskyGroupMembers", params, conversation_id=conversation_id, user=user, members=members)

    def remove_bluesky_group_members(self, conversation_id: str, user: str, members: List[str], **params) -> Dict:
        """Remove members from a Bluesky group.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        Owner only. Experimental on Bluesky: answers carry experimental: true; 403
        bluesky_dm_experimental_disabled while not enabled.

        ``DELETE /api/uploadposts/dms/bluesky/groups/{conversation_id}/members``

        Args:
            conversation_id
            user: Profile username.
            members
            **params: Any other API field, by its API name.
        """
        return self._op("removeBlueskyGroupMembers", params, conversation_id=conversation_id, user=user, members=members)

    def manage_bluesky_join_link(self, conversation_id: str, user: str, action: str, **params) -> Dict:
        """Manage a Bluesky group join link.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        action: create, edit, enable or disable. Experimental on Bluesky: answers carry
        experimental: true; 403 bluesky_dm_experimental_disabled while not enabled.

        ``POST /api/uploadposts/dms/bluesky/groups/{conversation_id}/join-link``

        Args:
            conversation_id
            user: Profile username.
            action
            require_approval (bool, optional)
            join_rule (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("manageBlueskyJoinLink", params, conversation_id=conversation_id, user=user, action=action)

    def list_bluesky_join_requests(self, conversation_id: str, user: str, **params) -> Dict:
        """Pending requests to join a Bluesky group.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        Owner only. Experimental on Bluesky: answers carry experimental: true; 403
        bluesky_dm_experimental_disabled while not enabled.

        ``GET /api/uploadposts/dms/bluesky/groups/{conversation_id}/join-requests``

        Args:
            conversation_id
            user: Profile username as configured in Upload-Post.
            **params: Any other API field, by its API name.
        """
        return self._op("listBlueskyJoinRequests", params, conversation_id=conversation_id, user=user)

    def answer_bluesky_join_request(self, conversation_id: str, user: str, action: str, **params) -> Dict:
        """Answer or withdraw a Bluesky join request.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        action: approve / reject (with member), mark_read, or withdraw (your own
        request). Experimental on Bluesky: answers carry experimental: true; 403
        bluesky_dm_experimental_disabled while not enabled.

        ``POST /api/uploadposts/dms/bluesky/groups/{conversation_id}/join-requests``

        Args:
            conversation_id
            user: Profile username.
            action
            member (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("answerBlueskyJoinRequest", params, conversation_id=conversation_id, user=user, action=action)

    def preview_bluesky_join_links(self, user: str, codes: str, **params) -> Dict:
        """Preview Bluesky join links.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        Up to 50 codes; status active, disabled or invalid. Experimental on Bluesky:
        answers carry experimental: true; 403 bluesky_dm_experimental_disabled while not
        enabled.

        ``GET /api/uploadposts/dms/bluesky/join-links``

        Args:
            user: Profile username as configured in Upload-Post.
            codes: Comma-separated join link codes.
            **params: Any other API field, by its API name.
        """
        return self._op("previewBlueskyJoinLinks", params, user=user, codes=codes)

    def join_bluesky_group(self, user: str, code: str, **params) -> Dict:
        """Ask to join a Bluesky group.

        Not generally available yet. Group chats answer `403`
        `bluesky_dm_experimental_disabled` until they are turned on.

        status is joined or pending. Experimental on Bluesky: answers carry
        experimental: true; 403 bluesky_dm_experimental_disabled while not enabled.

        ``POST /api/uploadposts/dms/bluesky/join-links``

        Args:
            user: Profile username.
            code
            **params: Any other API field, by its API name.
        """
        return self._op("joinBlueskyGroup", params, user=user, code=code)

    def download_dm_media(self, platform: str, user: str, media_id: str, **params) -> bytes:
        """Download a DM attachment.

        Returns the file of an attachment received in a DM (the media_id in
        dm_received). Telegram: bots download up to 20 MB.

        ``GET /api/uploadposts/dms/media``
        Returns the file as bytes.

        Args:
            platform: Platform of the conversation.
            user: Profile username.
            media_id: media_id of the attachment (Telegram file_id).
            **params: Any other API field, by its API name.
        """
        return self._op("downloadDmMedia", params, platform=platform, user=user, media_id=media_id)

    # ---- Bluesky ----
    def bluesky_graph_action(self, user: str, action: str, **params) -> Dict:
        """Follow, block or mute (one target per call).

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        follow/unfollow (daily limit), block/unblock, mute/unmute (only_reposts,
        only_quoteposts), mute_list/unmute_list, block_list/unblock_list (moderation
        lists), mute_thread/unmute_thread.

        ``POST /api/uploadposts/bluesky/graph``

        Args:
            user: Profile username.
            action
            actor (str, optional): Handle, DID or bsky.app profile link.
            list (str, optional): List at:// URI, bsky.app link or own list id.
            post_id (str, optional): First post of the thread.
            only_reposts (bool, optional)
            only_quoteposts (bool, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("blueskyGraphAction", params, user=user, action=action)

    def list_bluesky_lists(self, user: str, **params) -> Dict:
        """The account's lists.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        getLists for the account.

        ``GET /api/uploadposts/bluesky/lists``

        Args:
            user: Profile username.
            purposes (str, optional)
            cursor (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("listBlueskyLists", params, user=user)

    def create_bluesky_list(self, user: str, name: str, purpose: str, **params) -> Dict:
        """Create a list.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        Curated, moderation or reference list.

        ``POST /api/uploadposts/bluesky/lists``

        Args:
            user: Profile username.
            name: Up to 64 bytes.
            purpose
            description (str, optional): Up to 300 characters.
            avatar (Any, optional): PNG or JPEG file, up to 1,000,000 bytes
                (multipart).
            avatar_url (str, optional)
            remove_avatar (bool, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("createBlueskyList", params, user=user, name=name, purpose=purpose)

    def get_bluesky_list(self, list_id: str, user: str, **params) -> Dict:
        """A list and its members.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        getList.

        ``GET /api/uploadposts/bluesky/lists/{list_id}``

        Args:
            list_id: The list's record key.
            user: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("getBlueskyList", params, list_id=list_id, user=user)

    def update_bluesky_list(self, list_id: str, user: str, **params) -> Dict:
        """Update a list.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        Merges the fields sent.

        ``PATCH /api/uploadposts/bluesky/lists/{list_id}``

        Args:
            list_id: The list's record key.
            user: Profile username.
            name (str, optional): Up to 64 bytes.
            purpose (str, optional)
            description (str, optional): Up to 300 characters.
            avatar (Any, optional): PNG or JPEG file, up to 1,000,000 bytes
                (multipart).
            avatar_url (str, optional)
            remove_avatar (bool, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("updateBlueskyList", params, list_id=list_id, user=user)

    def delete_bluesky_list(self, list_id: str, user: str, confirm: bool, **params) -> Dict:
        """Delete a list and its members.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        Needs confirm=true.

        ``DELETE /api/uploadposts/bluesky/lists/{list_id}``

        Args:
            list_id: The list's record key.
            user: Profile username.
            confirm: Must be true: this cannot be undone.
            **params: Any other API field, by its API name.
        """
        return self._op("deleteBlueskyList", params, list_id=list_id, user=user, confirm=confirm)

    def list_bluesky_list_members(self, list_id: str, user: str, **params) -> Dict:
        """List members.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        getList items.

        ``GET /api/uploadposts/bluesky/lists/{list_id}/members``

        Args:
            list_id: The list's record key.
            user: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("listBlueskyListMembers", params, list_id=list_id, user=user)

    def add_bluesky_list_member(self, list_id: str, user: str, actor: str, **params) -> Dict:
        """Add a member.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        One account per call.

        ``POST /api/uploadposts/bluesky/lists/{list_id}/members``

        Args:
            list_id: The list's record key.
            user: Profile username.
            actor
            **params: Any other API field, by its API name.
        """
        return self._op("addBlueskyListMember", params, list_id=list_id, user=user, actor=actor)

    def remove_bluesky_list_member(self, list_id: str, user: str, actor: str, **params) -> Dict:
        """Remove a member.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        One account per call.

        ``DELETE /api/uploadposts/bluesky/lists/{list_id}/members``

        Args:
            list_id: The list's record key.
            user: Profile username.
            actor
            **params: Any other API field, by its API name.
        """
        return self._op("removeBlueskyListMember", params, list_id=list_id, user=user, actor=actor)

    def opt_out_bluesky_list(self, user: str, list: str, **params) -> Dict:
        """Ask not to appear in a reference list.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        referencelistoptout.

        ``POST /api/uploadposts/bluesky/lists/opt-out``

        Args:
            user: Profile username.
            list
            **params: Any other API field, by its API name.
        """
        return self._op("optOutBlueskyList", params, user=user, list=list)

    def remove_opt_out_bluesky_list(self, user: str, list: str, **params) -> Dict:
        """Withdraw the opt-out.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        ``DELETE /api/uploadposts/bluesky/lists/opt-out``

        Args:
            user: Profile username.
            list
            **params: Any other API field, by its API name.
        """
        return self._op("removeOptOutBlueskyList", params, user=user, list=list)

    def list_bluesky_starter_packs(self, user: str, **params) -> Dict:
        """The account's starter packs.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        ``GET /api/uploadposts/bluesky/starter-packs``

        Args:
            user: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("listBlueskyStarterPacks", params, user=user)

    def create_bluesky_starter_pack(self, user: str, name: str, **params) -> Dict:
        """Create a starter pack.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        ``POST /api/uploadposts/bluesky/starter-packs``

        Args:
            user: Profile username.
            name: Up to 50 characters.
            description (str, optional)
            feeds (List[str], optional): Up to 3 feed at:// URIs.
            list (str, optional): Own list to use.
            members (List[str], optional): Up to 25 accounts per request (a new list
                is created; add more through /lists/{list_id}/members).
            **params: Any other API field, by its API name.
        """
        return self._op("createBlueskyStarterPack", params, user=user, name=name)

    def get_bluesky_starter_pack(self, pack_id: str, user: str, **params) -> Dict:
        """A starter pack.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        ``GET /api/uploadposts/bluesky/starter-packs/{pack_id}``

        Args:
            pack_id: The starter pack's record key.
            user: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("getBlueskyStarterPack", params, pack_id=pack_id, user=user)

    def update_bluesky_starter_pack(self, pack_id: str, user: str, **params) -> Dict:
        """Update a starter pack.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        name, description, feeds.

        ``PATCH /api/uploadposts/bluesky/starter-packs/{pack_id}``

        Args:
            pack_id: The starter pack's record key.
            user: Profile username.
            name (str, optional): Up to 50 characters.
            description (str, optional)
            feeds (List[str], optional): Up to 3 feed at:// URIs.
            list (str, optional): Own list to use.
            members (List[str], optional): Up to 25 accounts per request (a new list
                is created; add more through /lists/{list_id}/members).
            **params: Any other API field, by its API name.
        """
        return self._op("updateBlueskyStarterPack", params, pack_id=pack_id, user=user)

    def delete_bluesky_starter_pack(self, pack_id: str, user: str, confirm: bool, **params) -> Dict:
        """Delete a starter pack.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        Needs confirm=true; delete_list=true also deletes its list.

        ``DELETE /api/uploadposts/bluesky/starter-packs/{pack_id}``

        Args:
            pack_id: The starter pack's record key.
            user: Profile username.
            confirm: Must be true: this cannot be undone.
            delete_list (bool, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("deleteBlueskyStarterPack", params, pack_id=pack_id, user=user, confirm=confirm)

    def list_bluesky_feeds(self, user: str, **params) -> Dict:
        """Feeds declared by the account.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        ``GET /api/uploadposts/bluesky/feeds``

        Args:
            user: Profile username.
            **params: Any other API field, by its API name.
        """
        return self._op("listBlueskyFeeds", params, user=user)

    def create_bluesky_feed(self, user: str, rkey: str, did: str, display_name: str, **params) -> Dict:
        """Declare a custom feed.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        Points to a feed generator service run by someone else.

        ``POST /api/uploadposts/bluesky/feeds``

        Args:
            user: Profile username.
            rkey: 1-15 letters, digits or dashes (create only).
            did: Feed generator service DID.
            display_name: Up to 24 characters.
            description (str, optional)
            avatar (Any, optional): PNG or JPEG file, up to 1,000,000 bytes
                (multipart).
            accepts_interactions (bool, optional)
            content_mode (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("createBlueskyFeed", params, user=user, rkey=rkey, did=did, display_name=display_name)

    def update_bluesky_feed(self, rkey: str, user: str, **params) -> Dict:
        """Update a feed declaration.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        ``PATCH /api/uploadposts/bluesky/feeds/{rkey}``

        Args:
            rkey: The feed's record key.
            user: Profile username.
            did (str, optional): Feed generator service DID.
            display_name (str, optional): Up to 24 characters.
            description (str, optional)
            avatar (Any, optional): PNG or JPEG file, up to 1,000,000 bytes
                (multipart).
            accepts_interactions (bool, optional)
            content_mode (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("updateBlueskyFeed", params, rkey=rkey, user=user)

    def delete_bluesky_feed(self, rkey: str, user: str, confirm: bool, **params) -> Dict:
        """Delete a feed declaration.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        Needs confirm=true.

        ``DELETE /api/uploadposts/bluesky/feeds/{rkey}``

        Args:
            rkey: The feed's record key.
            user: Profile username.
            confirm: Must be true: this cannot be undone.
            **params: Any other API field, by its API name.
        """
        return self._op("deleteBlueskyFeed", params, rkey=rkey, user=user, confirm=confirm)

    def report_on_bluesky(self, user: str, reason_type: str, confirm: bool, **params) -> Dict:
        """Report a post or account to Bluesky moderation.

        Not generally available yet. Answers `503` `bluesky_feature_disabled` until it
        is turned on.

        Needs confirm=true. Up to 20 reports per account per UTC day.

        ``POST /api/uploadposts/bluesky/report``

        Args:
            user: Profile username.
            post_id (str, optional)
            actor (str, optional)
            reason_type: spam, violation, misleading, sexual, rude, other, appeal,
                or tools.ozone.report.defs#reason... values.
            reason (str, optional): Up to 2,000 characters.
            confirm: Must be true: this cannot be undone.
            **params: Any other API field, by its API name.
        """
        return self._op("reportOnBluesky", params, user=user, reason_type=reason_type, confirm=confirm)

    # ---- Teams and Approvals ----
    def list_post_approvals(self, **params) -> Dict:
        """List posts awaiting approval.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        Open items by default (pending_approval and draft). Editors and Contributors
        only see their own; members limited to some profiles only see those. Page with
        `before` = the previous `next_before`.

        ``GET /api/uploadposts/approvals``

        Args:
            status (str, optional): Comma-separated statuses (default the open
                ones).
            profile_username (str, optional): Only this profile.
            author (str, optional): Only this author email.
            limit (int, optional): Page size.
            before (str, optional): created_at of the last item of the previous page
                (next_before).
            count_only (bool, optional): true (or 1): answer only how many items
                there are per status, with the same filters (status, profile_username,
                author; limit and before are ignored). Nothing is listed or signed.
            **params: Any other API field, by its API name.
        """
        return self._op("listPostApprovals", params)

    def get_post_approval(self, approval_id: str, **params) -> Dict:
        """Get a post awaiting approval.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        The author or a reviewer (owner or Admin). Adds fields, preview_url,
        thumbnail_url and destinations_effective.

        ``GET /api/uploadposts/approvals/{approval_id}``

        Args:
            approval_id: Approval id.
            **params: Any other API field, by its API name.
        """
        return self._op("getPostApproval", params, approval_id=approval_id)

    def edit_post_approval(self, approval_id: str, **params) -> Dict:
        """Edit a post awaiting approval.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        The author or a reviewer, while it is open. Same body and validations as `PATCH
        /uploadposts/schedule/{job_id}`. Every edit raises `version` by one.

        ``PATCH /api/uploadposts/approvals/{approval_id}``

        Args:
            approval_id: Approval id.
            title (str, optional)
            caption (str, optional)
            description (str, optional): Alias of caption.
            platform_content (Dict[str, Any], optional)
            fields (Dict[str, Any], optional)
            scheduled_date (str, optional)
            timezone (str, optional)
            cover_image_base64 (str, optional)
            remove_cover (bool, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("editPostApproval", params, approval_id=approval_id)

    def withdraw_post_approval(self, approval_id: str, **params) -> Dict:
        """Withdraw or discard a post awaiting approval.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        The author withdraws it or a reviewer discards it: status withdrawn; its media
        is deleted.

        ``DELETE /api/uploadposts/approvals/{approval_id}``

        Args:
            approval_id: Approval id.
            **params: Any other API field, by its API name.
        """
        return self._op("withdrawPostApproval", params, approval_id=approval_id)

    def approve_post_approval(self, approval_id: str, version: int, **params) -> Dict:
        """Approve a post.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        Reviewer only (owner or Admin). `version` is required: the `item.version` you
        reviewed. Date used: the one in the body; else now (immediate posts or
        `publish_now`); else the next free queue slot (posts sent with add_to_queue);
        else the post's own date if it is more than 60 s away. Monthly credits are
        reserved now; if creating the job fails the item reopens and the credits come
        back (500 approval_failed).

        ``POST /api/uploadposts/approvals/{approval_id}/approve``

        Args:
            approval_id: Approval id.
            version
            comment (str, optional)
            scheduled_date (str, optional)
            timezone (str, optional)
            publish_now (bool, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("approvePostApproval", params, approval_id=approval_id, version=version)

    def reject_post_approval(self, approval_id: str, comment: str, **params) -> Dict:
        """Reject a post.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        Reviewer only. `comment` is required (max 2000 characters) and is shown to the
        author.

        ``POST /api/uploadposts/approvals/{approval_id}/reject``

        Args:
            approval_id: Approval id.
            comment
            **params: Any other API field, by its API name.
        """
        return self._op("rejectPostApproval", params, approval_id=approval_id, comment=comment)

    def list_client_post_approvals(self, token: str, **params) -> Dict:
        """End client: list posts to approve.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        Called with the **profile JWT** of the white-label connect page (`Authorization:
        Bearer <access_url token>`), generated with `client_approval: true` (`POST
        /uploadposts/users/generate-jwt`). Only the `pending_approval` posts of that
        profile; the end client cannot change the date. The account owner turns it off
        by generating the JWT again with `client_approval: false`. Items come without
        author or internal ids.

        ``GET /api/uploadposts/approvals/client``
        Authenticated with the profile JWT (``token``), not the API key.

        Args:
            token: Profile JWT (from ``generate_jwt``), sent as ``Authorization: Bearer``.
            **params: Any other API field, by its API name.
        """
        return self._op("listClientPostApprovals", params, token=token)

    def approve_client_post_approval(self, token: str, approval_id: str, version: int, **params) -> Dict:
        """End client: approve a post.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        Called with the **profile JWT** of the white-label connect page (`Authorization:
        Bearer <access_url token>`), generated with `client_approval: true` (`POST
        /uploadposts/users/generate-jwt`). Only the `pending_approval` posts of that
        profile; the end client cannot change the date. The account owner turns it off
        by generating the JWT again with `client_approval: false`. `version` is
        required, as for reviewers. Recorded as decided_by `client:<profile>`,
        decided_by_role `client`.

        ``POST /api/uploadposts/approvals/client/{approval_id}/approve``
        Authenticated with the profile JWT (``token``), not the API key.

        Args:
            token: Profile JWT (from ``generate_jwt``), sent as ``Authorization: Bearer``.
            approval_id: Approval id.
            version
            comment (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("approveClientPostApproval", params, token=token, approval_id=approval_id, version=version)

    def reject_client_post_approval(self, token: str, approval_id: str, comment: str, **params) -> Dict:
        """End client: reject a post.

        Not generally available yet. While post approvals are switched off every route
        of this group answers `503` with `error_code: post_approvals_disabled`.

        Called with the **profile JWT** of the white-label connect page (`Authorization:
        Bearer <access_url token>`), generated with `client_approval: true` (`POST
        /uploadposts/users/generate-jwt`). Only the `pending_approval` posts of that
        profile; the end client cannot change the date. The account owner turns it off
        by generating the JWT again with `client_approval: false`. `comment` is
        required.

        ``POST /api/uploadposts/approvals/client/{approval_id}/reject``
        Authenticated with the profile JWT (``token``), not the API key.

        Args:
            token: Profile JWT (from ``generate_jwt``), sent as ``Authorization: Bearer``.
            approval_id: Approval id.
            comment
            **params: Any other API field, by its API name.
        """
        return self._op("rejectClientPostApproval", params, token=token, approval_id=approval_id, comment=comment)

    def get_team_roles(self, **params) -> Dict:
        """Team roles and your role.

        The role matrix and the caller's role. `enabled: false` while team roles are not
        available: then every member is treated as Admin with every profile. Roles and
        profile lists are changed by the account owner from the dashboard.

        ``GET /api/uploadposts/teams/roles``

        Any API field goes in ``**params`` by its API name.
        """
        return self._op("getTeamRoles", params)

    def list_team_audit(self, **params) -> Dict:
        """Team activity log.

        What team members did on the account (posts created, published, edited or
        cancelled, approvals and decisions, access changes), newest first. Owner and
        Admin members only. Rows are kept `retention_days` days.

        ``GET /api/uploadposts/teams/audit``

        Args:
            actor (str, optional): Only this member email.
            action (str, optional): Only this action.
            profile_username (str, optional): Only this profile.
            target_id (str, optional): Only this approval or job id.
            since (str, optional): ISO 8601, inclusive.
            until (str, optional): ISO 8601, exclusive.
            limit (int, optional): Page size.
            cursor (str, optional): next_cursor of the previous page.
            **params: Any other API field, by its API name.
        """
        return self._op("listTeamAudit", params)

    # ---- Feedback ----
    def send_feedback(self, message: str, **params) -> Dict:
        """Send feedback to the Upload-Post team.

        For AI agents and developers. Never include credentials or personal data (they
        are redacted anyway). A repeated report returns duplicate: true.

        ``POST /api/uploadposts/feedback``

        Args:
            message
            category (str, optional)
            endpoint (str, optional)
            request_id (str, optional)
            agent (str, optional): Name of the agent or tool.
            **params: Any other API field, by its API name.
        """
        return self._op("sendFeedback", params, message=message)

    # ---- Google Business ----
    def update_google_business_account(self, user: str, account_name: str, **params) -> Dict:
        """Rename a Google Business account.

        Not generally available yet. Off by default: answers `403` with
        `ownership_changes_disabled` until the feature is available.

        Renames a business account (only the name). With `validate_only: true` Google
        checks the request without changing anything (no `confirm` needed); that mode
        works today. A real rename is not generally available yet: 403
        `ownership_changes_disabled`. `account` must be the account connected to the
        profile or the owner of one of its saved locations (404 `account_not_found`
        otherwise).

        ``PATCH /api/uploadposts/google-business/accounts``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            account (str, optional): `accounts/{id}` or a bare id.
            account_name: New name.
            validate_only (bool, optional): Google validates only; nothing changes.
            confirm (bool, optional): Required (`true`) unless `validate_only`.
            **params: Any other API field, by its API name.
        """
        return self._op("updateGoogleBusinessAccount", params, user=user, account_name=account_name)

    def create_google_business_admin(self, user: str, role: str, confirm: bool, **params) -> Dict:
        """Invite an admin.

        Not generally available yet. The API answers HTTP 503 until it is switched on.

        Google emails the invitation; the person gets access once they accept. Not
        generally available yet: answers 403 `ownership_changes_disabled` (do it in
        Google Business Profile). When enabled, only the owner of the Upload-Post
        account can do it (a team member gets 403 `owner_only`). Needs `"confirm":
        true`. Every change is audited. On 502 `google_result_unknown`, check with the
        matching GET before resending.

        ``POST /api/uploadposts/google-business/admins``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            scope (str, optional): `account` (default) or `location`.
            account (str, optional): Target account (`scope=account`).
            location_id (str, optional): Target location (`scope=location`).
            admin (str, optional): Email of the person to invite (one of `admin` /
                `admin_account`).
            admin_account (str, optional): `accounts/{id}` of a location group to
                invite to a location (`scope=location` only).
            role
            confirm: Must be `true`.
            **params: Any other API field, by its API name.
        """
        return self._op("createGoogleBusinessAdmin", params, user=user, role=role, confirm=confirm)

    def update_google_business_admin(self, user: str, admin_name: str, role: str, confirm: bool, **params) -> Dict:
        """Change an admin's role.

        Not generally available yet. The API answers HTTP 503 until it is switched on.

        Changes the role of an admin (`admin_name` from GET /admins). If the role is
        already that one, the answer has `unchanged: true` and nothing is sent. Refused
        with 409 `last_owner` if it would demote the last owner and 409
        `connected_identity` if it would demote the Google account connected to
        Upload-Post. Not generally available yet: answers 403
        `ownership_changes_disabled` (do it in Google Business Profile). When enabled,
        only the owner of the Upload-Post account can do it (a team member gets 403
        `owner_only`). Needs `"confirm": true`. Every change is audited. On 502
        `google_result_unknown`, check with the matching GET before resending.

        ``PATCH /api/uploadposts/google-business/admins``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            admin_name: `accounts/{a}/admins/{id}` or `locations/{l}/admins/{id}`
                (alias `name`).
            role
            confirm: Must be `true`.
            **params: Any other API field, by its API name.
        """
        return self._op("updateGoogleBusinessAdmin", params, user=user, admin_name=admin_name, role=role, confirm=confirm)

    def delete_google_business_admin(self, user: str, admin_name: str, confirm: bool, **params) -> Dict:
        """Remove an admin.

        Not generally available yet. The API answers HTTP 503 until it is switched on.

        Removes an admin at once (they would have to be invited again). Refused with 409
        `last_owner` / `connected_identity` like the role change. JSON body. Not
        generally available yet: answers 403 `ownership_changes_disabled` (do it in
        Google Business Profile). When enabled, only the owner of the Upload-Post
        account can do it (a team member gets 403 `owner_only`). Needs `"confirm":
        true`. Every change is audited. On 502 `google_result_unknown`, check with the
        matching GET before resending.

        ``DELETE /api/uploadposts/google-business/admins``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            admin_name: Admin resource name from GET /admins (alias `name`).
            confirm: Must be `true`.
            **params: Any other API field, by its API name.
        """
        return self._op("deleteGoogleBusinessAdmin", params, user=user, admin_name=admin_name, confirm=confirm)

    def accept_google_business_invitation(self, user: str, invitation: str, confirm: bool, **params) -> Dict:
        """Accept an invitation.

        Not generally available yet. The API answers HTTP 503 until it is switched on.

        Accepts a pending invitation (404 `invitation_not_found` otherwise). Not
        generally available yet: answers 403 `ownership_changes_disabled` (do it in
        Google Business Profile). When enabled, only the owner of the Upload-Post
        account can do it (a team member gets 403 `owner_only`). Needs `"confirm":
        true`. Every change is audited. On 502 `google_result_unknown`, check with the
        matching GET before resending.

        ``POST /api/uploadposts/google-business/invitations/accept``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            invitation: `accounts/{a}/invitations/{id}` (alias `invitation_name`).
            confirm: Must be `true`.
            **params: Any other API field, by its API name.
        """
        return self._op("acceptGoogleBusinessInvitation", params, user=user, invitation=invitation, confirm=confirm)

    def decline_google_business_invitation(self, user: str, invitation: str, confirm: bool, **params) -> Dict:
        """Decline an invitation.

        Not generally available yet. The API answers HTTP 503 until it is switched on.

        Declines a pending invitation (404 `invitation_not_found` otherwise). Not
        generally available yet: answers 403 `ownership_changes_disabled` (do it in
        Google Business Profile). When enabled, only the owner of the Upload-Post
        account can do it (a team member gets 403 `owner_only`). Needs `"confirm":
        true`. Every change is audited. On 502 `google_result_unknown`, check with the
        matching GET before resending.

        ``POST /api/uploadposts/google-business/invitations/decline``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            invitation: `accounts/{a}/invitations/{id}` (alias `invitation_name`).
            confirm: Must be `true`.
            **params: Any other API field, by its API name.
        """
        return self._op("declineGoogleBusinessInvitation", params, user=user, invitation=invitation, confirm=confirm)

    def transfer_google_business_location(self, user: str, location_id: str, destination_account: str, confirm: bool, **params) -> Dict:
        """Transfer a location to another account.

        Not generally available yet. The API answers HTTP 503 until it is switched on.

        Moves a location to another Google account. Google only allows it when the
        connected user owns the location and manages the destination account. Not
        generally available yet: answers 403 `ownership_changes_disabled` (do it in
        Google Business Profile). When enabled, only the owner of the Upload-Post
        account can do it (a team member gets 403 `owner_only`). Needs `"confirm":
        true`. Every change is audited. On 502 `google_result_unknown`, check with the
        matching GET before resending.

        ``POST /api/uploadposts/google-business/locations/transfer``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            location_id: Location: `locations/{id}`, a bare id or
                `accounts/{a}/locations/{id}`.
            destination_account: `accounts/{id}` that receives the location.
            confirm: Must be `true`.
            **params: Any other API field, by its API name.
        """
        return self._op("transferGoogleBusinessLocation", params, user=user, location_id=location_id, destination_account=destination_account, confirm=confirm)

    def create_google_business_location(self, user: str, language_code: str, **params) -> Dict:
        """Create a location.

        Not generally available yet. Answers 503 `gbp_feature_disabled` before anything
        else is checked. Send `location` (a Google Location object) or the friendly
        fields of location info, plus `language_code`. `title`, `primary_category` and
        `language_code` are required. Needs `confirm: true` (not with `dry_run`).
        `request_id` comes back in every answer: on 502 `google_result_unknown` repeat
        with the same `request_id` and Google never creates it twice. Search first with
        google-locations/search. Daily creation limits: 429 `daily_limit_reached` /
        `google_daily_quota_exhausted`.

        ``POST /api/uploadposts/google-business/locations/create``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            account (str, optional): Google account, `accounts/{id}` or a bare id.
                Default: the account saved when Google Business was connected.
            location (Dict[str, Any], optional): Google Location object (instead of
                the friendly fields).
            language_code: BCP 47; cannot be changed later.
            title (str, optional)
            primary_category (str, optional)
            request_id (str, optional): Up to 50 letters, digits, `-` or `_`.
                Generated if missing.
            dry_run (bool, optional): Validate and return what would be sent,
                without applying it.
            confirm (bool, optional): Required (`true`) for a real creation.
            **params: Any other API field, by its API name.
        """
        return self._op("createGoogleBusinessLocation", params, user=user, language_code=language_code)

    def delete_google_business_location(self, user: str, location_id: str, confirm: bool, **params) -> Dict:
        """Delete a location.

        Not generally available yet. Answers 503 `gbp_feature_disabled` before anything
        else is checked. Irreversible. Needs `confirm: true`. If Google does not allow
        deleting it through the API: 409 `location_cannot_be_deleted` (delete it from
        business.google.com).

        ``DELETE /api/uploadposts/google-business/locations/delete``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            location_id: Location: `locations/{id}`, a bare id or
                `accounts/{a}/locations/{id}`.
            confirm: Must be `true`.
            **params: Any other API field, by its API name.
        """
        return self._op("deleteGoogleBusinessLocation", params, user=user, location_id=location_id, confirm=confirm)

    def get_google_business_notification_settings(self, user: str, **params) -> Dict:
        """Get real-time notification settings.

        Not generally available yet. Answers 503 `gbp_notifications_unavailable` and no
        Google Business event is sent to webhooks. Google keeps one notification setting
        per Google account; when another tool owns it, `other_tool_configured` is
        `true`.

        ``GET /api/uploadposts/google-business/notifications``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            account (str, optional): Google account, `accounts/{id}` or a bare id.
                Default: the account saved when Google Business was connected.
            **params: Any other API field, by its API name.
        """
        return self._op("getGoogleBusinessNotificationSettings", params, user=user)

    def update_google_business_notification_settings(self, user: str, confirm: bool, **params) -> Dict:
        """Turn real-time notifications on or off.

        Not generally available yet. Answers 503 `gbp_notifications_unavailable` and no
        Google Business event is sent to webhooks. Turns notifications on or off for the
        Google account; webhooks must also list the events (`review_received`,
        `review_updated`, `customer_media_received`, `listing_google_update`,
        `listing_duplicate`, `listing_control_changed`) in `webhook_events`. Needs
        `confirm: true`. If Google does not confirm the change (`outcome_unknown:
        true`), read the setting before retrying.

        ``PUT /api/uploadposts/google-business/notifications``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            account (str, optional): Google account, `accounts/{id}` or a bare id.
                Default: the account saved when Google Business was connected.
            enabled (bool, optional): `true` (default) or `false`.
            types (List[str], optional): Types to receive (alias
                `notification_types`). Default: all six.
            confirm: Must be `true`: this replaces any other tool's setting for this
                Google account.
            force (bool, optional): `true` to replace a setting that belongs to
                another tool.
            confirm_other_tool (bool, optional): With `enabled: false` and `force:
                true` on another tool's setting: switch that tool's notifications off
                too.
            **params: Any other API field, by its API name.
        """
        return self._op("updateGoogleBusinessNotificationSettings", params, user=user, confirm=confirm)

    def start_google_business_verification(self, user: str, method: str, confirm: bool, **params) -> Dict:
        """Start a verification.

        Not generally available yet. Answers 503 `gbp_feature_disabled`. Google contacts
        the business (postcard, SMS, call or email), so `confirm: true` is required. 3
        verifications a day per location (429 `daily_limit_reached`, `scope: location`).
        `AUTO` verifications are `COMPLETED` at once; the others wait for the code. On
        502 `google_result_unknown`, check the list before trying again.

        ``POST /api/uploadposts/google-business/verification/start``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            location_id (str, optional): Location: `locations/{id}`, a bare id or
                `accounts/{a}/locations/{id}`.
            method
            phone_number (str, optional): `PHONE_CALL` / `SMS`: one of the numbers
                in the options.
            email_address (str, optional): `EMAIL`: one of the addresses in the
                options.
            mailer_contact (str, optional): `ADDRESS`: name the postcard is
                addressed to.
            trusted_partner_token (str, optional): Required for `TRUSTED_PARTNER`.
            token (str, optional): Vetted partners only. Not with the four fields
                above.
            language_code (str, optional): BCP-47, default `en`. The methods depend
                on the language and the country.
            context (Dict[str, Any], optional): Only for service-area businesses
                without a storefront: `{"address": {PostalAddress with regionCode}}`.
            confirm: Must be `true`.
            **params: Any other API field, by its API name.
        """
        return self._op("startGoogleBusinessVerification", params, user=user, method=method, confirm=confirm)

    def complete_google_business_verification(self, user: str, pin: str, **params) -> Dict:
        """Enter the verification code.

        Not generally available yet. Answers 503 `gbp_feature_disabled`. Sends the code
        Google sent. 10 attempts a day per account and location (429
        `daily_limit_reached`); only codes Google actually checked count. `state:
        COMPLETED` when Google accepts it.

        ``POST /api/uploadposts/google-business/verification/complete``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            location_id (str, optional): Location: `locations/{id}`, a bare id or
                `accounts/{a}/locations/{id}`.
            verification_name (str, optional): `locations/{l}/verifications/{v}`
                (one of `verification_name` / `verification_id`).
            verification_id (str, optional): Last part of the name, with
                `location_id`.
            pin: The code Google sent.
            **params: Any other API field, by its API name.
        """
        return self._op("completeGoogleBusinessVerification", params, user=user, pin=pin)

    def generate_google_business_verification_token(self, user: str, **params) -> Dict:
        """Get an instant verification token.

        Not generally available yet. Answers 503 `gbp_feature_disabled`. Asks Google for
        an instant verification token. When Google reserves it to its vetted partners,
        403 `partner_only`: use verification/start instead.

        ``POST /api/uploadposts/google-business/verification/token``

        Args:
            user: Profile username with Google Business connected (alias `profile`).
            location_id (str, optional): Location: `locations/{id}`, a bare id or
                `accounts/{a}/locations/{id}`.
            **params: Any other API field, by its API name.
        """
        return self._op("generateGoogleBusinessVerificationToken", params, user=user)

    # ---- ChatGPT Ads ----
    def connect_chatgpt_ads_account(self, api_key: str, **params) -> Dict:
        """Connect a ChatGPT Ads account.

        Stores an OpenAI Ads API key after validating it live against OpenAI. Each key
        is scoped to one ad account. The key is encrypted at rest and never returned.
        Posting the same account again replaces the stored key (key rotation). The first
        account connected becomes the default. Spend runs on your own OpenAI billing.

        ``POST /api/uploadposts/ads/chatgpt/connect``

        Args:
            api_key: Your OpenAI Ads API key (ads.openai.com -> Settings -> API
                keys).
            profile_username (str, optional): Link the ad account to this profile.
            name (str, optional): Friendly label. Default: the ad account name
                reported by OpenAI.
            default (bool, optional): Make this the account used when a request does
                not choose one.
            **params: Any other API field, by its API name.
        """
        return self._op("connectChatgptAdsAccount", params, api_key=api_key)

    def list_chatgpt_ads_accounts(self, **params) -> Dict:
        """List connected ChatGPT Ads accounts.

        Connected ad accounts (never the credentials), default first, each with the
        `profiles` it is linked to.

        ``GET /api/uploadposts/ads/chatgpt/accounts``

        Any API field goes in ``**params`` by its API name.
        """
        return self._op("listChatgptAdsAccounts", params)

    def disconnect_chatgpt_ads_account(self, ad_account_id: str, **params) -> Dict:
        """Disconnect a ChatGPT Ads account.

        Without `profile_username`: forgets the stored key and unlinks every profile (if
        it was the default, another connected account becomes the default). With
        `profile_username`: only unlinks that profile and keeps the key for the others.
        Campaigns keep running in Ads Manager either way.

        ``DELETE /api/uploadposts/ads/chatgpt/accounts/{ad_account_id}``

        Args:
            ad_account_id: Connected ad account (`adacct_...`).
            profile_username (str, optional): Only unlink this profile.
            **params: Any other API field, by its API name.
        """
        return self._op("disconnectChatgptAdsAccount", params, ad_account_id=ad_account_id)

    def get_chatgpt_ads_account(self, **params) -> Dict:
        """Get live ad account metadata.

        The selected ad account's metadata, read live from OpenAI. A 401 can also mean
        OpenAI rejected the stored key (revoked): reconnect the account with POST
        /connect.

        ``GET /api/uploadposts/ads/chatgpt/account``

        Args:
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("getChatgptAdsAccount", params)

    def list_chatgpt_ads_campaigns(self, **params) -> Dict:
        """List campaigns.

        Campaigns of the ad account. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/campaigns``

        Args:
            limit (int, optional): 1-500 (default 20).
            after (str, optional): Cursor: `last_id` of the previous page.
            before (str, optional): Cursor: `first_id` of the next page.
            order (str, optional): Sort order.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("listChatgptAdsCampaigns", params)

    def create_chatgpt_ads_campaign(self, name: str, **params) -> Dict:
        """Create a campaign.

        Creates a campaign (budget, schedule, location and audience targeting). One of
        `budget` / `budget_micros` is required. Created `paused` unless `status: active`
        is sent. A 401 can also mean OpenAI rejected the stored key (revoked): reconnect
        the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/campaigns``

        Args:
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            name: 3-1000 characters.
            budget (float, optional): Lifetime spend limit in the ad account
                currency. Minimum 1.
            budget_micros (int, optional): Same in micros (`25000000` = 25.00).
                Alternative to `budget`.
            status (str, optional): Default `paused`: nothing starts spending by
                accident.
            description (str, optional)
            start_time (Any, optional): Unix timestamp or ISO-8601 datetime. Empty
                or null clears it.
            end_time (Any, optional): Unix timestamp or ISO-8601 datetime. Empty or
                null clears it.
            bidding_type (str, optional): Default `impressions`. Cannot be changed
                later.
            conversion_event_setting_ids (List[str], optional): Exactly one active
                standard event setting; required for `conversions`.
            mode (str, optional): Passed to OpenAI as is.
            product_feed_id (str, optional): Product feed (product-feed campaigns).
            locations (List[str], optional): OpenAI location ids (country, region or
                DMA). Shorthand for `targeting.locations.include`.
            custom_audience_ids (List[str], optional): Shorthand for
                `targeting.custom_audiences.ids`.
            excluded_custom_audience_ids (List[str], optional): Shorthand for
                `targeting.excluded_custom_audiences.ids`.
            targeting (Dict[str, Any], optional): Full OpenAI targeting object.
                Overrides the shorthands.
            **params: Any other API field, by its API name.
        """
        return self._op("createChatgptAdsCampaign", params, name=name)

    def get_chatgpt_ads_campaign(self, campaign_id: str, **params) -> Dict:
        """Get a campaign.

        One campaign. A 401 can also mean OpenAI rejected the stored key (revoked):
        reconnect the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}``

        Args:
            campaign_id: Campaign id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("getChatgptAdsCampaign", params, campaign_id=campaign_id)

    def update_chatgpt_ads_campaign(self, campaign_id: str, **params) -> Dict:
        """Update a campaign.

        Updates a campaign. Every field is optional; at least one is required (400 `No
        updatable fields supplied`). Archiving is irreversible. A 401 can also mean
        OpenAI rejected the stored key (revoked): reconnect the account with POST
        /connect.

        ``POST /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}``

        Args:
            campaign_id: Campaign id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            name (str, optional): 3-1000 characters.
            budget (float, optional): Lifetime spend limit in the ad account
                currency. Minimum 1.
            budget_micros (int, optional): Same in micros (`25000000` = 25.00).
                Alternative to `budget`.
            status (str, optional): `archived` is irreversible.
            description (str, optional)
            start_time (Any, optional): Unix timestamp or ISO-8601 datetime. Empty
                or null clears it.
            end_time (Any, optional): Unix timestamp or ISO-8601 datetime. Empty or
                null clears it.
            locations (List[str], optional): OpenAI location ids (country, region or
                DMA). Shorthand for `targeting.locations.include`.
            custom_audience_ids (List[str], optional): Shorthand for
                `targeting.custom_audiences.ids`.
            excluded_custom_audience_ids (List[str], optional): Shorthand for
                `targeting.excluded_custom_audiences.ids`.
            targeting (Dict[str, Any], optional): Full OpenAI targeting object.
                Overrides the shorthands.
            **params: Any other API field, by its API name.
        """
        return self._op("updateChatgptAdsCampaign", params, campaign_id=campaign_id)

    def activate_chatgpt_ads_campaign(self, campaign_id: str, **params) -> Dict:
        """Activate a campaign.

        Sets the campaign `active`. An ad only serves when its campaign, ad group and ad
        are all active and the ad passed OpenAI's review. No body: choose the ad account
        with the query parameter or the header. A 401 can also mean OpenAI rejected the
        stored key (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}/activate``

        Args:
            campaign_id: Campaign id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("activateChatgptAdsCampaign", params, campaign_id=campaign_id)

    def pause_chatgpt_ads_campaign(self, campaign_id: str, **params) -> Dict:
        """Pause a campaign.

        Sets the campaign `paused`. No body: choose the ad account with the query
        parameter or the header. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}/pause``

        Args:
            campaign_id: Campaign id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("pauseChatgptAdsCampaign", params, campaign_id=campaign_id)

    def archive_chatgpt_ads_campaign(self, campaign_id: str, **params) -> Dict:
        """Archive a campaign.

        Archives the campaign. Irreversible. No body: choose the ad account with the
        query parameter or the header. A 401 can also mean OpenAI rejected the stored
        key (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}/archive``

        Args:
            campaign_id: Campaign id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("archiveChatgptAdsCampaign", params, campaign_id=campaign_id)

    def get_chatgpt_ads_campaign_insights(self, campaign_id: str, **params) -> Dict:
        """Get campaign insights.

        Performance of one campaign; rows per `aggregation_level` inside it. Repeatable
        parameters accept `key` or `key[]` and are forwarded to OpenAI. Page forward
        with `after=<last_id>`. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}/insights``

        Args:
            campaign_id: Campaign id.
            since (str, optional): `YYYY-MM-DD`, start of a date range in the ad
                account timezone.
            until (str, optional): `YYYY-MM-DD`, end of the date range.
            time_granularity (str, optional): Default `daily`.
            aggregation_level (str, optional): Row entity inside the endpoint's
                scope.
            fields (List[str], optional): Repeatable (`fields` or `fields[]`).
                Metrics and metadata: `impressions`, `clicks`, `spend`, `ctr`, `cpc`,
                `cpm`, `campaign.name`...
            segments (List[str], optional): Repeatable. One of `product`, `country`,
                `device`.
            filters (List[str], optional): Repeatable JSON-encoded objects, passed
                through to OpenAI.
            sort (List[str], optional): Repeatable JSON-encoded objects, passed
                through to OpenAI.
            time_ranges (List[str], optional): Repeatable JSON-encoded range
                objects, for windows `since`/`until` cannot express (they win over
                `since`/`until`).
            limit (int, optional): 1-2000 (default 20).
            after (str, optional): Cursor: `last_id` of the previous page.
            before (str, optional): Cursor: `first_id` of the next page.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("getChatgptAdsCampaignInsights", params, campaign_id=campaign_id)

    def list_chatgpt_ads_ad_groups(self, campaign_id: str, **params) -> Dict:
        """List ad groups.

        Ad groups of a campaign. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/adgroups``

        Args:
            campaign_id: Parent campaign.
            limit (int, optional): 1-500 (default 20).
            after (str, optional): Cursor: `last_id` of the previous page.
            before (str, optional): Cursor: `first_id` of the next page.
            order (str, optional): Sort order.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("listChatgptAdsAdGroups", params, campaign_id=campaign_id)

    def create_chatgpt_ads_ad_group(self, campaign_id: str, name: str, **params) -> Dict:
        """Create an ad group.

        Creates an ad group (the bid) under a campaign. One of `max_bid` /
        `max_bid_micros` is required unless `bidding_config` is sent. Created `paused`
        unless `status: active` is sent. A 401 can also mean OpenAI rejected the stored
        key (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/adgroups``

        Args:
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            campaign_id: Parent campaign.
            name: 3-1000 characters.
            max_bid (float, optional): Max bid per billing event in account currency
                (`0.06` = a $60 CPM on impression billing).
            max_bid_micros (int, optional): Same in micros. Alternative to
                `max_bid`.
            billing_event_type (str, optional): Default `impression`; `click` for
                click and conversion campaigns.
            bidding_config (Dict[str, Any], optional): Full OpenAI bidding config.
                Overrides `max_bid` / `billing_event_type`.
            status (str, optional): Default `paused`: nothing starts spending by
                accident.
            description (str, optional)
            context_hints (List[str], optional): When your product or service is
                useful, in your own words.
            product_set (Dict[str, Any], optional): Product filters for product-feed
                campaigns.
            **params: Any other API field, by its API name.
        """
        return self._op("createChatgptAdsAdGroup", params, campaign_id=campaign_id, name=name)

    def get_chatgpt_ads_ad_group(self, ad_group_id: str, **params) -> Dict:
        """Get an ad group.

        One ad group. A 401 can also mean OpenAI rejected the stored key (revoked):
        reconnect the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}``

        Args:
            ad_group_id: Ad group id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("getChatgptAdsAdGroup", params, ad_group_id=ad_group_id)

    def update_chatgpt_ads_ad_group(self, ad_group_id: str, **params) -> Dict:
        """Update an ad group.

        Updates an ad group. Every field is optional; at least one is required (400 `No
        updatable fields supplied`). Archiving is irreversible. A 401 can also mean
        OpenAI rejected the stored key (revoked): reconnect the account with POST
        /connect.

        ``POST /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}``

        Args:
            ad_group_id: Ad group id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            name (str, optional): 3-1000 characters.
            max_bid (float, optional): Max bid per billing event in account currency
                (`0.06` = a $60 CPM on impression billing).
            max_bid_micros (int, optional): Same in micros. Alternative to
                `max_bid`.
            billing_event_type (str, optional): Default `impression`; `click` for
                click and conversion campaigns.
            bidding_config (Dict[str, Any], optional): Full OpenAI bidding config.
                Overrides `max_bid` / `billing_event_type`.
            status (str, optional): `archived` is irreversible.
            description (str, optional)
            context_hints (List[str], optional): When your product or service is
                useful, in your own words.
            product_set (Dict[str, Any], optional): Product filters for product-feed
                campaigns.
            **params: Any other API field, by its API name.
        """
        return self._op("updateChatgptAdsAdGroup", params, ad_group_id=ad_group_id)

    def activate_chatgpt_ads_ad_group(self, ad_group_id: str, **params) -> Dict:
        """Activate an ad group.

        Sets the ad group `active`. An ad only serves when its campaign, ad group and ad
        are all active and the ad passed OpenAI's review. No body: choose the ad account
        with the query parameter or the header. A 401 can also mean OpenAI rejected the
        stored key (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/activate``

        Args:
            ad_group_id: Ad group id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("activateChatgptAdsAdGroup", params, ad_group_id=ad_group_id)

    def pause_chatgpt_ads_ad_group(self, ad_group_id: str, **params) -> Dict:
        """Pause an ad group.

        Sets the ad group `paused`. No body: choose the ad account with the query
        parameter or the header. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/pause``

        Args:
            ad_group_id: Ad group id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("pauseChatgptAdsAdGroup", params, ad_group_id=ad_group_id)

    def archive_chatgpt_ads_ad_group(self, ad_group_id: str, **params) -> Dict:
        """Archive an ad group.

        Archives the ad group. Irreversible. No body: choose the ad account with the
        query parameter or the header. A 401 can also mean OpenAI rejected the stored
        key (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/archive``

        Args:
            ad_group_id: Ad group id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("archiveChatgptAdsAdGroup", params, ad_group_id=ad_group_id)

    def get_chatgpt_ads_ad_group_insights(self, ad_group_id: str, **params) -> Dict:
        """Get ad group insights.

        Performance of one ad group; rows per `aggregation_level` inside it. Repeatable
        parameters accept `key` or `key[]` and are forwarded to OpenAI. Page forward
        with `after=<last_id>`. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/insights``

        Args:
            ad_group_id: Ad group id.
            since (str, optional): `YYYY-MM-DD`, start of a date range in the ad
                account timezone.
            until (str, optional): `YYYY-MM-DD`, end of the date range.
            time_granularity (str, optional): Default `daily`.
            aggregation_level (str, optional): Row entity inside the endpoint's
                scope.
            fields (List[str], optional): Repeatable (`fields` or `fields[]`).
                Metrics and metadata: `impressions`, `clicks`, `spend`, `ctr`, `cpc`,
                `cpm`, `campaign.name`...
            segments (List[str], optional): Repeatable. One of `product`, `country`,
                `device`.
            filters (List[str], optional): Repeatable JSON-encoded objects, passed
                through to OpenAI.
            sort (List[str], optional): Repeatable JSON-encoded objects, passed
                through to OpenAI.
            time_ranges (List[str], optional): Repeatable JSON-encoded range
                objects, for windows `since`/`until` cannot express (they win over
                `since`/`until`).
            limit (int, optional): 1-2000 (default 20).
            after (str, optional): Cursor: `last_id` of the previous page.
            before (str, optional): Cursor: `first_id` of the next page.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("getChatgptAdsAdGroupInsights", params, ad_group_id=ad_group_id)

    def list_chatgpt_ads_ads(self, ad_group_id: str, **params) -> Dict:
        """List ads.

        Ads of an ad group. `review_status` is `in_review`, `approved` or `rejected`. A
        401 can also mean OpenAI rejected the stored key (revoked): reconnect the
        account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/ads``

        Args:
            ad_group_id: Parent ad group.
            limit (int, optional): 1-500 (default 20).
            after (str, optional): Cursor: `last_id` of the previous page.
            before (str, optional): Cursor: `first_id` of the next page.
            order (str, optional): Sort order.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("listChatgptAdsAds", params, ad_group_id=ad_group_id)

    def create_chatgpt_ads_ad(self, ad_group_id: str, name: str, **params) -> Dict:
        """Create an ad.

        Creates an ad (the creative) under an ad group: send `title`, `body`,
        `target_url` and `file_id` at the top level, or a full `creative` object (needed
        for `product_ad_template`). It starts serving after OpenAI's review
        (`review_status: approved`). Created `paused` unless `status: active` is sent. A
        401 can also mean OpenAI rejected the stored key (revoked): reconnect the
        account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/ads``

        Args:
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            ad_group_id: Parent ad group.
            name: Internal name, 3-1000 characters. Not shown to users.
            title (str, optional): Headline, 3-50 characters.
            body (str, optional): Copy, up to 100 characters.
            target_url (str, optional): http(s) destination URL.
            file_id (str, optional): Creative id from POST /creatives.
            price (str, optional)
            type (str, optional): Creative type (flat form).
            status (str, optional): Default `paused`: nothing starts spending by
                accident.
            creative (Dict[str, Any], optional): Creative. `chat_card` (default)
                needs `title`, `body`, `target_url` and `file_id`; `product_ad_template`
                takes image and destination from the feed item.
            **params: Any other API field, by its API name.
        """
        return self._op("createChatgptAdsAd", params, ad_group_id=ad_group_id, name=name)

    def get_chatgpt_ads_ad(self, ad_id: str, **params) -> Dict:
        """Get an ad.

        One ad. A 401 can also mean OpenAI rejected the stored key (revoked): reconnect
        the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/ads/{ad_id}``

        Args:
            ad_id: Ad id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("getChatgptAdsAd", params, ad_id=ad_id)

    def update_chatgpt_ads_ad(self, ad_id: str, **params) -> Dict:
        """Update an ad.

        Updates an ad. Only `name`, `status` and `creative` are read; an edited ad goes
        back into review. Every field is optional; at least one is required (400 `No
        updatable fields supplied`). Archiving is irreversible. A 401 can also mean
        OpenAI rejected the stored key (revoked): reconnect the account with POST
        /connect.

        ``POST /api/uploadposts/ads/chatgpt/ads/{ad_id}``

        Args:
            ad_id: Ad id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            name (str, optional): 3-1000 characters.
            status (str, optional): `archived` is irreversible.
            creative (Dict[str, Any], optional): Creative. `chat_card` (default)
                needs `title`, `body`, `target_url` and `file_id`; `product_ad_template`
                takes image and destination from the feed item.
            **params: Any other API field, by its API name.
        """
        return self._op("updateChatgptAdsAd", params, ad_id=ad_id)

    def activate_chatgpt_ads_ad(self, ad_id: str, **params) -> Dict:
        """Activate an ad.

        Sets the ad `active`. An ad only serves when its campaign, ad group and ad are
        all active and the ad passed OpenAI's review. No body: choose the ad account
        with the query parameter or the header. A 401 can also mean OpenAI rejected the
        stored key (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/ads/{ad_id}/activate``

        Args:
            ad_id: Ad id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("activateChatgptAdsAd", params, ad_id=ad_id)

    def pause_chatgpt_ads_ad(self, ad_id: str, **params) -> Dict:
        """Pause an ad.

        Sets the ad `paused`. No body: choose the ad account with the query parameter or
        the header. A 401 can also mean OpenAI rejected the stored key (revoked):
        reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/ads/{ad_id}/pause``

        Args:
            ad_id: Ad id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("pauseChatgptAdsAd", params, ad_id=ad_id)

    def archive_chatgpt_ads_ad(self, ad_id: str, **params) -> Dict:
        """Archive an ad.

        Archives the ad. Irreversible. No body: choose the ad account with the query
        parameter or the header. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/ads/{ad_id}/archive``

        Args:
            ad_id: Ad id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("archiveChatgptAdsAd", params, ad_id=ad_id)

    def get_chatgpt_ads_ad_insights(self, ad_id: str, **params) -> Dict:
        """Get ad insights.

        Performance of one ad; rows per `aggregation_level` inside it. Repeatable
        parameters accept `key` or `key[]` and are forwarded to OpenAI. Page forward
        with `after=<last_id>`. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/ads/{ad_id}/insights``

        Args:
            ad_id: Ad id.
            since (str, optional): `YYYY-MM-DD`, start of a date range in the ad
                account timezone.
            until (str, optional): `YYYY-MM-DD`, end of the date range.
            time_granularity (str, optional): Default `daily`.
            aggregation_level (str, optional): Row entity inside the endpoint's
                scope.
            fields (List[str], optional): Repeatable (`fields` or `fields[]`).
                Metrics and metadata: `impressions`, `clicks`, `spend`, `ctr`, `cpc`,
                `cpm`, `campaign.name`...
            segments (List[str], optional): Repeatable. One of `product`, `country`,
                `device`.
            filters (List[str], optional): Repeatable JSON-encoded objects, passed
                through to OpenAI.
            sort (List[str], optional): Repeatable JSON-encoded objects, passed
                through to OpenAI.
            time_ranges (List[str], optional): Repeatable JSON-encoded range
                objects, for windows `since`/`until` cannot express (they win over
                `since`/`until`).
            limit (int, optional): 1-2000 (default 20).
            after (str, optional): Cursor: `last_id` of the previous page.
            before (str, optional): Cursor: `first_id` of the next page.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("getChatgptAdsAdInsights", params, ad_id=ad_id)

    def preview_chatgpt_ads_ad(self, ad_id: str, **params) -> Dict:
        """Preview an ad.

        A temporary iframe preview of the ad (expires in 24 h). No body. A 401 can also
        mean OpenAI rejected the stored key (revoked): reconnect the account with POST
        /connect.

        ``POST /api/uploadposts/ads/chatgpt/ads/{ad_id}/preview``

        Args:
            ad_id: Ad id.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("previewChatgptAdsAd", params, ad_id=ad_id)

    def upload_chatgpt_ads_creative(self, **params) -> Dict:
        """Upload a creative image.

        Uploads the image an ad uses; reuse the returned `file_id`. JSON with
        `image_url` (OpenAI fetches it) or multipart with a binary `file` (up to 10 MB).
        A 401 can also mean OpenAI rejected the stored key (revoked): reconnect the
        account with POST /connect.

        ``POST /api/uploadposts/ads/chatgpt/creatives``

        Args:
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            image_url (str, optional): http(s) image URL.
            file (Any, optional): Image, up to 10 MB.
            **params: Any other API field, by its API name.
        """
        return self._op("uploadChatgptAdsCreative", params)

    def get_chatgpt_ads_account_insights(self, **params) -> Dict:
        """Get ad account insights.

        Performance of the whole ad account; rows per `aggregation_level`. Repeatable
        parameters accept `key` or `key[]` and are forwarded to OpenAI. Page forward
        with `after=<last_id>`. A 401 can also mean OpenAI rejected the stored key
        (revoked): reconnect the account with POST /connect.

        ``GET /api/uploadposts/ads/chatgpt/insights``

        Args:
            since (str, optional): `YYYY-MM-DD`, start of a date range in the ad
                account timezone.
            until (str, optional): `YYYY-MM-DD`, end of the date range.
            time_granularity (str, optional): Default `daily`.
            aggregation_level (str, optional): Row entity inside the endpoint's
                scope.
            fields (List[str], optional): Repeatable (`fields` or `fields[]`).
                Metrics and metadata: `impressions`, `clicks`, `spend`, `ctr`, `cpc`,
                `cpm`, `campaign.name`...
            segments (List[str], optional): Repeatable. One of `product`, `country`,
                `device`.
            filters (List[str], optional): Repeatable JSON-encoded objects, passed
                through to OpenAI.
            sort (List[str], optional): Repeatable JSON-encoded objects, passed
                through to OpenAI.
            time_ranges (List[str], optional): Repeatable JSON-encoded range
                objects, for windows `since`/`until` cannot express (they win over
                `since`/`until`).
            limit (int, optional): 1-2000 (default 20).
            after (str, optional): Cursor: `last_id` of the previous page.
            before (str, optional): Cursor: `first_id` of the next page.
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            **params: Any other API field, by its API name.
        """
        return self._op("getChatgptAdsAccountInsights", params)

    def promote_chatgpt_ads(self, title: str, body: str, target_url: str, **params) -> Dict:
        """Launch an ad in one call.

        Creates the campaign, ad group and ad, and uploads the creative from `image_url`
        (or reuses `file_id`), in one request. Every payload is validated before the
        first write; everything is created paused and only activated (`status: active`)
        once all three exist. If a later step fails, the error carries `details.created`
        with the ids already created so you can finish or archive them. A 401 can also
        mean OpenAI rejected the stored key (revoked): reconnect the account with POST
        /connect.

        ``POST /api/uploadposts/ads/chatgpt/promote``

        Args:
            ad_account_id (str, optional): ChatGPT Ads account to use
                (`adacct_...`). Without it: `X-Ads-Account-Id` header, then
                `ad_account_id` in the JSON body, then the only or the default connected
                account (several and no default = 400).
            profile_username (str, optional): Use the ad account linked to this
                profile, and only that one (404 if the profile has none linked; never
                falls back to the default account).
            title: Ad headline, 3-50 characters.
            body: Ad copy, up to 100 characters.
            target_url: http(s) destination URL.
            image_url (str, optional): Creative image URL (one of `image_url` /
                `file_id`).
            file_id (str, optional): Already uploaded creative id.
            budget (float, optional): Lifetime spend limit in the ad account
                currency. Minimum 1.
            budget_micros (int, optional): Same in micros (`25000000` = 25.00).
                Alternative to `budget`.
            max_bid (float, optional): Max bid per billing event in account currency
                (`0.06` = a $60 CPM on impression billing).
            max_bid_micros (int, optional): Same in micros. Alternative to
                `max_bid`.
            name (str, optional): Base name of the three objects. Default: `title`.
            status (str, optional): Default `paused`: nothing starts spending by
                accident.
            bidding_type (str, optional): Default `impressions`.
            billing_event_type (str, optional): Default: `impression` for impression
                campaigns, `click` otherwise.
            start_time (Any, optional): Unix timestamp or ISO-8601 datetime. Empty
                or null clears it.
            end_time (Any, optional): Unix timestamp or ISO-8601 datetime. Empty or
                null clears it.
            description (str, optional): Campaign description.
            conversion_event_setting_ids (List[str], optional): For `conversions`
                bidding.
            locations (List[str], optional): OpenAI location ids (country, region or
                DMA). Shorthand for `targeting.locations.include`.
            custom_audience_ids (List[str], optional): Shorthand for
                `targeting.custom_audiences.ids`.
            excluded_custom_audience_ids (List[str], optional): Shorthand for
                `targeting.excluded_custom_audiences.ids`.
            targeting (Dict[str, Any], optional): Full OpenAI targeting object.
                Overrides the shorthands.
            context_hints (List[str], optional): When the ad is useful, e.g.
                `["productivity"]`.
            price (str, optional): Creative price.
            ad_group_name (str, optional)
            ad_name (str, optional)
            **params: Any other API field, by its API name.
        """
        return self._op("promoteChatgptAds", params, title=title, body=body, target_url=target_url)

    # </openapi:methods>
