# Upload-Post SDK for Python

Official Python client for the [Upload-Post API](https://www.upload-post.com) - Cross-platform social media upload.

Upload videos, photos, text posts, and documents to **TikTok, Instagram, YouTube, LinkedIn, Facebook, Pinterest, Threads, Reddit, Bluesky, Discord, Telegram, X (Twitter), Slack, Mastodon, Nostr, Lemmy, Dev.to, Hashnode, WordPress, Whop, and Listmonk** with a single API.

## Installation

```bash
pip install upload-post
```

## Quick Start

```python
from upload_post import UploadPostClient

client = UploadPostClient("YOUR_API_KEY")

# Upload a video to multiple platforms
response = client.upload_video(
    "video.mp4",
    title="Check out this awesome video! 🎬",
    user="my-profile",
    platforms=["tiktok", "instagram", "youtube"]
)

print(response)
```

## Features

- ✅ **Video Upload** - TikTok, Instagram, YouTube, LinkedIn, Facebook, Pinterest, Threads, Bluesky, Discord, Telegram, X, Mastodon, WordPress
- ✅ **Photo Upload** - TikTok, Instagram, LinkedIn, Facebook, Pinterest, Threads, Reddit, Bluesky, Discord, Telegram, X, Mastodon, Lemmy, WordPress
- ✅ **Text Posts** - X, LinkedIn, Facebook, Threads, Reddit, Bluesky, Discord, Telegram, Slack, Mastodon, Nostr, Lemmy, Dev.to, Hashnode, WordPress, Whop, Listmonk
- ✅ **Document Upload** - LinkedIn (PDF, PPT, PPTX, DOC, DOCX)
- ✅ **Scheduling** - Schedule posts for later
- ✅ **Posting Queue** - Add posts to your configured queue
- ✅ **First Comments** - Auto-post first comment after publishing
- ✅ **Analytics** - Get engagement metrics
- ✅ **Full Type Hints**

## API Reference

### Upload Video

```python
response = client.upload_video(
    "video.mp4",
    title="My awesome video",
    user="my-profile",
    platforms=["tiktok", "instagram", "youtube"],
    
    # Optional: Schedule for later
    scheduled_date="2024-12-25T10:00:00Z",
    timezone="Europe/Madrid",
    
    # Optional: Add first comment
    first_comment="Thanks for watching! 🙏",
    
    # Optional: Platform-specific settings
    disable_comment=False,  # TikTok
    media_type="REELS",  # Instagram
    privacyStatus="public",  # YouTube
    tags=["tutorial", "coding"],  # YouTube
)
```

### Upload Photos

```python
# Upload single or multiple photos
response = client.upload_photos(
    ["photo1.jpg", "photo2.jpg", "https://example.com/photo3.jpg"],
    title="Check out these photos! 📸",
    user="my-profile",
    platforms=["instagram", "facebook", "x"],
    
    # Optional: Add to queue instead of posting immediately
    add_to_queue=True,
    
    # Platform-specific
    media_type="IMAGE",  # Instagram: IMAGE or STORIES
    facebook_page_id="your-page-id",
)
```

### Upload Text Posts

```python
response = client.upload_text(
    title="Just shipped a new feature! 🚀 Check it out at example.com",
    user="my-profile",
    platforms=["x", "linkedin", "threads"],
    
    # Optional: Create a poll on X
    poll_options=["Option A", "Option B", "Option C"],
    poll_duration=1440,  # 24 hours in minutes
    
    # Optional: Post to a LinkedIn company page
    target_linkedin_page_id="company-page-id",
)
```

### Upload Documents (LinkedIn)

```python
response = client.upload_document(
    "presentation.pdf",
    title="Q4 2024 Report",
    user="my-profile",
    description="Check out our latest quarterly results!",
    visibility="PUBLIC",
    target_linkedin_page_id="company-page-id",  # Optional: post to company page
)
```

### Check Upload Status

For async uploads, check the status using the request_id:

```python
status = client.get_status("request_id_from_upload")
print(status)
```

For scheduled or queued posts, check the status using the job_id:

```python
status = client.get_job_status("job_id_from_scheduled_post")
print(status)
```

### Get Upload History

```python
history = client.get_history(page=1, limit=20)
print(history)
```

### Scheduled Posts

```python
# List all scheduled posts
scheduled = client.list_scheduled()

# Edit a scheduled post
client.edit_scheduled(
    "job-id",
    scheduled_date="2024-12-26T15:00:00Z",
    timezone="America/New_York",
)

# Cancel a scheduled post
client.cancel_scheduled("job-id")
```

### User Management

```python
# List all profiles
users = client.list_users()

# Create a new profile
client.create_user("new-profile")

# Delete a profile
client.delete_user("old-profile")

# Generate JWT for platform integration (white-label)
jwt = client.generate_jwt(
    "my-profile",
    redirect_url="https://yourapp.com/callback",
    platforms=["tiktok", "instagram"],
    # Optional: force the connection page language for this profile.
    # Supported: "en", "es", "de", "fr", "pt", "pl", "tr". When omitted, the page
    # auto-detects the visitor's browser language and falls back to English.
    language="es",
    # Optional: override individual connection-page strings. Flat dict of i18n
    # dot-path keys to strings. Max 100 entries, keys ^[a-zA-Z0-9_.]+$, values
    # up to 300 chars. Echoed back in the "profile" object of validate_jwt.
    ui_labels={
        "connect.title": "Link your accounts",
        "connect.subtitle": "Publish everywhere from one place",
    },
)
```

### Get Analytics

```python
analytics = client.get_analytics(
    "my-profile",
    platforms=["instagram", "tiktok"],
)
print(analytics)

# Instagram returns two audience breakdowns with the same shape
# ("age", "gender", "country", "city"):
print(analytics["analytics"]["instagram"]["follower_demographics"])
print(analytics["analytics"]["instagram"]["engaged_audience_demographics"])
```

### Cached Post Analytics

Replays per-post metrics already fetched, instead of calling the platforms again. Only contains posts previously fetched through a live per-post endpoint; there is no background refresh, so captured_at is the last time that post was read live. Not subject to the live
calls, so it is not subject to the live post-analytics rate limit
(100 requests / 5 minutes). Use it to page through a profile's post history.

```python
cursor = None
while True:
    page = client.get_cached_post_analytics(
        "my-profile",
        platform="youtube",   # optional: instagram, tiktok, youtube, facebook, linkedin, threads, pinterest, reddit
        limit=50,             # default 50, max 200
        since="2026-06-01",   # defaults to 30 days ago
        until="2026-07-01",   # defaults to today
        cursor=cursor,
    )
    for post in page["posts"]:
        print(post["platform"], post["post_id"], post["metrics"])
    cursor = page["next_cursor"]
    if not cursor:
        break
```

### Get Media

Retrieve recent posts from a connected social account. Supported platforms:
`instagram`, `tiktok`, `youtube`, `linkedin`, `facebook`, `x`, `threads`,
`pinterest`, `bluesky`, `reddit`.

```python
# Personal LinkedIn profile (default for non-org accounts):
media = client.get_media("linkedin", "my-profile")

# Force the personal profile of an account connected as an org admin:
media = client.get_media("linkedin", "my-profile", page_urn="me")

# Target a specific LinkedIn organization page:
media = client.get_media("linkedin", "my-profile", page_urn="12345")
```

The response carries a `pagination` object — `{"limit": ..., "next_cursor": ...,
"has_more": ...}`, with `next_cursor` `None` and `has_more` `False` on the last
page:

```python
cursor = None
while True:
    page = client.get_media("instagram", "my-profile", limit=50, cursor=cursor)
    print(len(page["media"]))
    cursor = page["pagination"]["next_cursor"]
    if not cursor:
        break
```

`limit` defaults to 25 and is clamped to 1-100, with per-platform caps of 20 for
TikTok and 50 for YouTube. **LinkedIn, Discord and Telegram do not support
cursors** — they accept `limit` only, and passing a `cursor` returns HTTP 400.

### Helper Methods

```python
# Get Facebook pages for a profile
fb_pages = client.get_facebook_pages("my-profile")

# Get LinkedIn pages for a profile
li_pages = client.get_linkedin_pages("my-profile")

# Get Pinterest boards for a profile
boards = client.get_pinterest_boards("my-profile")

# TikTok: trending Commercial Music Library tracks
music = client.get_tiktok_trending_music(
    "my-profile", genre="POP", country_code="ES", date_range="7DAY"
)

# TikTok: search locations to tag
locations = client.get_tiktok_locations("my-profile", "Madrid")
```

## TikTok music, location, cover and drafts

> **Capabilities.** These options are available on connections that declare the
> matching capability (`music`, `location`, `cover_image`, `draft`) — see the
> `capabilities` array on the TikTok account returned by
> `GET /api/uploadposts/users` (`client.list_users()`). Other values that can
> appear there: `cover_timestamp`, `photo_privacy`, `video_privacy`,
> `inbox_fallback`, `comments`, `profile_analytics`. If your connection does
> not have the capability, the field is ignored, the post still publishes, and
> the response includes a per-field `warnings` string — reconnect the TikTok
> account to enable it.

```python
# 1. Pick a track and a place
tracks = client.get_tiktok_trending_music("my-profile", country_code="ES")["tracks"]
places = client.get_tiktok_locations("my-profile", "Madrid")["locations"]

# 2. Publish with them
client.upload_video(
    "video.mp4",
    title="Shot in Madrid",
    user="my-profile",
    platforms=["tiktok"],

    tiktok_music_id=tracks[0]["id"],
    tiktok_music_volume=70,             # 0-100, defaults to 50 when music is set
    tiktok_music_start=0,               # ms
    tiktok_music_end=15000,             # ms
    tiktok_original_sound_volume=30,    # 0-100, defaults to 50 so the original audio is not muted

    tiktok_location_id=places[0]["location_id"],
    tiktok_location_name=places[0]["location_name"],  # required together with the id

    tiktok_cover_image_url="https://example.com/cover.jpg",
    tiktok_is_ai_generated=False,
    tiktok_upload_to_draft=False,       # True sends it to drafts and ignores the rest
)
```

### TikTok music, location, cover and draft options

| Option | Type | Capability | Notes |
| --- | --- | --- | --- |
| `tiktok_music_id` | str | `music` | The track `id` from `get_tiktok_trending_music()` (not `commercial_music_id`) |
| `tiktok_music_volume` | int | `music` | 0-100. Defaults to 50 when music is set |
| `tiktok_music_start` | int | `music` | Music start offset in ms |
| `tiktok_music_end` | int | `music` | Music end offset in ms |
| `tiktok_original_sound_volume` | int | `music` | 0-100. Defaults to 50 when music is set, so the original audio is not muted |
| `tiktok_location_id` | str | `location` | `location_id` from `get_tiktok_locations()` |
| `tiktok_location_name` | str | `location` | Required whenever `tiktok_location_id` is set |
| `tiktok_cover_image_url` | str | `cover_image` | Custom cover image URL |
| `tiktok_is_ai_generated` | bool | — | AI-generated content disclosure |
| `tiktok_upload_to_draft` | bool | `draft` | Publish to drafts; TikTok ignores the rest of the post settings |
| `photo_cover_index` | int | — | Cover photo index for photo posts (0-based) |
| `privacy_level` | str | `photo_privacy` / `video_privacy` | Photo posts only unless the connection declares `video_privacy`, see the note below |

## Platform-Specific Options

### TikTok (Video)
- `disable_duet` - Disable duet
- `disable_comment` - Disable comments
- `disable_stitch` - Disable stitch
- `cover_timestamp` - Timestamp in ms for cover
- `is_aigc` - AI-generated content flag
- `post_mode` - DIRECT_POST or MEDIA_UPLOAD
- `brand_content_toggle` - Branded content toggle
- `brand_organic_toggle` - Brand organic toggle

> **TikTok particularity:** `privacy_level` is not accepted on TikTok **video**
> posts — the video is published public, or sent to your TikTok drafts with
> `tiktok_upload_to_draft=True`. On TikTok **photo** posts `privacy_level` *is*
> accepted.

See [TikTok music, location, cover and drafts](#tiktok-music-location-cover-and-drafts)
for the music, location, cover and draft options.

### TikTok (Photos)
- `privacy_level` - PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR, SELF_ONLY
- `post_mode` - DIRECT_POST or MEDIA_UPLOAD
- `auto_add_music` - Auto add music
- `photo_cover_index` - Index of photo for cover (0-based)
- `disable_comment` - Disable comments

### Instagram
- `media_type` - REELS, STORIES, IMAGE
- `share_to_feed` - Share to feed (for Reels/Stories)
- `collaborators` - Comma-separated collaborator usernames
- `cover_url` - Custom cover URL
- `audio_name` - Audio track name
- `user_tags` - Comma-separated user tags
- `location_id` - Location ID
- `thumb_offset` - Thumbnail offset

### YouTube
- `tags` - List or comma-separated tags
- `categoryId` - Category ID (default: "22" People & Blogs)
- `privacyStatus` - public, unlisted, private
- `embeddable` - Allow embedding
- `license` - youtube, creativeCommon
- `publicStatsViewable` - Show public stats
- `thumbnail_url` - Custom thumbnail URL
- `selfDeclaredMadeForKids` - Made for kids (COPPA)
- `containsSyntheticMedia` - AI/synthetic content flag
- `defaultLanguage` - Title/description language (BCP-47)
- `defaultAudioLanguage` - Audio language (BCP-47)
- `allowedCountries` / `blockedCountries` - Country restrictions
- `hasPaidProductPlacement` - Paid placement flag
- `recordingDate` - Recording date (ISO 8601)
- `youtube_playlist_id` - Playlist ID (single string, list, or comma-separated) to add the uploaded video to after publishing

### LinkedIn
- `visibility` - PUBLIC, CONNECTIONS, LOGGED_IN, CONTAINER
- `target_linkedin_page_id` - Page ID for organization posts

### Facebook
- `facebook_page_id` - Facebook Page ID (required)
- `video_state` - PUBLISHED, DRAFT
- `facebook_media_type` - REELS, STORIES, or VIDEO (normal page video)
- `thumbnail_url` - Thumbnail URL for normal page videos (only when `facebook_media_type` is VIDEO)
- `facebook_link_url` - URL for text posts

### Pinterest
- `pinterest_board_id` - Board ID
- `pinterest_link` - Destination link
- `pinterest_alt_text` - Alt text for photos
- `pinterest_cover_image_url` - Cover image URL (video)
- `pinterest_cover_image_key_frame_time` - Key frame time in ms

### X (Twitter)
- `reply_settings` - everyone, following, mentionedUsers, subscribers, verified
- `nullcast` - Promoted-only post
- `tagged_user_ids` - User IDs to tag
- `place_id` / `geo_place_id` - Location place ID
- `quote_tweet_id` - Tweet ID to quote
- `poll_options` - Poll options (2-4)
- `poll_duration` - Poll duration in minutes (5-10080)
- `for_super_followers_only` - Exclusive for super followers
- `community_id` - Community ID
- `share_with_followers` - Share community post with followers
- `card_uri` - Card URI for Twitter Cards
- `x_long_text_as_post` - Post long text as single post
- `x_thread_image_layout` - Comma-separated image layout for thread (e.g. "4,4" or "2,3,1"). Each value 1-4, total must equal image count. Auto-chunks into groups of 4 when >4 images.

### Threads
- `threads_long_text_as_post` - Post long text as single post (vs thread)
- `threads_thread_media_layout` - Comma-separated list of how many media items to include in each Threads post (e.g. "5,5" or "3,4,3"). Each value 1-10, total must equal media count. Auto-chunks into groups of 10 when >10 items.
- `threads_topic_tag` - Topic tag for the Threads post (1-50 characters, no periods or ampersands). One tag per post. Helps increase reach.

### Reddit
- `subreddit` - Subreddit name (without r/)
- `flair_id` - Flair template ID

### Google Business
- `gbp_location_id` - Location, e.g. `"accounts/123/locations/456"` (list them with `get_google_business_locations`). Required when the account has more than one location; the API only auto-selects when exactly one exists.
- `gbp_post_type` - `MEDIA`, `PHOTO` or `GALLERY` to publish into the location's photo gallery instead of creating a Local Post. Any other value, or omitting it, keeps the Local Post behaviour.
- `gbp_media_category` - Gallery category, default `ADDITIONAL`. One of `COVER`, `PROFILE`, `LOGO`, `EXTERIOR`, `INTERIOR`, `PRODUCT`, `AT_WORK`, `FOOD_AND_DRINK`, `MENU`, `COMMON_AREA`, `ROOMS`, `TEAMS`, `ADDITIONAL`.
- `gbp_topic_type` - STANDARD, EVENT or OFFER
- `gbp_media_url` / `gbp_media_format` - Media attached to the post
- `gbp_cta_type` / `gbp_cta_url` - Call-to-action button
- `gbp_event_title` / `gbp_event_start_date` / `gbp_event_start_time` / `gbp_event_end_date` / `gbp_event_end_time` - Used with `gbp_topic_type="EVENT"`
- `gbp_offer_coupon` / `gbp_offer_redeem_url` / `gbp_offer_terms` - Used with `gbp_topic_type="OFFER"`

```python
locations = client.get_google_business_locations("my-profile")

# Publish a photo straight into the location's gallery
client.upload_photos(
    ["storefront.jpg"],
    user="my-profile",
    platforms=["google_business"],
    gbp_location_id=locations["locations"][0]["name"],
    gbp_post_type="GALLERY",
    gbp_media_category="EXTERIOR",
)
```

## Common Options

These options work across all upload methods:

| Option | Description |
|--------|-------------|
| `title` | Post title/caption (required) |
| `user` | Profile name (required) |
| `platforms` | Target platforms list (required) |
| `first_comment` | First comment to post |
| `alt_text` | Alt text for accessibility |
| `scheduled_date` | ISO date for scheduling |
| `timezone` | Timezone for scheduled date |
| `add_to_queue` | Add to posting queue |
| `max_posts_per_slot` | Max posts per queue slot (overrides profile setting) |
| `async_upload` | Process asynchronously (default: True) |

## Error Handling

```python
from upload_post import UploadPostClient, UploadPostError

client = UploadPostClient("YOUR_API_KEY")

try:
    response = client.upload_video("video.mp4", **options)
    print("Upload successful:", response)
except UploadPostError as e:
    print("Upload failed:", str(e))
```

## Links

- [Upload-Post Website](https://www.upload-post.com)
- [API Documentation](https://docs.upload-post.com)
- [Dashboard](https://app.upload-post.com)

## License

MIT

<!-- deployed 2026-03-16 17:49 UTC -->
