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
- ✅ **Audience** - Who follows a profile, per platform
- ✅ **Suggestions** - Hashtags and searches to post about, per platform
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

# TikTok: find a track by song or artist
found = client.search_tiktok_music("my-profile", q="bad bunny", country_code="ES")

# TikTok: search locations to tag
locations = client.get_tiktok_locations("my-profile", "Madrid")
```

### Comments

The same methods cover every platform that has comments — Instagram, Facebook,
YouTube, LinkedIn and TikTok. There is no per-network method: the endpoint
answers one question and `platform` says who to ask.

```python
# Read the comments on a post. TikTok has no post-URL lookup: pass the video id.
comments = client.get_post_comments(
    user="my-profile",
    platform="tiktok",
    post_id="7412345678901234567",
    limit=20,
)

# Read the replies hanging from one of them — same question, one more parameter
replies = client.get_post_comments(
    user="my-profile",
    platform="tiktok",
    post_id="7412345678901234567",
    comment_id="7412345678909999999",
)

# Comment on the post, or reply to a comment
client.create_comment(
    user="my-profile",
    platform="tiktok",
    post_id="7412345678901234567",
    message="Thanks for watching!",
)
client.create_comment(
    user="my-profile",
    platform="tiktok",
    comment_id="7412345678909999999",
    message="Glad you liked it",
)

# Delete one
client.delete_comment(
    user="my-profile", platform="tiktok", comment_id="7412345678909999999"
)
```

You can also have the first comment posted for you right after publishing, with
`first_comment` for every platform or `tiktok_first_comment` for TikTok alone.

On TikTok all of this needs the `comments` capability, which the account grants
when it connects — see
[What a TikTok connection can do](#what-a-tiktok-connection-can-do-capabilities).

#### Moderating a comment: hide, like, pin

`comment_action()` does the three and undoes them, on any platform that
supports it. Each action carries its own inverse, and `post_id` is only sent
when the platform needs it:

```python
client.comment_action(
    user="my-profile", platform="tiktok", action="hide",
    comment_id="7412345678909999999", post_id="7412345678901234567",
)
client.comment_action(
    user="my-profile", platform="tiktok", action="like",
    comment_id="7412345678909999999",
)
client.comment_action(
    user="my-profile", platform="tiktok", action="unpin",
    comment_id="7412345678909999999", post_id="7412345678901234567",
)
```

| `action` | Undo | `post_id` |
| --- | --- | --- |
| `hide` | `unhide` | required |
| `like` | `unlike` | not sent |
| `pin` | `unpin` | required |

### Audience

Where the analytics methods answer *how did my posts do*, `get_audience()`
answers *who is following me*. One endpoint, one `platform` parameter, like
every other question in the API.

```python
audience = client.get_audience(
    user="my-profile",
    platform="tiktok",
    start_date="2026-07-01",
    end_date="2026-07-30",
)

print(audience["range"])                 # the window actually used
print(audience["audience"]["countries"])  # and "cities", "ages", "genders"
print(audience["activity_by_hour"])       # [{"hour": "14", "followers_online": 1494}, ...]
print(audience["followers_daily"])        # [{"date", "total", "new", "lost"}, ...]
print(audience["profile_actions"])        # bio link, address, email, phone, leads
print(audience["bio_description"])
```

The window is clamped on the server: at most 60 days, and `end_date` always
before today. A wider window is trimmed to what the platform accepts instead of
failing.

Ask for a `benchmark_category` and the same call also returns how the account
compares with the average of that category. The accepted categories come back in
`benchmark_categories` on every response, so a picker needs no second call:

```python
categories = client.get_audience(
    user="my-profile", platform="tiktok"
)["benchmark_categories"]

benchmark = client.get_audience(
    user="my-profile", platform="tiktok",
    benchmark_category="SOFTWARE_AND_APPS",
)["benchmark"]
print(benchmark["average_engagement_rate"], benchmark["average_video_views"])
```

### Suggestions

`get_suggestions()` answers *what is worth posting about*: the hashtags or the
searches a platform suggests around a keyword. One endpoint for both, told apart
by `type`.

```python
hashtags = client.get_suggestions(
    user="my-profile", platform="tiktok", type="hashtags",
    q="pilates", country_code="ES", language="es",
)["hashtags"]
print(hashtags)  # [{"name": ..., "view_count": ...}, ...]

keywords = client.get_suggestions(
    user="my-profile", platform="tiktok", type="keywords", q="pilates",
)["keywords"]
```

Per-post numbers stay in `get_post_analytics()`. On TikTok that response carries
more than the usual counters: `retention` (the curve, second by second),
`impression_sources` (For You, search, profile...), `audience_types` (followers
vs non-followers), `new_followers`, `reach` and the watch times.

Asking a platform a question it cannot answer fails with
`platform_not_supported` and the list of the ones that can.

## What a TikTok connection can do (`capabilities`)

Not every TikTok connection can do the same things. `client.list_users()`
(`GET /api/uploadposts/users`) returns a `capabilities` array on each profile's
TikTok account; check it before offering a feature.

| Capability | What it unlocks |
| --- | --- |
| `music` | `tiktok_music_id` and the volume/trim fields, plus `get_tiktok_trending_music()` and `search_tiktok_music()` |
| `location` | `tiktok_location_id` / `tiktok_location_name`, plus `get_tiktok_locations()` |
| `cover_image` | `tiktok_cover_image_url` |
| `cover_timestamp` | `cover_timestamp` |
| `draft` | `tiktok_upload_to_draft` |
| `video_privacy` | `privacy_level` on video |
| `photo_privacy` | `privacy_level` on photo posts |
| `profile_analytics` | `get_audience()` and `get_suggestions(type="hashtags")` with `platform="tiktok"` |
| `comments` | Comments on TikTok: `get_post_comments()` (top-level and replies), `create_comment()`, `delete_comment()`, `comment_action()` and `tiktok_first_comment` |
| `trend_search` | `get_suggestions(type="keywords")` with `platform="tiktok"` |

> **`comments` and `trend_search` need the account to be reconnected.** TikTok
> grants them at connect time, so an account linked before they existed keeps
> working for everything else but will not list them — reconnect it from Manage
> Users to enable them.

If a connection lacks a capability the upload field is simply ignored: the post
still publishes and the response carries a per-field `warnings` string. The
methods above answer with an error asking for a reconnection.

## TikTok music, location, cover and drafts

> Needs the `music`, `location`, `cover_image` or `draft` capability — see
> [What a TikTok connection can do](#what-a-tiktok-connection-can-do-capabilities).

```python
# 1. Pick a track and a place
tracks = client.get_tiktok_trending_music("my-profile", country_code="ES")["tracks"]
# ...or find one by name. TikTok has no music search endpoint, so this searches
# the trending charts Upload-Post caches, not TikTok's whole catalogue.
tracks = client.search_tiktok_music("my-profile", q="bossa", country_code="ES")["tracks"]
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
| `tiktok_music_id` | str | `music` | Video + photos. The track `id` from `get_tiktok_trending_music()` or `search_tiktok_music()` (not `commercial_music_id`) |
| `tiktok_music_volume` | int | `music` | Video only. 0-100, defaults to 50 when music is set |
| `tiktok_music_start` | int | `music` | Video only. Music start offset in ms |
| `tiktok_music_end` | int | `music` | Video only. Music end offset in ms |
| `tiktok_original_sound_volume` | int | `music` | Video only. 0-100, defaults to 50 when music is set, so the original audio is not muted |
| `tiktok_location_id` | str | `location` | Video + photos. `location_id` from `get_tiktok_locations()` |
| `tiktok_location_name` | str | `location` | Required whenever `tiktok_location_id` is set |
| `tiktok_cover_image_url` | str | `cover_image` | Video only. Custom cover image URL |
| `tiktok_is_ai_generated` | bool | — | Video + photos. AI-generated content disclosure |
| `tiktok_upload_to_draft` | bool | `draft` | Video only. Publish to drafts; TikTok ignores the rest of the post settings |
| `photo_cover_index` | int | — | Cover photo index for photo posts (0-based) |
| `privacy_level` | str | `photo_privacy` / `video_privacy` | Accepted on video and photo posts alike; which values the account may use is decided by TikTok, see the note below |

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

> **TikTok particularity:** `privacy_level` works on video and photo posts
> alike, but **TikTok decides per account which values are available**. A
> private account, for example, is offered `FOLLOWER_OF_CREATOR`,
> `MUTUAL_FOLLOW_FRIENDS` and `SELF_ONLY`, with no `PUBLIC_TO_EVERYONE`; asking
> for one the account does not have fails with
> `error_code="tiktok_privacy_unavailable"` and an error listing the ones it
> does have. Omit it on video and TikTok applies the account's own default; on
> photo posts it defaults to `PUBLIC_TO_EVERYONE`. To offer only the values that
> will actually work, ask the account with
> `client.get_tiktok_publishing_settings(profile)` and read
> `privacy_level_options`.

See [TikTok music, location, cover and drafts](#tiktok-music-location-cover-and-drafts)
for the music, location, cover and draft options.

### TikTok (Photos)
- `privacy_level` - PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR, SELF_ONLY
- `post_mode` - DIRECT_POST or MEDIA_UPLOAD
- `auto_add_music` - Auto add music
- `photo_cover_index` - Index of photo for cover (0-based)
- `disable_comment` - Disable comments
- `tiktok_music_id` - Commercial Music Library track id
- `tiktok_location_id` / `tiktok_location_name` - Location tag, both required together
- `tiktok_is_ai_generated` - AI-generated content disclosure

> TikTok's photo contract takes the music track id alone: `tiktok_music_volume`,
> `tiktok_music_start`, `tiktok_music_end`, `tiktok_original_sound_volume`,
> `tiktok_cover_image_url` and `tiktok_upload_to_draft` are video-only.

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
| `tiktok_first_comment` | First comment for TikTok only (needs the `comments` capability) |
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
