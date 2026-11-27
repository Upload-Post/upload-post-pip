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

### Timeouts and retries

Every request has a timeout: 60 seconds by default, and 10 minutes for uploads
and other requests that send or download a file (a synchronous upload waits on
the server before it answers, and a big video takes minutes to send). A
request that runs out raises `UploadPostError` with `status_code` `None`.
Change them in seconds (`None` or `0` = no limit):

```python
client = UploadPostClient("YOUR_API_KEY", timeout=30, upload_timeout=1800)
```

A timed-out upload may still have reached the API. Give every upload an
`idempotency_key` (sent as the `Idempotency-Key` header) and reuse it when you
retry: the API returns the first upload instead of publishing it twice.

```python
import uuid

key = str(uuid.uuid4())  # once, outside the retry loop
client.upload_video("video.mp4", title="Hi", user="my-profile",
                    platforms=["tiktok"], idempotency_key=key)
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
- ✅ **Comments** - Read, reply, moderate; replies under a comment on TikTok, Threads, YouTube, Instagram, Facebook and LinkedIn
- ✅ **Direct Messages** - Instagram, WhatsApp (messaging only: WhatsApp does not publish posts), Bluesky and Telegram bot DMs
- ✅ **AutoDM rules** - Account-wide Instagram comment/story/keyword DMs
- ✅ **Webhook deliveries** - 7-day delivery log and redelivery
- ✅ **Phone numbers** - Buy a number for WhatsApp, SMS and calls (paid plans; no emergency calls)
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

# Any file up to 50 MB to Telegram (or both, with platforms=["linkedin", "telegram"])
client.upload_document("archive.zip", title="Files", user="my-profile", platforms=["telegram"])
```

### Upload fields added in 2.22.0

- **Threads**: `threads_gif_id` (text posts, a GIPHY id), `threads_spoiler_media`
  (images, videos, carousels), `threads_text_spoilers` (`[{"offset", "length"}]`, up to
  10) and `threads_ghost_post` (a temporary text post; `list_threads_ghost_posts` shows
  when it expires).
- **Facebook** (text posts): `facebook_backdated_time` (a past Unix time or ISO 8601
  date) and `facebook_backdated_time_granularity` (`year`, `month`, `day`, `hour`, `minute`).
- **X**: `x_video_title`, `x_video_description`, `x_video_cta` (`visit_site`,
  `watch_now`, `app_install`), `x_video_cta_url`, `x_video_cta_app_store_id`,
  `x_video_cta_ipad_app_store_id`, `x_video_cta_play_store_id` (videos); `x_clip_post_id`,
  `x_clip_start_seconds`, `x_clip_end_seconds` (text posts: a clip of the video of
  another post of the account).
- **Instagram**: a single video sent with `upload_photos` is published as a Reel and
  takes `cover_url` (a URL), `thumb_offset`, `share_to_feed` and `audio_name`;
  `user_tags` also works on a video Story.

X reads and actions that need an X permission (bookmarks, lists, followers and following,
likers, `reposts_of_me`, hiding replies) only work with an X account connected or
reconnected on or after 2026-11-25; an older connection answers `403`
`x_reconnect_required` (reconnect X to grant them).

```python
client.upload_text(
    title="Guess what is coming",
    user="my-profile",
    platforms=["threads"],
    threads_ghost_post=True,
    threads_text_spoilers=[{"offset": 6, "length": 4}],
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

# Fix the text in place (only the platforms listed change)
client.edit_scheduled(
    "job-id",
    platform_content={"instagram": {"caption": "New Instagram caption"}},
)

# Change any other option by its API form name (None removes it), schedule the
# video natively on YouTube, or replace the Reels cover
client.edit_scheduled(
    "job-id",
    fields={"privacyStatus": "unlisted", "disable_comment": True},
    youtube_publish_at="2026-11-01T09:00:00Z",
    cover_image_base64="data:image/jpeg;base64,...",  # or remove_cover=True
)

# Cancel a scheduled post
client.cancel_scheduled("job-id")
```

### User Management

```python
# List all profiles
users = client.list_users()

# Create a new profile (409 "Username already in use" if it exists,
# 403 PROFILE_LIMIT_REACHED at the plan's profile limit)
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

### Post Analytics and TikTok drafts

```python
# Every platform the upload went to, or just one of them
stats = client.get_post_analytics("REQUEST_ID")
tiktok = client.get_post_analytics("REQUEST_ID", platform="tiktok")

# Any post of the account by its native id (e.g. one returned by get_media)
client.get_post_analytics_by_platform_id("7412345678901234567", "tiktok", "my-profile")
```

A TikTok upload sent to drafts (`post_mode="MEDIA_UPLOAD"` or
`tiktok_upload_to_draft=True`) has no post until the creator publishes it from
the TikTok app. Call `get_post_analytics(request_id)` after that: Upload-Post
asks TikTok which post came from the draft, then returns its metrics and fills
in `platform_post_id` and `post_url`.

- While the draft is still in the inbox, `post_metrics_error` says so. That
  answer is reused for a while (about 5 minutes for a fresh upload, up to 6
  hours for one several days old); after 30 days without a post Upload-Post
  stops asking.
- TikTok only gives the post id once the post is **public** and moderated. A
  draft published as private never gets per-post analytics.
- TikTok rows carry `original_publish_id` (the upload's TikTok `publish_id`),
  here and in `get_cached_post_analytics`. `post_url` is empty when the
  account's @username is not known.

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

# Resolve any LinkedIn company Page to the urn + exact name a mention needs
org = client.resolve_linkedin_organization(
    "my-profile", "https://www.linkedin.com/company/linkedin/"
)
print(org["urn"], org["name"], org["mention"])  # urn:li:organization:1337 LinkedIn @[LinkedIn](urn:li:organization:1337)

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

# Same on Instagram, Facebook and LinkedIn (company Pages). On LinkedIn pass the
# comment_urn from the listing; a bare id is only looked up in the first 250.
replies = client.get_post_comments(
    user="my-profile",
    platform="linkedin",
    post_id="urn:li:share:7500811262105264139",
    comment_id="urn:li:comment:(urn:li:activity:7500811262105264139,7503818768586981376)",
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

Replies (`comment_id`) work on TikTok, Threads, YouTube, Instagram, Facebook and
LinkedIn (company Pages only); `post_id` is still required. X and Bluesky answer
`platform_not_supported`. Error codes you can branch on with
`UploadPostError.error_code`:

| `error_code` | Status | Meaning |
| --- | --- | --- |
| `invalid_comment_id` | 400 | Wrong format (Instagram: digits; Facebook: `{post}_{comment}`; LinkedIn: digits or the `comment_urn`) |
| `invalid_cursor` | 400 | LinkedIn replies: `after` must be the number from `next_cursor` |
| `comment_not_found` | 404 | Instagram/Facebook do not know the comment (one without replies is a 200 with an empty list) |
| `linkedin_comment_not_found` | 404 | Bare LinkedIn id not among the post's first 250 comments: pass the `comment_urn` |
| `linkedin_personal_not_supported` | 403 | Personal LinkedIn profile: LinkedIn only lets us read company Pages |
| `linkedin_page_access_denied` | 403 | The member who connected LinkedIn is no longer an admin of the Page |

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

### Direct Messages

One pair of methods for every messaging platform: `instagram`, `whatsapp`
and `bluesky`. `send_dm` also sends from your own
Telegram bot (`platform="telegram"`) to people who started it, and
`get_dm_conversations(platform="telegram", ...)` reads them once the bot's
updates are turned on.

```python
# Instagram: by the person's Instagram-scoped id, inside the 24-hour window
client.send_dm("my-profile", "instagram", recipient_id="1784...", message="Thanks!")

# Bluesky: by handle, DID or profile link. Links, #hashtags and @mentions are clickable
sent = client.send_dm(
    "my-profile", "bluesky",
    recipient_id="alice.bsky.social",
    message="Our new guide: https://example.com/guide",
)

# Share a Bluesky post, reply to a message, or act on one (no DM quota used)
client.send_dm("my-profile", "bluesky", recipient_id="alice.bsky.social",
               message="Look at this",
               attachments={"type": "post", "url": "https://bsky.app/profile/alice.bsky.social/post/3l5t..."})
client.send_dm("my-profile", "bluesky", conversation_id=sent["conversation_id"],
               sender_action="react", message_id=sent["message_id"], reaction="🔥")
client.send_dm("my-profile", "bluesky", conversation_id=sent["conversation_id"],
               sender_action="mark_read")

# Read conversations (Bluesky: at most 25 per page)
page = client.get_dm_conversations("my-profile", "bluesky", messages_limit=5)
for convo in page["conversations"]:
    print(convo["id"], convo.get("status"), convo.get("unread_count"))

# Bluesky-only filters: one conversation and its older messages, requests, unread
client.get_dm_conversations("my-profile", "bluesky", conversation_id="3l5ttwb6ycx2f",
                            messages_cursor="...")
client.get_dm_conversations("my-profile", "bluesky", status="request", read_state="unread")
```

Any other `/dms/send` field (WhatsApp `template`, `location`, `contacts`,
`list`, `cta_url`...) goes through as a keyword
argument, dicts and lists as JSON. **Bluesky DMs need an app password created with "Allow access to your
direct messages"** (Bluesky > Settings > Privacy and security > App passwords),
then reconnect Bluesky with it; otherwise the API answers 403
`bluesky_dm_scope_missing`. Other Bluesky codes:

| `error_code` | Status | Meaning |
| --- | --- | --- |
| `bluesky_recipient_unavailable` | 403 | The recipient does not accept your DM (`reason`: `MessagesDisabled`, `NotFollowedBySender`, `BlockedActor`...). No quota used |
| `bluesky_recipient_not_found` / `bluesky_conversation_not_found` / `bluesky_post_not_found` | 404 | Unknown handle, conversation or shared post |
| `bluesky_message_too_long` | 400 | More than 1000 characters. Nothing sent |
| `bluesky_rejected` | 400 | Bluesky refused it (e.g. a reaction that is not a single emoji) |
| `bluesky_reauth_required` | 401 | Reconnect Bluesky |
| `bluesky_rate_limited` | 429 | Wait `retry_after` seconds |
| `bluesky_chat_unavailable` / `bluesky_edge_rate_limited` | 502 / 503 | Nothing was sent; retry later |
| `bluesky_send_unconfirmed` | 504 | **It may have been sent.** Do not retry automatically: read the conversation first |

#### WhatsApp DMs

WhatsApp is a messaging channel, not a place to publish: the upload methods
never send to it. Connect the profile's WhatsApp Business number (the connect
page, or `generate_jwt(..., platforms=["whatsapp"])`) and write from it with
`send_dm(user, "whatsapp", ...)`. `recipient_id` is the phone number in
international format. Meta bills the conversations to your WhatsApp Business
Account.

Free text, media and interactive messages only go inside the **24-hour
customer-service window** that opens each time the person writes to you.
Outside it Meta refuses (`meta_error_code` 131047): send an approved template.

```python
# Inside the 24 h window: text with reply buttons
client.send_dm("my-profile", "whatsapp", recipient_id="+34600000000",
               message="Your order is ready. Pick it up today?",
               buttons=[{"id": "yes", "title": "Yes"}, {"id": "later", "title": "Tomorrow"}])

# Outside the window: an approved template
client.send_dm("my-profile", "whatsapp", recipient_id="+34600000000",
               template={"name": "order_ready", "language": "en_US",
                         "components": [{"type": "body",
                                         "parameters": [{"type": "text", "text": "#1042"}]}]})

# Media: upload a local file (or put an https "url" straight in the attachment)
media = client.upload_dm_media("my-profile", "invoice.pdf", platform="whatsapp")
client.send_dm("my-profile", "whatsapp", recipient_id="+34600000000",
               attachments={"type": media["type"], "media_id": media["media_id"],
                            "filename": "invoice.pdf"})

# Mark an inbound message as read and show "typing..." (no DM allowance used)
client.send_dm("my-profile", "whatsapp", recipient_id="+34600000000",
               sender_action="mark_read", message_id="wamid.HBg...", typing=True)
```

Other WhatsApp fields of `send_dm`: `attachments` (up to 10, `{"type": "image" |
"video" | "audio" | "document" | "sticker", "url" | "media_id", "caption"?,
"filename"?}`), `reply_to` (wamid), `location`, `contacts`, `list`, `cta_url`,
`header`, `footer` and `reaction` (`{"message_id", "emoji"}`). Inbound media
arrive with a `media_id`: download them with
`download_dm_media("whatsapp", user, media_id)`.

```python
# Templates (Meta reviews new ones: PENDING, then APPROVED or REJECTED)
client.list_dm_templates("my-profile", status="APPROVED")
client.create_dm_template("my-profile", "order_ready", category="UTILITY",
                          language="en_US", body="Your order {{1}} is ready.",
                          examples=["#1042"])
client.delete_dm_template("my-profile", "order_ready")

# Business profile of the number (file = new profile photo, JPEG/PNG)
client.get_whatsapp_business_profile("my-profile")
client.update_whatsapp_business_profile("my-profile", about="Open 9-18",
                                        websites=["https://example.com"], file="logo.png")

# QR codes / wa.me links that open a chat with a prefilled message
qr = client.create_whatsapp_qr_code("my-profile", "Hi! I want to order")["qr_code"]
client.list_whatsapp_qr_codes("my-profile")
client.delete_whatsapp_qr_code("my-profile", qr["code"])
```

Errors come as `UploadPostError.error_code`: 400 `whatsapp_invalid_request`,
401 `whatsapp_reauth_required` (reconnect the number). Meta's own code is in
`error.response["meta_error_code"]`: 131047 outside the window (send a
template), 131026 undeliverable, 131030 recipient not allowed on a test number.

New DMs (Instagram, WhatsApp and Bluesky) can also reach you as the
opt-in `dm_received` webhook. Bluesky has no push, so Upload-Post checks every
5 minutes.

### AutoDM rules (whole Instagram account)

A rule answers comments on **every** post and reel of the account (present and
future), plus story replies, story mentions and keyword DMs. Rules never expire
and work only from Meta's real-time notifications.

```python
rule = client.create_autodm_rule(
    profile_username="my-profile",
    reply_message="Here is your free guide!",
    triggers=["comment", "story_reply", "story_mention", "dm_keyword"],
    trigger_keywords=["guide"],            # required for dm_keyword
    buttons=[{"title": "Get the guide", "url": "https://example.com/guide"}],
    per_user_cooldown_hours=24,            # 0-720; never < 24 for story/DM triggers
)["rule"]

for r in client.list_autodm_rules("my-profile")["rules"]:
    print(r["rule_id"], r["status"], r["webhook"]["receiving_events"], r["webhook"].get("hint"))

client.pause_autodm_rule(rule["rule_id"])
client.resume_autodm_rule(rule["rule_id"])
client.delete_autodm_rule(rule["rule_id"])
```

- Up to 10 rules per Instagram account; they do not count towards the
  2-monitors-per-day limit. A post with its own monitor is answered by that
  monitor only.
- Pace: 25 DMs per account every 15 minutes plus the plan's daily DM allowance;
  what does not fit is queued for up to 24 hours.
- Errors: 409 `duplicate_rule` / `rule_limit_reached` /
  `rule_creation_in_progress`, 502 `webhook_subscription_failed` (reconnect
  Instagram), 503 `account_rules_disabled`, 409 `rule_stopped` on resume when
  the account left its profile.

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

## Webhooks: configuration, delivery log and redelivery

```python
# Turn the webhook on and opt into the inbound events
client.update_notification_config(
    webhook_url="https://example.com/upload-post",
    webhook_events=["upload_completed", "dm_received", "comment_received"],
    channels={"webhook": True},
)
print(client.get_notification_config()["notifications"]["webhook_secret"])

# Did an event reach my server? (7-day history, newest first)
failed = client.list_webhook_deliveries(status="failed", limit=20, include_payload=True)
for d in failed["deliveries"]:
    print(d["delivery_id"], d["event"], d["attempt_count"], d["last_status_code"], d["last_error"])

# One delivery with its exact payload, and send it again
one = client.get_webhook_delivery(failed["deliveries"][0]["delivery_id"])
again = client.redeliver_webhook(one["delivery"]["delivery_id"])
print(again["delivery"]["delivery_id"], again["delivery"]["redelivery_of"])
```

Webhooks are delivered **at least once**: a timeout, connection error, `5xx`,
`408` or `429` is retried with the same body and the same
`X-Upload-Post-Delivery` id (6 attempts over about 8.5 hours, header
`X-Upload-Post-Attempt` 1-6); other `4xx` answers are final. Deduplicate by
`X-Upload-Post-Delivery`. A redelivery is a new delivery with its own id and
`X-Upload-Post-Redelivery-Of`. Filters of `list_webhook_deliveries`: `event`,
`status` (`pending`, `delivered`, `failed`, `cancelled`), `request_id`,
`job_id`, `profile_username`, `limit` (1-100), `page` (1-50). `redeliver_webhook`
answers 409 `webhook_removed` / `event_unsubscribed` / `blocked_url` when there
is nowhere to send it.

## Phone numbers

Buy a phone number inside Upload-Post and use it for WhatsApp, SMS and calls
([guide](https://docs.upload-post.com/api/phone-numbers)). Paid plans only (a
trial or the Free plan answers `402` `phone_numbers_paid_plan_required` with
`upgrade_url`). Each number costs $3 to $30 per month depending on country and
type (no setup fee), charged on your subscription; usage (outbound SMS,
forwarded minutes, recording, transcription) goes on the next invoice. Numbers
**cannot call emergency services** (112/911) and make no outbound calls. If
phone numbers are not available for your account yet, `get_phone_numbers_config`
answers `enabled: false` and the other methods `403` `phone_numbers_not_available`.

```python
import uuid

# 1. Can this account buy, and which terms apply?
config = client.get_phone_numbers_config()  # enabled, can_purchase, reason, terms_version, terms_url...

# 2. Pick a number (countries: US, GB, ES, FR, DE, IT, MX, BR; types local, mobile, national)
countries = client.list_phone_number_countries()["countries"]  # per type: monthly_cents, needs_kyc, sms, sms_send
numbers = client.search_available_phone_numbers("ES", number_type="mobile", sms=True)["numbers"]

# 3. Buy it. purchase_intent_id is your idempotency key: repeat it to retry
#    safely, it never charges twice.
end_user = {
    "type": "business",  # or "individual"
    "first_name": "Ana", "last_name": "García", "business_name": "Acme SL",
    "phone": "+34600111222", "email": "ana@example.com",
    "address": {"street_address": "Calle Mayor 1", "locality": "Madrid",
                "postal_code": "28013", "country_code": "ES"},
}
bought = client.purchase_phone_number(
    "my-profile", "ES", "mobile", str(uuid.uuid4()), end_user,
    accept_terms=True,  # no emergency calls, acceptable use: config["terms_url"]
    terms_version=config["terms_version"],
    phone_number=numbers[0]["phone_number"],
)
# 200: status "active". 202: "kyc_required" (nothing charged yet) or
# "pending_regulatory" (paid, under review by our carrier; the
# phone_number_activated or phone_number_declined webhook tells you the result).
```

Some countries need identity documents. `get_phone_number_kyc_fields` lists
them; send them with the same fields as the purchase. The client sends the
documents base64-encoded in JSON (PDF, JPG or PNG, up to 10 MB each):

```python
import base64

fields = client.get_phone_number_kyc_fields("DE", number_type="local")["fields"]
# fields["requirements"]: [{"requirement_id", "label", "kind": text|date|address|file, ...}]
with open("id.pdf", "rb") as fh:
    content = base64.b64encode(fh.read()).decode()
client.submit_phone_number_kyc(
    "my-profile", "DE", "local", purchase_intent_id, end_user,
    accept_terms=True, terms_version=config["terms_version"],
    values={"req_tax_id": "DE123456789"},                                # text and date requirements
    documents={"req_id_document": {"filename": "id.pdf", "content_base64": content}},  # file requirements
)
# The number stays pending_regulatory until approved; declined = refunded.
```

SMS, calls and the codes to connect WhatsApp (ids are `pn_...`):

```python
number_id = bought["phone_number"]["id"]

# SMS (US/CA numbers receive SMS but cannot send yet; STOP opt-outs are honoured)
client.send_phone_number_sms(number_id, "+34600999888", "Your order has shipped")
messages = client.list_phone_number_messages(number_id, limit=50)["messages"]

# Calls: forward to a number of the same country, voicemail with transcription
client.update_phone_number_voice(number_id, forward_to="tel:+34600111222",
                                 voicemail_enabled=True, transcription_language="es")
# forward_to="" turns forwarding off (None values are not sent)
calls = client.list_phone_number_calls(number_id)["calls"]  # recording URL valid 1 h, transcript

# WhatsApp: there are no pre-verified numbers. Prepare the number, then in the
# dashboard's WhatsApp connect add it and choose "Phone call" (not SMS):
# Upload-Post answers Meta's call and the code shows up in list_phone_number_codes.
client.prepare_phone_number_whatsapp(number_id, language="en")  # 30-minute window
codes = client.list_phone_number_codes(number_id)["codes"]      # poll every few seconds

# Usage and charges of the month
usage = client.get_phone_numbers_usage()
```

Releasing is final: WhatsApp on the number stops working, the carrier may give
the number to someone else later and the monthly charge stops (no proration).
It needs `confirm=True` (otherwise `400` `confirmation_required`). To keep the
number with another carrier, `get_phone_number_port_out_info` gives what the new
carrier needs.

```python
client.release_phone_number(number_id, confirm=True)
```

Webhooks (opt-in: list them in `webhook_events`): `sms_received` (`message`),
`call_received` and `voicemail_received` (`call`), `phone_number_activated`,
`phone_number_declined`, `phone_number_released` and `phone_number_port_out`
(`number`, plus `reason` or `port_out_status`). Every body has `event`,
`platform: "phone"`, `account_id` (the `pn_...` id), `phone_number` and
`profile_username`. Only the account owner can buy, send documents, release or
port out a number (team members get `403` `phone_numbers_owner_only`). Terms:
https://docs.upload-post.com/resources/phone-number-terms

## Team members (acting on the owner's account)

```python
client = UploadPostClient("MEMBER_API_KEY", act_as_user="owner@example.com")
client.list_users()  # the owner's profiles
```

Every request carries `X-Act-As-User`. If the owner's current plan no longer
covers your seat (the last invited members are suspended after a downgrade,
never removed), requests fail with `status_code` 403 and `error_code`
`"TEAM_SEAT_SUSPENDED"`; access comes back by itself when the owner upgrades or
frees a seat.

`list_team_members()` (owner) and `list_shared_accounts()` (member) show who is
on the team and `suspended` / `suspended_reason`. Profile webhooks:
`get_profile_webhook`, `set_profile_webhook`, `delete_profile_webhook`; also
`delete_notification_webhook()` and `rotate_webhook_secret()`.

### Roles and post approvals (not generally available yet)

Team roles (admin, editor, contributor, viewer) and the approval queue are
**not generally available yet**: while they are switched off the approval
methods answer HTTP 503 (`post_approvals_disabled`) and every member acts as an
Admin. The owner invites members and sets their role and profiles in the
dashboard; that is not done with the API key. With the API you can read them:
`get_team_roles()` (roles and your own), `list_team_members()` and
`list_shared_accounts()` (each entry adds `role` and `profiles`, `None` = every
profile) and `list_team_audit()` (owner and Admins).

When an Editor uploads, the post is **not** published or scheduled: the upload
answers HTTP 202 with `pending_approval: True`, `approval_id`,
`approval_status: "pending_approval"` and `job_id: None` (a Contributor gets
`approval_status: "draft"`). A reviewer (owner or Admin) decides:

```python
items = client.list_post_approvals(status="pending_approval")["items"]
counts = client.list_post_approvals(count_only=True)  # {"counts": {...}, "total": n}

item = client.get_post_approval(items[0]["approval_id"])["item"]
# version is required: the item["version"] you reviewed (409 approval_version_changed otherwise)
client.approve_post_approval(item["approval_id"], version=item["version"])
# or: comment is required to reject
client.reject_post_approval(item["approval_id"], comment="Fix the caption")
```

`edit_post_approval()` and `withdraw_post_approval()` change or withdraw an
open item. The end client of a white-label profile can decide too: generate the
profile JWT with `generate_jwt(username, client_approval=True)` and call
`list_client_post_approvals(token)`, `approve_client_post_approval(token,
approval_id, version)` or `reject_client_post_approval(token, approval_id,
comment)` with that JWT instead of the API key.

## Post actions, best times, queue, Telegram, Bluesky and Google Business

Editing and reposting published posts, the best time to post, the queue, and
the management endpoints of Telegram, Bluesky and Google Business are plain
methods: the required arguments are positional and **every other keyword is
sent to the API with its API name**, nothing is dropped. A file field (`file`,
`photo`, `animation`, `sticker`, `avatar`, `banner`, `telegram_media`...) given
as a local path, `bytes` or an open file turns the request into
`multipart/form-data`; URLs and Telegram `file_id`s stay strings. Each method
links to its page in the API docs for the full list of fields.

```python
# Best hours to post on Instagram, and a queue that fills them by itself
best = client.get_best_times("my-profile", "instagram", top=3)
client.update_queue_settings("my-profile", slots="auto", auto_slots_count=3,
                             auto_platforms=["instagram", "tiktok"])

# Telegram: pin a post, copy it to another chat, delete every message of an album
client.edit_post("my-profile", "telegram", "42", action="pin")
client.repost_post("my-profile", "telegram", "42", mode="copy", target_chat_id="@other_channel")
client.unpublish_post("my-profile", "telegram", "42", delete_all_messages=True)

# Telegram chat management
client.create_telegram_invite_link("my-profile", name="Newsletter", creates_join_request=True)
client.update_telegram_chat_info("my-profile", photo="logo.jpg")   # multipart

# Bluesky: bookmark a post, read notifications, save a draft
client.post_action("my-profile", "bluesky", "bookmark", post_id="at://did:plc:.../app.bsky.feed.post/3l...")
notifications = client.get_bluesky_notifications("my-profile", limit=20)
client.create_bluesky_draft("my-profile", posts=[{"text": "Coming soon"}])

# Google Business: reviews, gallery, daily metrics, strict location edits
reviews = client.list_google_business_reviews("my-shop", page_size=20)["reviews"]
client.reply_to_google_business_review("my-shop", "Thank you!", review_name=reviews[0]["name"])
client.upload_google_business_media("my-shop", file="dining-room.jpg", category="INTERIOR")
client.get_google_business_performance("my-shop", metrics=["call_clicks", "website_clicks"],
                                       start_date="2026-10-01", end_date="2026-10-31")
client.update_google_business_location_info("my-shop", edit_mode="strict", dry_run=True,
                                            phone="+34 900 000 000")
```

Telegram analytics come from `get_analytics("my-profile", platforms=["telegram"])`
(subscribers or members, reactions, boosts), and Telegram DMs from your own bot
go through `send_dm(platform="telegram", ...)`.

### Posts: edit, repost, actions

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`edit_post`](https://docs.upload-post.com/api/edit-post) | `POST /api/uploadposts/posts/edit` | Edit a published post (Facebook, LinkedIn, X, Google Business, Telegram: text, buttons, pin/unpin, stop a poll, live location, replace the media). |
| [`repost_post`](https://docs.upload-post.com/api/repost) | `POST /api/uploadposts/posts/repost` | Repost / reshare a post (LinkedIn, X, Threads; Telegram forward or copy with `mode`, `post_ids`, `all_messages`). |
| [`post_action`](https://docs.upload-post.com/api/bluesky-post-actions) | `POST /api/uploadposts/posts/action` | Act on a published post: Telegram reactions and forward/copy; Bluesky bookmark/unbookmark, pin/unpin, reply and quote settings, detach/reattach quotes. |
| [`save_post`](https://docs.upload-post.com/api/save-pin) | `POST /api/uploadposts/posts/save` | Save a post: a Pinterest Pin to a board, or a Bluesky bookmark (`platform: "bluesky"`). |

### Best time to post and queue

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_best_times`](https://docs.upload-post.com/api/best-times) | `GET /api/uploadposts/best-times` | Best hours to publish for a connected account, with `source` and `confidence` (`timezone`, `top`, `refresh`, `page_urn`, `facebook_page_id`). |
| [`get_queue_settings`](https://docs.upload-post.com/api/queue-system) | `GET /api/uploadposts/queue/settings` | Queue settings, including `slots_mode`, `auto_slots` and `effective_slots`. |
| [`update_queue_settings`](https://docs.upload-post.com/api/queue-system) | `POST /api/uploadposts/queue/settings` | Update the queue. `slots: "auto"` (or `slots_mode: "auto"`) fills the best hours automatically (`auto_slots_count`, `auto_platforms`, `refresh`); a `slots` array switches back to fixed slots. |
| [`get_queue_preview`](https://docs.upload-post.com/api/queue-system) | `GET /api/uploadposts/queue/preview` | Upcoming queue slots and what is scheduled in each (`count`, max 50). |
| [`get_next_queue_slot`](https://docs.upload-post.com/api/queue-system) | `GET /api/uploadposts/queue/next-slot` | Next free queue slot. |
| [`mark_queue_slot_full`](https://docs.upload-post.com/api/queue-system) | `POST /api/uploadposts/queue/slot-full` | Mark a queue slot (ISO 8601, UTC) as full. |
| [`unmark_queue_slot_full`](https://docs.upload-post.com/api/queue-system) | `DELETE /api/uploadposts/queue/slot-full` | Unmark a queue slot marked as full. |

### Telegram: chat, members and invite links

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_telegram_chat_info`](https://docs.upload-post.com/api/telegram-chat-insights) | `GET /api/uploadposts/telegram/chat-info` | Chat details, subscribers/members and administrators (`include_administrators`, `return_bots`). |
| [`update_telegram_chat_info`](https://docs.upload-post.com/api/telegram-chat) | `PATCH /api/uploadposts/telegram/chat-info` | Change the chat title, description, photo (file or `photo_url`), permissions, slow mode, sticker set... |
| [`get_telegram_boosts`](https://docs.upload-post.com/api/telegram-chat-insights) | `GET /api/uploadposts/telegram/boosts` | Boosts of the chat (with `user_id`: that user's boosts). |
| [`get_telegram_member`](https://docs.upload-post.com/api/telegram-chat) | `GET /api/uploadposts/telegram/members` | Read one member (`user_id`) or list the administrators. |
| [`moderate_telegram_member`](https://docs.upload-post.com/api/telegram-chat) | `POST /api/uploadposts/telegram/members` | Ban, unban, restrict, promote or give a custom title to a member (`action`). |
| [`create_telegram_invite_link`](https://docs.upload-post.com/api/telegram-chat) | `POST /api/uploadposts/telegram/invite-links` | Create an invite link (name, expiry, member limit, join requests, subscription). |
| [`edit_telegram_invite_link`](https://docs.upload-post.com/api/telegram-chat) | `PATCH /api/uploadposts/telegram/invite-links` | Edit an invite link. |
| [`revoke_telegram_invite_link`](https://docs.upload-post.com/api/telegram-chat) | `DELETE /api/uploadposts/telegram/invite-links` | Revoke an invite link. |
| [`create_telegram_primary_invite_link`](https://docs.upload-post.com/api/telegram-chat) | `POST /api/uploadposts/telegram/invite-links/primary` | Generate a new primary invite link (the previous one stops working). |
| [`answer_telegram_join_request`](https://docs.upload-post.com/api/telegram-chat) | `POST /api/uploadposts/telegram/join-requests` | Approve or decline a request to join the chat. |
| [`get_telegram_topic_icons`](https://docs.upload-post.com/api/telegram-chat) | `GET /api/uploadposts/telegram/topics/icons` | Custom emoji that can be used as forum topic icons. |
| [`create_telegram_topic`](https://docs.upload-post.com/api/telegram-chat) | `POST /api/uploadposts/telegram/topics` | Create a forum topic. |
| [`edit_telegram_topic`](https://docs.upload-post.com/api/telegram-chat) | `PATCH /api/uploadposts/telegram/topics` | Edit, close, reopen, hide, unhide or unpin a forum topic. |
| [`delete_telegram_topic`](https://docs.upload-post.com/api/telegram-chat) | `DELETE /api/uploadposts/telegram/topics` | Delete a forum topic. |
| [`unpin_all_telegram_messages`](https://docs.upload-post.com/api/telegram-chat) | `POST /api/uploadposts/telegram/unpin-all` | Unpin every message of the chat (or of a topic). |
| [`leave_telegram_chat`](https://docs.upload-post.com/api/telegram-chat) | `POST /api/uploadposts/telegram/leave` | Make the bot leave the connected chat. |
| [`answer_telegram_suggested_post`](https://docs.upload-post.com/api/telegram-chat) | `POST /api/uploadposts/telegram/suggested-posts` | Approve or decline a suggested post in a channel direct messages chat. |
| [`get_telegram_user_personal_chat_messages`](https://docs.upload-post.com/api/telegram-chat) | `GET /api/uploadposts/telegram/users/{user_id}/personal-chat-messages` | Last messages of a user's personal channel. |
| [`get_telegram_user_profile_audios`](https://docs.upload-post.com/api/telegram-chat) | `GET /api/uploadposts/telegram/users/{user_id}/profile-audios` | Profile audios of a Telegram user. |
| [`get_telegram_share_theme_backdrops`](https://docs.upload-post.com/api/telegram-chat) | `GET /api/uploadposts/telegram/share-theme-backdrops` | Backdrops available for the Telegram share screen theme. |
| [`get_telegram_updates_status`](https://docs.upload-post.com/api/telegram-inbox) | `GET /api/uploadposts/telegram/updates` | Whether update receiving is on for the bot. |

### Telegram: bot profile, commands and stickers

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_telegram_bot_profile`](https://docs.upload-post.com/api/telegram-bot-profile) | `GET /api/uploadposts/telegram/bot-profile` | Bot name, descriptions, photo, menu button and default administrator rights. |
| [`update_telegram_bot_profile`](https://docs.upload-post.com/api/telegram-bot-profile) | `PATCH /api/uploadposts/telegram/bot-profile` | Change the bot profile (`photo`/`animation` as file or URL, `menu_button`, `default_administrator_rights`...). |
| [`get_telegram_bot_commands`](https://docs.upload-post.com/api/telegram-bot-profile) | `GET /api/uploadposts/telegram/bot-commands` | Bot commands for a scope and language. |
| [`set_telegram_bot_commands`](https://docs.upload-post.com/api/telegram-bot-profile) | `POST /api/uploadposts/telegram/bot-commands` | Set the bot commands (`commands`, `scope`, `language_code`). |
| [`delete_telegram_bot_commands`](https://docs.upload-post.com/api/telegram-bot-profile) | `DELETE /api/uploadposts/telegram/bot-commands` | Delete the bot commands of a scope and language. |
| [`get_telegram_sticker_set`](https://docs.upload-post.com/api/telegram-stickers) | `GET /api/uploadposts/telegram/sticker-sets` | Read a sticker set (`name`) or custom emoji stickers. |
| [`create_telegram_sticker_set`](https://docs.upload-post.com/api/telegram-stickers) | `POST /api/uploadposts/telegram/sticker-sets` | Create a sticker set. |
| [`edit_telegram_sticker_set`](https://docs.upload-post.com/api/telegram-stickers) | `PATCH /api/uploadposts/telegram/sticker-sets` | Edit a sticker set (add, replace, reorder stickers, title, thumbnail, emoji, keywords...). |
| [`delete_telegram_sticker_set`](https://docs.upload-post.com/api/telegram-stickers) | `DELETE /api/uploadposts/telegram/sticker-sets` | Delete a sticker set, or a sticker from it. |
| [`upload_telegram_sticker_file`](https://docs.upload-post.com/api/telegram-stickers) | `POST /api/uploadposts/telegram/sticker-sets/upload` | Upload a sticker file (`sticker` file or `sticker_url`, `sticker_format`, `owner_user_id`); returns its `file_id`. |

### Telegram: Stars, invoices and gifts

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_telegram_stars`](https://docs.upload-post.com/api/telegram-chat-insights) | `GET /api/uploadposts/telegram/stars` | The bot's Telegram Stars balance. |
| [`get_telegram_star_transactions`](https://docs.upload-post.com/api/telegram-chat-insights) | `GET /api/uploadposts/telegram/stars/transactions` | The bot's Telegram Stars transactions (`offset`, `limit`). |
| [`send_telegram_invoice`](https://docs.upload-post.com/api/telegram-payments) | `POST /api/uploadposts/telegram/invoices` | Send an invoice to the connected chat or to `chat_id` (payments go to your bot). |
| [`create_telegram_invoice_link`](https://docs.upload-post.com/api/telegram-payments) | `POST /api/uploadposts/telegram/invoice-links` | Create an invoice link. |
| [`refund_telegram_star_payment`](https://docs.upload-post.com/api/telegram-payments) | `POST /api/uploadposts/telegram/stars/refund` | Refund a Telegram Stars payment (`user_id`, `telegram_payment_charge_id`). |
| [`edit_telegram_star_subscription`](https://docs.upload-post.com/api/telegram-payments) | `POST /api/uploadposts/telegram/stars/subscription` | Cancel or re-enable a user's Stars subscription. |
| [`get_telegram_available_gifts`](https://docs.upload-post.com/api/telegram-payments) | `GET /api/uploadposts/telegram/gifts` | Gifts the bot can send. |
| [`get_telegram_owned_gifts`](https://docs.upload-post.com/api/telegram-payments) | `GET /api/uploadposts/telegram/gifts/owned` | Gifts owned by a user or a chat. |
| [`get_telegram_unique_gift`](https://docs.upload-post.com/api/telegram-payments) | `GET /api/uploadposts/telegram/gifts/unique` | A unique gift by name. |
| [`get_telegram_unanswered_payments`](https://docs.upload-post.com/api/telegram-payments) | `GET /api/uploadposts/telegram/payments/unanswered` | Payment queries that were not answered in time. |

### Bluesky: reads

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_post_engagement`](https://docs.upload-post.com/api/bluesky-reads) | `GET /api/uploadposts/post-engagement` | Who liked, reposted or quoted a post (`type`: likes, reposts, quotes; `limit`, `cursor`). |
| [`get_bluesky_profiles`](https://docs.upload-post.com/api/bluesky-reads) | `GET /api/uploadposts/bluesky/profile` | One or several Bluesky profiles (`actor`: handles or DIDs, comma separated, up to 25; without it, the connected account). |
| [`search_bluesky_posts`](https://docs.upload-post.com/api/bluesky-reads) | `GET /api/uploadposts/bluesky/search/posts` | Search Bluesky posts (`sort`, `since`, `until`, `author`, `lang`, `tag`, `limit`, `cursor`...). |
| [`search_bluesky_actors`](https://docs.upload-post.com/api/bluesky-reads) | `GET /api/uploadposts/bluesky/search/actors` | Search Bluesky accounts. |
| [`get_bluesky_followers`](https://docs.upload-post.com/api/bluesky-reads) | `GET /api/uploadposts/bluesky/followers` | Followers of an account (`actor`, or the connected one with `user`; `known=true` for followers you follow). |
| [`get_bluesky_follows`](https://docs.upload-post.com/api/bluesky-reads) | `GET /api/uploadposts/bluesky/follows` | Accounts an account follows. |
| [`bluesky_xrpc`](https://docs.upload-post.com/api/bluesky-reads) | `GET /api/uploadposts/bluesky/xrpc/{nsid}` | Read-only gateway to an allow-listed public Bluesky XRPC method (e.g. `app.bsky.feed.getAuthorFeed`); returns Bluesky's answer untouched. |
| [`get_bluesky_labels`](https://docs.upload-post.com/api/bluesky-reads) | `GET /api/uploadposts/bluesky/labels` | Moderation labels on the account and its posts. |

### Bluesky: notifications

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_bluesky_notifications`](https://docs.upload-post.com/api/bluesky-notifications) | `GET /api/uploadposts/bluesky/notifications` | List notifications (`reasons`, `priority`, `limit`, `cursor`). |
| [`get_bluesky_unread_count`](https://docs.upload-post.com/api/bluesky-notifications) | `GET /api/uploadposts/bluesky/notifications/unread-count` | Unread notification count. |
| [`mark_bluesky_notifications_seen`](https://docs.upload-post.com/api/bluesky-notifications) | `POST /api/uploadposts/bluesky/notifications/seen` | Mark notifications as seen (up to `seen_at`). |
| [`get_bluesky_notification_preferences`](https://docs.upload-post.com/api/bluesky-notifications) | `GET /api/uploadposts/bluesky/notification-preferences` | Notification preferences. |
| [`update_bluesky_notification_preferences`](https://docs.upload-post.com/api/bluesky-notifications) | `POST /api/uploadposts/bluesky/notification-preferences` | Update notification preferences. |
| [`get_bluesky_activity_subscriptions`](https://docs.upload-post.com/api/bluesky-notifications) | `GET /api/uploadposts/bluesky/activity-subscriptions` | Accounts whose activity you are subscribed to. |
| [`set_bluesky_activity_subscription`](https://docs.upload-post.com/api/bluesky-notifications) | `POST /api/uploadposts/bluesky/activity-subscriptions` | Subscribe to (or stop) an account's posts and replies. |

### Bluesky: profile, settings and drafts

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_bluesky_own_profile`](https://docs.upload-post.com/api/bluesky-profile) | `GET /api/uploadposts/bluesky/profile/self` | The connected account's profile record. |
| [`update_bluesky_profile`](https://docs.upload-post.com/api/bluesky-profile) | `POST /api/uploadposts/bluesky/profile/self` | Update the profile (display name, description, `avatar`/`banner` files, links, pinned post...). Fields not sent stay as they are. |
| [`get_bluesky_status`](https://docs.upload-post.com/api/bluesky-profile) | `GET /api/uploadposts/bluesky/status` | Read the live status. |
| [`set_bluesky_status`](https://docs.upload-post.com/api/bluesky-profile) | `POST /api/uploadposts/bluesky/status` | Set the live status. |
| [`clear_bluesky_status`](https://docs.upload-post.com/api/bluesky-profile) | `DELETE /api/uploadposts/bluesky/status` | Clear the live status. |
| [`get_bluesky_settings`](https://docs.upload-post.com/api/bluesky-profile) | `GET /api/uploadposts/bluesky/settings` | Chat and discovery settings. |
| [`update_bluesky_settings`](https://docs.upload-post.com/api/bluesky-profile) | `POST /api/uploadposts/bluesky/settings` | Change chat and discovery settings. |
| [`get_bluesky_preferences`](https://docs.upload-post.com/api/bluesky-profile) | `GET /api/uploadposts/bluesky/preferences` | App preferences (content filters, feeds, muted words...). |
| [`update_bluesky_preferences`](https://docs.upload-post.com/api/bluesky-profile) | `PUT /api/uploadposts/bluesky/preferences` | Replace some app preferences. |
| [`list_bluesky_drafts`](https://docs.upload-post.com/api/bluesky-drafts) | `GET /api/uploadposts/bluesky/drafts` | List drafts. |
| [`create_bluesky_draft`](https://docs.upload-post.com/api/bluesky-drafts) | `POST /api/uploadposts/bluesky/drafts` | Create a draft. |
| [`update_bluesky_draft`](https://docs.upload-post.com/api/bluesky-drafts) | `PATCH /api/uploadposts/bluesky/drafts/{draft_id}` | Replace a draft. |
| [`delete_bluesky_draft`](https://docs.upload-post.com/api/bluesky-drafts) | `DELETE /api/uploadposts/bluesky/drafts/{draft_id}` | Delete a draft. |

### Bluesky: chat

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_bluesky_chat_status`](https://docs.upload-post.com/api/bluesky-chat) | `GET /api/uploadposts/dms/bluesky/status` | Chat status of the account. |
| [`get_bluesky_chat_preferences`](https://docs.upload-post.com/api/bluesky-chat) | `GET /api/uploadposts/dms/bluesky/preferences` | DM notification settings. |
| [`update_bluesky_chat_preferences`](https://docs.upload-post.com/api/bluesky-chat) | `POST /api/uploadposts/dms/bluesky/preferences` | Change DM notification settings. |
| [`export_bluesky_chat`](https://docs.upload-post.com/api/bluesky-chat) | `GET /api/uploadposts/dms/bluesky/export` | Export the account's chat history. |

### Google Business: posts and reviews

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`list_google_business_posts`](https://docs.upload-post.com/api/google-business-posts) | `GET /api/uploadposts/google-business/posts` | List the location's posts (`location_id`, `page_size`, `page_token`). Edit them with editPost and delete them with unpublishPost. |
| [`get_google_business_post`](https://docs.upload-post.com/api/google-business-posts) | `GET /api/uploadposts/google-business/posts/get` | Read one post (`post_id` or `post_name`). |
| [`list_google_business_reviews`](https://docs.upload-post.com/api/google-business-reviews) | `GET /api/uploadposts/google-business/reviews` | List reviews (`location_id`, `page_size`, `page_token`, `order_by`). |
| [`get_google_business_review`](https://docs.upload-post.com/api/google-business-reviews) | `GET /api/uploadposts/google-business/reviews/get` | Read one review (`review_name`, or `review_id` + `location_id`). |
| [`batch_get_google_business_reviews`](https://docs.upload-post.com/api/google-business-reviews) | `GET /api/uploadposts/google-business/reviews/batch` | Reviews of several locations at once (`location_ids`). |
| [`reply_to_google_business_review`](https://docs.upload-post.com/api/google-business-reviews) | `PUT /api/uploadposts/google-business/reviews/reply` | Reply to a review, or replace the reply (`review_name`, or `review_id` + `location_id`). |
| [`delete_google_business_review_reply`](https://docs.upload-post.com/api/google-business-reviews) | `DELETE /api/uploadposts/google-business/reviews/reply` | Delete the reply to a review. |

### Google Business: gallery and performance

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`list_google_business_media`](https://docs.upload-post.com/api/google-business-media) | `GET /api/uploadposts/google-business/media` | List the location's gallery. |
| [`get_google_business_media`](https://docs.upload-post.com/api/google-business-media) | `GET /api/uploadposts/google-business/media/get` | Read one gallery item. |
| [`upload_google_business_media`](https://docs.upload-post.com/api/google-business-media) | `POST /api/uploadposts/google-business/media` | Upload a photo or video to the gallery: `file` (local path, stream or Buffer) or `source_url`, plus `category`, `description`, `media_format`. |
| [`update_google_business_media`](https://docs.upload-post.com/api/google-business-media) | `PATCH /api/uploadposts/google-business/media` | Change a gallery item's category. |
| [`delete_google_business_media`](https://docs.upload-post.com/api/google-business-media) | `DELETE /api/uploadposts/google-business/media` | Delete a gallery item. |
| [`list_google_business_customer_media`](https://docs.upload-post.com/api/google-business-media) | `GET /api/uploadposts/google-business/media/customers` | Photos uploaded by customers. |
| [`get_google_business_customer_media`](https://docs.upload-post.com/api/google-business-media) | `GET /api/uploadposts/google-business/media/customers/get` | One customer photo. |
| [`get_google_business_performance`](https://docs.upload-post.com/api/google-business-performance) | `GET /api/uploadposts/google-business/performance` | Daily metrics for any date range (impressions, calls, website clicks, directions...: `metrics`, `start_date`, `end_date`). |
| [`get_google_business_search_keywords`](https://docs.upload-post.com/api/google-business-performance) | `GET /api/uploadposts/google-business/performance/keywords` | Monthly search keywords that showed the location (`start_month`, `end_month`). |

### Google Business: location info

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_google_business_location_info`](https://docs.upload-post.com/api/google-business-info) | `GET /api/uploadposts/google-business/location-info` | Read the location's info (name, address, hours, phones, categories, service area, open status...). |
| [`update_google_business_location_info`](https://docs.upload-post.com/api/google-business-info) | `PATCH /api/uploadposts/google-business/location-info` | Edit the location's info. `edit_mode: "legacy"` (default) or `"strict"` (`dry_run`, `confirm`, `include_edit_status`); `validate_only` in both. |
| [`get_google_business_google_updates`](https://docs.upload-post.com/api/google-business-info) | `GET /api/uploadposts/google-business/location-info/google-updated` | Changes Google suggested for the location (`diff_fields`). |
| [`answer_google_business_google_updates`](https://docs.upload-post.com/api/google-business-info) | `POST /api/uploadposts/google-business/location-info/google-updates` | Accept or reject Google's suggested changes, field by field. |
| [`get_google_business_location_info_extended`](https://docs.upload-post.com/api/google-business-info) | `GET /api/uploadposts/google-business/location-info/extended` | Edit status of each field (experimental). |
| [`list_google_business_locations`](https://docs.upload-post.com/api/google-business-info) | `GET /api/uploadposts/google-business/locations/list` | List locations with filters (`account`, `filter`, `order_by`, `read_mask`, `page_size`, `page_token`). |
| [`get_google_business_pinned_location`](https://docs.upload-post.com/api/google-business-location) | `GET /api/uploadposts/users/google-business-location` | Locations available to a profile and the one pinned for its uploads. |
| [`pin_google_business_location`](https://docs.upload-post.com/api/google-business-location) | `POST /api/uploadposts/users/google-business-location` | Pin the location a profile publishes to (instead of passing gbpLocationId on every upload). |
| [`clear_google_business_location_pin`](https://docs.upload-post.com/api/google-business-location) | `DELETE /api/uploadposts/users/google-business-location` | Clear the pinned location. |

### Google Business: catalogs, attributes, Place Actions, menus, services and lodging

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`search_google_business_categories`](https://docs.upload-post.com/api/google-business-catalogs) | `GET /api/uploadposts/google-business/categories` | Search categories (`region_code`, `language_code`, `query`). |
| [`batch_get_google_business_categories`](https://docs.upload-post.com/api/google-business-catalogs) | `GET /api/uploadposts/google-business/categories/batch` | Category details: service types and more-hours types (`names`). |
| [`search_google_business_chains`](https://docs.upload-post.com/api/google-business-catalogs) | `GET /api/uploadposts/google-business/chains` | Search chains (`name`). |
| [`get_google_business_chain`](https://docs.upload-post.com/api/google-business-catalogs) | `GET /api/uploadposts/google-business/chains/get` | One chain (`chain`). |
| [`search_google_business_google_locations`](https://docs.upload-post.com/api/google-business-catalogs) | `POST /api/uploadposts/google-business/google-locations/search` | Is the business already on Google? Search Google's listings. |
| [`get_google_business_recommended_locations`](https://docs.upload-post.com/api/google-business-catalogs) | `GET /api/uploadposts/google-business/google-locations/recommended` | Locations Google recommends for the account. |
| [`report_google_business_google_location`](https://docs.upload-post.com/api/google-business-catalogs) | `POST /api/uploadposts/google-business/google-locations/report` | Report a wrong listing to Google. |
| [`get_google_business_available_attributes`](https://docs.upload-post.com/api/google-business-attributes) | `GET /api/uploadposts/google-business/attributes/available` | Attributes the location can use. |
| [`get_google_business_attributes`](https://docs.upload-post.com/api/google-business-attributes) | `GET /api/uploadposts/google-business/attributes` | Current attributes of the location. |
| [`update_google_business_attributes`](https://docs.upload-post.com/api/google-business-attributes) | `PATCH /api/uploadposts/google-business/attributes` | Update attributes. |
| [`get_google_business_attributes_google_updated`](https://docs.upload-post.com/api/google-business-attributes) | `GET /api/uploadposts/google-business/attributes/google-updated` | Attributes as Google shows them. |
| [`get_google_business_attributes_extended`](https://docs.upload-post.com/api/google-business-attributes) | `GET /api/uploadposts/google-business/attributes/extended` | Attributes with their edit status (experimental). |
| [`get_google_business_place_action_types`](https://docs.upload-post.com/api/google-business-place-actions) | `GET /api/uploadposts/google-business/place-actions/types` | Place Action types (booking, ordering, shopping links...) the location can use. |
| [`list_google_business_place_actions`](https://docs.upload-post.com/api/google-business-place-actions) | `GET /api/uploadposts/google-business/place-actions` | List Place Action links. |
| [`get_google_business_place_action`](https://docs.upload-post.com/api/google-business-place-actions) | `GET /api/uploadposts/google-business/place-actions/get` | Read one Place Action link (`link`). |
| [`create_google_business_place_action`](https://docs.upload-post.com/api/google-business-place-actions) | `POST /api/uploadposts/google-business/place-actions` | Create a Place Action link. |
| [`update_google_business_place_action`](https://docs.upload-post.com/api/google-business-place-actions) | `PATCH /api/uploadposts/google-business/place-actions` | Edit or switch off a Place Action link. |
| [`delete_google_business_place_action`](https://docs.upload-post.com/api/google-business-place-actions) | `DELETE /api/uploadposts/google-business/place-actions` | Delete a Place Action link. |
| [`get_google_business_food_menus`](https://docs.upload-post.com/api/google-business-menus-services) | `GET /api/uploadposts/google-business/food-menus` | Food menus of the location. |
| [`update_google_business_food_menus`](https://docs.upload-post.com/api/google-business-menus-services) | `PUT /api/uploadposts/google-business/food-menus` | Replace the food menus. |
| [`get_google_business_services`](https://docs.upload-post.com/api/google-business-menus-services) | `GET /api/uploadposts/google-business/services` | Services of the location. |
| [`update_google_business_services`](https://docs.upload-post.com/api/google-business-menus-services) | `PUT /api/uploadposts/google-business/services` | Replace the services. |
| [`get_google_business_lodging`](https://docs.upload-post.com/api/google-business-lodging) | `GET /api/uploadposts/google-business/lodging` | Lodging data of a hotel (`read_mask`). |
| [`update_google_business_lodging`](https://docs.upload-post.com/api/google-business-lodging) | `PATCH /api/uploadposts/google-business/lodging` | Update lodging data. |
| [`get_google_business_lodging_google_updated`](https://docs.upload-post.com/api/google-business-lodging) | `GET /api/uploadposts/google-business/lodging/google-updated` | Lodging data as Google shows it. |

### Google Business: accounts and verification (reads)

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`list_google_business_accounts`](https://docs.upload-post.com/api/google-business-accounts) | `GET /api/uploadposts/google-business/accounts` | Google Business accounts and location groups (`type`). |
| [`get_google_business_account`](https://docs.upload-post.com/api/google-business-accounts) | `GET /api/uploadposts/google-business/accounts/get` | Read one account (`account`). |
| [`create_google_business_account`](https://docs.upload-post.com/api/google-business-accounts) | `POST /api/uploadposts/google-business/accounts` | Create a location group or user group (`type`, `account_name`, `confirm`). |
| [`list_google_business_admins`](https://docs.upload-post.com/api/google-business-accounts) | `GET /api/uploadposts/google-business/admins` | Admins of an account or a location (`scope`, `location_id`). |
| [`list_google_business_invitations`](https://docs.upload-post.com/api/google-business-accounts) | `GET /api/uploadposts/google-business/invitations` | Pending invitations of an account. |
| [`get_google_business_verification_state`](https://docs.upload-post.com/api/google-business-verification) | `GET /api/uploadposts/google-business/verification/state` | Whether the location is verified and in good standing. |
| [`get_google_business_verification_options`](https://docs.upload-post.com/api/google-business-verification) | `POST /api/uploadposts/google-business/verification/options` | Verification methods available for the location. |
| [`list_google_business_verifications`](https://docs.upload-post.com/api/google-business-verification) | `GET /api/uploadposts/google-business/verifications` | Past verifications of the location. |

## AutoDM monitors (one post)

A monitor answers every new comment on one post: a private DM on Instagram, a
public reply on TikTok, YouTube, Facebook, Threads and Bluesky. Monitors stop
after 15 days and a profile can create 2 per day (account-wide Instagram rules
are below, in AutoDM rules).

```python
monitor = client.start_autodm("my-profile", "Thanks! Check your DMs",
                              post_url="https://www.instagram.com/p/XXXX/", trigger_keywords=["info"])
client.get_autodm_status(include_inactive=True)
client.get_autodm_logs(monitor["monitor_id"])
client.pause_autodm(monitor["monitor_id"])   # also resume_autodm, stop_autodm, delete_autodm
```

## YouTube management

Video details and your daily allowance, thumbnails, playlists, captions, the
comments inbox, search and catalogs, subscriptions, ratings and reports, channel
settings, live broadcasts and streams, and the live chat. Same rules as above
(required arguments positional, every other keyword sent, files go multipart).
Destructive or hard-to-undo calls need `confirm=True`, which the SDK never adds
for you (`400 confirmation_required` otherwise). These calls share a daily
allowance per account, in YouTube quota units: check it with `get_youtube_quota()`.

```python
videos = client.get_youtube_videos("my-profile", ids="dQw4w9WgXcQ")
client.upload_youtube_caption("my-profile", "dQw4w9WgXcQ", language="es", file="es.srt")
srt = client.download_youtube_caption("my-profile", "AUieDa...", tfmt="srt")   # text
client.moderate_youtube_comments("my-profile", ["Ugz..."], "rejected", confirm=True)
live = client.create_youtube_broadcast("my-profile", title="Live Q&A", scheduled_start_time="2026-12-01T18:00:00Z")
client.transition_youtube_broadcast("my-profile", live["broadcast"]["id"], "live", confirm=True)
```

Editing a published video goes through `edit_post(user, "youtube", video_id, ...)`
with YouTube's own names (`privacyStatus`, `categoryId`, `publishAt`,
`hasPaidProductPlacement`...), plus `localizations`, `localizations_remove` and
`brand_partner`.

### YouTube: videos, thumbnail and quota

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_youtube_videos`](https://docs.upload-post.com/api/youtube-videos) | `GET /api/uploadposts/youtube/videos` | Full details of videos: status, processing, statistics, translations, paid placement... (`ids`, `chart` or `my_rating`; `parts`, `include_owner_details`). |
| [`get_youtube_quota`](https://docs.upload-post.com/api/youtube-videos) | `GET /api/uploadposts/youtube/quota` | Your account's daily allowance for the YouTube management endpoints and what is left. |
| [`set_youtube_thumbnail`](https://docs.upload-post.com/api/youtube-thumbnail) | `POST /api/uploadposts/youtube/thumbnail` | Set a video's thumbnail: `thumbnail` (local file, stream or Buffer) or `thumbnail_url`. |

### YouTube: playlists

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`list_youtube_playlists`](https://docs.upload-post.com/api/youtube-playlists) | `GET /api/uploadposts/youtube/playlists` | List the channel's playlists (or `ids`). |
| [`create_youtube_playlist`](https://docs.upload-post.com/api/youtube-playlists) | `POST /api/uploadposts/youtube/playlists` | Create a playlist (`title`, `description`, `privacy_status`, `default_language`, `localizations`...). |
| [`update_youtube_playlist`](https://docs.upload-post.com/api/youtube-playlists) | `PATCH /api/uploadposts/youtube/playlists/{playlist_id}` | Edit a playlist (only what you send changes). |
| [`delete_youtube_playlist`](https://docs.upload-post.com/api/youtube-playlists) | `DELETE /api/uploadposts/youtube/playlists/{playlist_id}` | Delete a playlist (needs `confirm: true`; the videos stay). |
| [`list_youtube_playlist_items`](https://docs.upload-post.com/api/youtube-playlists) | `GET /api/uploadposts/youtube/playlists/{playlist_id}/items` | Videos of a playlist. |
| [`add_youtube_playlist_item`](https://docs.upload-post.com/api/youtube-playlists) | `POST /api/uploadposts/youtube/playlists/{playlist_id}/items` | Add a video to a playlist (`video_id`, `position`, `note`). |
| [`update_youtube_playlist_item`](https://docs.upload-post.com/api/youtube-playlists) | `PATCH /api/uploadposts/youtube/playlists/{playlist_id}/items/{item_id}` | Reorder a playlist video or change its note. |
| [`delete_youtube_playlist_item`](https://docs.upload-post.com/api/youtube-playlists) | `DELETE /api/uploadposts/youtube/playlists/{playlist_id}/items/{item_id}` | Remove a video from a playlist (needs `confirm: true`). |
| [`get_youtube_playlist_image`](https://docs.upload-post.com/api/youtube-playlists) | `GET /api/uploadposts/youtube/playlists/{playlist_id}/image` | The playlist's custom image. |
| [`set_youtube_playlist_image`](https://docs.upload-post.com/api/youtube-playlists) | `POST /api/uploadposts/youtube/playlists/{playlist_id}/image` | Add the playlist image: `image` (local file, stream or Buffer) or `image_url`. |
| [`replace_youtube_playlist_image`](https://docs.upload-post.com/api/youtube-playlists) | `PUT /api/uploadposts/youtube/playlists/{playlist_id}/image` | Replace the playlist image (same fields, needs `confirm: true`). |
| [`delete_youtube_playlist_image`](https://docs.upload-post.com/api/youtube-playlists) | `DELETE /api/uploadposts/youtube/playlists/{playlist_id}/image` | Remove the playlist image (needs `confirm: true`). |

### YouTube: captions

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`list_youtube_captions`](https://docs.upload-post.com/api/youtube-captions) | `GET /api/uploadposts/youtube/captions` | Caption tracks of a video. |
| [`upload_youtube_caption`](https://docs.upload-post.com/api/youtube-captions) | `POST /api/uploadposts/youtube/captions` | Add a caption track: `file` (local file, stream or Buffer) or `file_url`, plus `language`, `name`, `is_draft`. |
| [`update_youtube_caption`](https://docs.upload-post.com/api/youtube-captions) | `PUT /api/uploadposts/youtube/captions/{caption_id}` | Replace a track's file and/or publish a draft (`is_draft: false`). |
| [`download_youtube_caption`](https://docs.upload-post.com/api/youtube-captions) | `GET /api/uploadposts/youtube/captions/{caption_id}/download` | Download a track (`tfmt`: srt, vtt, sbv, scc, ttml; `tlang` to translate). Returns the file's text. |
| [`delete_youtube_caption`](https://docs.upload-post.com/api/youtube-captions) | `DELETE /api/uploadposts/youtube/captions/{caption_id}` | Delete a track (needs `confirm: true`). |

### YouTube: comments inbox

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`list_youtube_comments`](https://docs.upload-post.com/api/youtube-comments) | `GET /api/uploadposts/youtube/comments` | Comment threads of a video (`video_id`), of the whole channel (`scope: "channel"`) or by `ids`; `moderation_status`, `order`, `search_terms`... |
| [`list_youtube_comment_replies`](https://docs.upload-post.com/api/youtube-comments) | `GET /api/uploadposts/youtube/comments/replies` | Replies to a comment (`parent_id`) or comments by `ids`. |
| [`create_youtube_comment`](https://docs.upload-post.com/api/youtube-comments) | `POST /api/uploadposts/youtube/comments` | Reply to a comment (`parent_id`) or comment on a video (`video_id`); `idempotency_key` optional. |
| [`update_youtube_comment`](https://docs.upload-post.com/api/youtube-comments) | `PATCH /api/uploadposts/youtube/comments/{comment_id}` | Edit your own comment (`text`). |
| [`delete_youtube_comment`](https://docs.upload-post.com/api/youtube-comments) | `DELETE /api/uploadposts/youtube/comments/{comment_id}` | Delete your own comment (needs `confirm: true`). |
| [`moderate_youtube_comments`](https://docs.upload-post.com/api/youtube-comments) | `POST /api/uploadposts/youtube/comments/moderate` | Approve, hold or reject comments of your channel (`rejected` needs `confirm: true`; `ban_author`). |

### YouTube: search and catalogs

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`search_youtube`](https://docs.upload-post.com/api/youtube-search-catalogs) | `GET /api/uploadposts/youtube/search` | Search videos, channels and playlists (`q`, `for_mine`, `channel_id`, `type`, `order`...). |
| [`get_youtube_categories`](https://docs.upload-post.com/api/youtube-search-catalogs) | `GET /api/uploadposts/youtube/categories` | Video categories of a region (`region`, `hl`, `assignable_only`). |
| [`get_youtube_languages`](https://docs.upload-post.com/api/youtube-search-catalogs) | `GET /api/uploadposts/youtube/languages` | Languages YouTube supports (`hl`). |
| [`get_youtube_regions`](https://docs.upload-post.com/api/youtube-search-catalogs) | `GET /api/uploadposts/youtube/regions` | Regions (countries) YouTube supports (`hl`). |
| [`get_youtube_abuse_reasons`](https://docs.upload-post.com/api/youtube-search-catalogs) | `GET /api/uploadposts/youtube/abuse-reasons` | Reasons for an abuse report (`hl`). |

### YouTube: subscriptions, ratings, reports and activity

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`list_youtube_subscriptions`](https://docs.upload-post.com/api/youtube-channel-actions) | `GET /api/uploadposts/youtube/subscriptions` | Channels the connected channel subscribes to (or its subscribers). |
| [`subscribe_youtube_channel`](https://docs.upload-post.com/api/youtube-channel-actions) | `POST /api/uploadposts/youtube/subscriptions` | Subscribe the connected channel to a channel (`channel_id`). |
| [`unsubscribe_youtube_channel`](https://docs.upload-post.com/api/youtube-channel-actions) | `DELETE /api/uploadposts/youtube/subscriptions/{subscription_id}` | Unsubscribe. |
| [`rate_youtube_video`](https://docs.upload-post.com/api/youtube-channel-actions) | `POST /api/uploadposts/youtube/videos/{video_id}/rate` | Like, dislike or remove the rating of a video (`rating`: like, dislike, none). |
| [`get_youtube_rating`](https://docs.upload-post.com/api/youtube-channel-actions) | `GET /api/uploadposts/youtube/videos/rating` | The channel's rating of up to 50 videos. |
| [`report_youtube_video_abuse`](https://docs.upload-post.com/api/youtube-channel-actions) | `POST /api/uploadposts/youtube/videos/{video_id}/report-abuse` | Report a video (needs `confirm: true`; it cannot be withdrawn). |
| [`get_youtube_activities`](https://docs.upload-post.com/api/youtube-channel-actions) | `GET /api/uploadposts/youtube/activities` | Activity of the channel (uploads, likes, playlist additions...). |

### YouTube: channel settings

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_youtube_channel`](https://docs.upload-post.com/api/youtube-channel) | `GET /api/uploadposts/youtube/channel` | Read the connected channel (settings, branding, translations, statistics). |
| [`update_youtube_channel`](https://docs.upload-post.com/api/youtube-channel) | `PATCH /api/uploadposts/youtube/channel` | Change the channel settings or translations (only what you send changes). |
| [`lookup_youtube_channel`](https://docs.upload-post.com/api/youtube-channel) | `GET /api/uploadposts/youtube/channel/lookup` | Public data of any channel (`for_handle`, `channel_id`...). |
| [`set_youtube_channel_banner`](https://docs.upload-post.com/api/youtube-channel) | `POST /api/uploadposts/youtube/channel/banner` | Upload and apply the banner: `image` (local file, stream or Buffer) or `image_url`. |
| [`list_youtube_channel_sections`](https://docs.upload-post.com/api/youtube-channel) | `GET /api/uploadposts/youtube/channel/sections` | Sections of the channel page. |
| [`create_youtube_channel_section`](https://docs.upload-post.com/api/youtube-channel) | `POST /api/uploadposts/youtube/channel/sections` | Create a section. |
| [`update_youtube_channel_section`](https://docs.upload-post.com/api/youtube-channel) | `PATCH /api/uploadposts/youtube/channel/sections/{section_id}` | Edit or move a section. |
| [`delete_youtube_channel_section`](https://docs.upload-post.com/api/youtube-channel) | `DELETE /api/uploadposts/youtube/channel/sections/{section_id}` | Delete a section (needs `confirm: true`). |
| [`set_youtube_watermark`](https://docs.upload-post.com/api/youtube-channel) | `POST /api/uploadposts/youtube/channel/watermark` | Set the watermark: `image` (local file, stream or Buffer) or `image_url`, `timing_type`, `offset_ms`, `duration_ms` (needs `confirm: true`). |
| [`remove_youtube_watermark`](https://docs.upload-post.com/api/youtube-channel) | `DELETE /api/uploadposts/youtube/channel/watermark` | Remove the watermark (needs `confirm: true`). |

### YouTube: live broadcasts and streams

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`list_youtube_broadcasts`](https://docs.upload-post.com/api/youtube-live) | `GET /api/uploadposts/youtube/live/broadcasts` | List live broadcasts (`status`, `ids`...). |
| [`create_youtube_broadcast`](https://docs.upload-post.com/api/youtube-live) | `POST /api/uploadposts/youtube/live/broadcasts` | Create a broadcast (`title`, `scheduled_start_time`, `privacy_status`...). |
| [`get_youtube_broadcast`](https://docs.upload-post.com/api/youtube-live) | `GET /api/uploadposts/youtube/live/broadcasts/{broadcast_id}` | One broadcast. |
| [`update_youtube_broadcast`](https://docs.upload-post.com/api/youtube-live) | `PATCH /api/uploadposts/youtube/live/broadcasts/{broadcast_id}` | Edit a broadcast. |
| [`delete_youtube_broadcast`](https://docs.upload-post.com/api/youtube-live) | `DELETE /api/uploadposts/youtube/live/broadcasts/{broadcast_id}` | Delete a broadcast (needs `confirm: true`). |
| [`bind_youtube_broadcast`](https://docs.upload-post.com/api/youtube-live) | `POST /api/uploadposts/youtube/live/broadcasts/{broadcast_id}/bind` | Bind a stream to the broadcast (`stream_id`), or unbind it. |
| [`transition_youtube_broadcast`](https://docs.upload-post.com/api/youtube-live) | `POST /api/uploadposts/youtube/live/broadcasts/{broadcast_id}/transition` | Go `testing`, `live` or `complete` (`live` and `complete` need `confirm: true`). |
| [`insert_youtube_cuepoint`](https://docs.upload-post.com/api/youtube-live) | `POST /api/uploadposts/youtube/live/broadcasts/{broadcast_id}/cuepoint` | Insert an ad break. |
| [`list_youtube_streams`](https://docs.upload-post.com/api/youtube-live) | `GET /api/uploadposts/youtube/live/streams` | List streams. |
| [`create_youtube_stream`](https://docs.upload-post.com/api/youtube-live) | `POST /api/uploadposts/youtube/live/streams` | Create a stream (its key is a secret). |
| [`get_youtube_stream`](https://docs.upload-post.com/api/youtube-live) | `GET /api/uploadposts/youtube/live/streams/{stream_id}` | One stream. |
| [`update_youtube_stream`](https://docs.upload-post.com/api/youtube-live) | `PATCH /api/uploadposts/youtube/live/streams/{stream_id}` | Edit a stream. |
| [`delete_youtube_stream`](https://docs.upload-post.com/api/youtube-live) | `DELETE /api/uploadposts/youtube/live/streams/{stream_id}` | Delete a stream (needs `confirm: true`; encoders using its key stop). |

### YouTube: live chat, polls and moderation

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| [`get_youtube_live_chat`](https://docs.upload-post.com/api/youtube-live-chat) | `GET /api/uploadposts/youtube/live/chat` | Read the live chat (`broadcast_id` or `live_chat_id`, `page_token`). |
| [`send_youtube_live_chat_message`](https://docs.upload-post.com/api/youtube-live-chat) | `POST /api/uploadposts/youtube/live/chat` | Post a message or a poll in the live chat (`idempotency_key` optional). |
| [`close_youtube_live_chat_poll`](https://docs.upload-post.com/api/youtube-live-chat) | `POST /api/uploadposts/youtube/live/chat/polls/{message_id}/close` | Close a poll. |
| [`delete_youtube_live_chat_message`](https://docs.upload-post.com/api/youtube-live-chat) | `DELETE /api/uploadposts/youtube/live/chat/messages/{message_id}` | Delete a chat message (needs `confirm: true`). |
| [`list_youtube_live_moderators`](https://docs.upload-post.com/api/youtube-live-chat) | `GET /api/uploadposts/youtube/live/moderators` | Moderators of the live chat. |
| [`add_youtube_live_moderator`](https://docs.upload-post.com/api/youtube-live-chat) | `POST /api/uploadposts/youtube/live/moderators` | Add a moderator (`channel_id`). |
| [`remove_youtube_live_moderator`](https://docs.upload-post.com/api/youtube-live-chat) | `DELETE /api/uploadposts/youtube/live/moderators/{moderator_id}` | Remove a moderator (the `id` from the list; needs `confirm: true`). |
| [`ban_youtube_live_chat_user`](https://docs.upload-post.com/api/youtube-live-chat) | `POST /api/uploadposts/youtube/live/bans` | Ban a user from the chat (`permanent` or `temporary` with `ban_duration_seconds`; needs `confirm: true`). |
| [`unban_youtube_live_chat_user`](https://docs.upload-post.com/api/youtube-live-chat) | `DELETE /api/uploadposts/youtube/live/bans/{ban_id}` | Lift a ban. |
| [`list_youtube_super_chats`](https://docs.upload-post.com/api/youtube-live-chat) | `GET /api/uploadposts/youtube/live/super-chats` | Super Chats and Super Stickers received. |

## Not generally available yet

<!-- openapi:availability -->
These hand-written methods call operations that are **not generally available yet**: they answer an error (usually HTTP 503) until the feature is switched on for your account. Generated from `codegen/openapi.json`.

| Method | Endpoint | Until it is switched on |
| :-- | :-- | :-- |
| `list_youtube_broadcasts` | `GET /api/uploadposts/youtube/live/broadcasts` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `create_youtube_broadcast` | `POST /api/uploadposts/youtube/live/broadcasts` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_broadcast` | `GET /api/uploadposts/youtube/live/broadcasts/{broadcast_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `update_youtube_broadcast` | `PATCH /api/uploadposts/youtube/live/broadcasts/{broadcast_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_broadcast` | `DELETE /api/uploadposts/youtube/live/broadcasts/{broadcast_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `bind_youtube_broadcast` | `POST /api/uploadposts/youtube/live/broadcasts/{broadcast_id}/bind` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `transition_youtube_broadcast` | `POST /api/uploadposts/youtube/live/broadcasts/{broadcast_id}/transition` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `insert_youtube_cuepoint` | `POST /api/uploadposts/youtube/live/broadcasts/{broadcast_id}/cuepoint` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_streams` | `GET /api/uploadposts/youtube/live/streams` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `create_youtube_stream` | `POST /api/uploadposts/youtube/live/streams` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_stream` | `GET /api/uploadposts/youtube/live/streams/{stream_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `update_youtube_stream` | `PATCH /api/uploadposts/youtube/live/streams/{stream_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_stream` | `DELETE /api/uploadposts/youtube/live/streams/{stream_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_live_chat` | `GET /api/uploadposts/youtube/live/chat` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `send_youtube_live_chat_message` | `POST /api/uploadposts/youtube/live/chat` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `close_youtube_live_chat_poll` | `POST /api/uploadposts/youtube/live/chat/polls/{message_id}/close` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_live_chat_message` | `DELETE /api/uploadposts/youtube/live/chat/messages/{message_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_live_moderators` | `GET /api/uploadposts/youtube/live/moderators` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `add_youtube_live_moderator` | `POST /api/uploadposts/youtube/live/moderators` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `remove_youtube_live_moderator` | `DELETE /api/uploadposts/youtube/live/moderators/{moderator_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `ban_youtube_live_chat_user` | `POST /api/uploadposts/youtube/live/bans` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `unban_youtube_live_chat_user` | `DELETE /api/uploadposts/youtube/live/bans/{ban_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_super_chats` | `GET /api/uploadposts/youtube/live/super-chats` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_comments` | `GET /api/uploadposts/youtube/comments` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `create_youtube_comment` | `POST /api/uploadposts/youtube/comments` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_comment_replies` | `GET /api/uploadposts/youtube/comments/replies` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `moderate_youtube_comments` | `POST /api/uploadposts/youtube/comments/moderate` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `update_youtube_comment` | `PATCH /api/uploadposts/youtube/comments/{comment_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_comment` | `DELETE /api/uploadposts/youtube/comments/{comment_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_categories` | `GET /api/uploadposts/youtube/categories` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_languages` | `GET /api/uploadposts/youtube/languages` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_regions` | `GET /api/uploadposts/youtube/regions` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_abuse_reasons` | `GET /api/uploadposts/youtube/abuse-reasons` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `search_youtube` | `GET /api/uploadposts/youtube/search` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_subscriptions` | `GET /api/uploadposts/youtube/subscriptions` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `subscribe_youtube_channel` | `POST /api/uploadposts/youtube/subscriptions` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `unsubscribe_youtube_channel` | `DELETE /api/uploadposts/youtube/subscriptions/{subscription_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_rating` | `GET /api/uploadposts/youtube/videos/rating` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `rate_youtube_video` | `POST /api/uploadposts/youtube/videos/{video_id}/rate` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `report_youtube_video_abuse` | `POST /api/uploadposts/youtube/videos/{video_id}/report-abuse` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_activities` | `GET /api/uploadposts/youtube/activities` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_channel` | `GET /api/uploadposts/youtube/channel` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `update_youtube_channel` | `PATCH /api/uploadposts/youtube/channel` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `lookup_youtube_channel` | `GET /api/uploadposts/youtube/channel/lookup` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `set_youtube_channel_banner` | `POST /api/uploadposts/youtube/channel/banner` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_channel_sections` | `GET /api/uploadposts/youtube/channel/sections` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `create_youtube_channel_section` | `POST /api/uploadposts/youtube/channel/sections` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `update_youtube_channel_section` | `PATCH /api/uploadposts/youtube/channel/sections/{section_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_channel_section` | `DELETE /api/uploadposts/youtube/channel/sections/{section_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `set_youtube_watermark` | `POST /api/uploadposts/youtube/channel/watermark` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `remove_youtube_watermark` | `DELETE /api/uploadposts/youtube/channel/watermark` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_playlists` | `GET /api/uploadposts/youtube/playlists` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `create_youtube_playlist` | `POST /api/uploadposts/youtube/playlists` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `update_youtube_playlist` | `PATCH /api/uploadposts/youtube/playlists/{playlist_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_playlist` | `DELETE /api/uploadposts/youtube/playlists/{playlist_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_playlist_items` | `GET /api/uploadposts/youtube/playlists/{playlist_id}/items` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `add_youtube_playlist_item` | `POST /api/uploadposts/youtube/playlists/{playlist_id}/items` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `update_youtube_playlist_item` | `PATCH /api/uploadposts/youtube/playlists/{playlist_id}/items/{item_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_playlist_item` | `DELETE /api/uploadposts/youtube/playlists/{playlist_id}/items/{item_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `get_youtube_playlist_image` | `GET /api/uploadposts/youtube/playlists/{playlist_id}/image` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `set_youtube_playlist_image` | `POST /api/uploadposts/youtube/playlists/{playlist_id}/image` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `replace_youtube_playlist_image` | `PUT /api/uploadposts/youtube/playlists/{playlist_id}/image` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_playlist_image` | `DELETE /api/uploadposts/youtube/playlists/{playlist_id}/image` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `list_youtube_captions` | `GET /api/uploadposts/youtube/captions` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `upload_youtube_caption` | `POST /api/uploadposts/youtube/captions` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `update_youtube_caption` | `PUT /api/uploadposts/youtube/captions/{caption_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `delete_youtube_caption` | `DELETE /api/uploadposts/youtube/captions/{caption_id}` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
| `download_youtube_caption` | `GET /api/uploadposts/youtube/captions/{caption_id}/download` | Off by default: answers `503` with `youtube_feature_disabled` until the feature is available. |
<!-- /openapi:availability -->

## Everything else in the API

Every operation of the [API reference](https://docs.upload-post.com) has a method. The ones below are generated from the OpenAPI spec, so they stay in step with it.

<!-- openapi:methods -->
Generated from the OpenAPI spec (`codegen/openapi.json`) by `codegen/generate.py`. Required fields are positional arguments; every other API field goes in `**params` by its API name.
Methods marked *not generally available* answer HTTP 503 until the feature is switched on for your account.

### Telegram

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `send_telegram_gift` | `POST /api/uploadposts/telegram/gifts` | Send a gift from the bot's Stars. *Not generally available.* |
| `gift_telegram_premium` | `POST /api/uploadposts/telegram/gifts/premium` | Gift Telegram Premium from the bot's Stars. *Not generally available.* |
| `get_telegram_payment_settings` | `GET /api/uploadposts/telegram/payments/settings` | Automatic pre-checkout rules. |
| `update_telegram_payment_settings` | `PUT /api/uploadposts/telegram/payments/settings` | Set automatic pre-checkout rules. |
| `set_telegram_updates` | `POST /api/uploadposts/telegram/updates` | Turn Telegram updates on or off. *Not generally available.* |
| `answer_telegram_query` | `POST /api/uploadposts/telegram/answer` | Answer a Telegram query. |
| `get_telegram_business_connections` | `GET /api/uploadposts/telegram/business-connections` | Telegram Business connections. *Not generally available.* |
| `get_telegram_business_profile` | `GET /api/uploadposts/telegram/business-profile` | Telegram Business account. *Not generally available.* |
| `update_telegram_business_profile` | `PATCH /api/uploadposts/telegram/business-profile` | Update the Telegram Business profile. *Not generally available.* |
| `post_telegram_story` | `POST /api/uploadposts/telegram/business-stories` | Post a Telegram story. *Not generally available.* |
| `edit_telegram_story` | `PATCH /api/uploadposts/telegram/business-stories` | Edit a Telegram story. *Not generally available.* |
| `delete_telegram_story` | `DELETE /api/uploadposts/telegram/business-stories` | Delete a Telegram story. *Not generally available.* |
| `repost_telegram_story` | `POST /api/uploadposts/telegram/business-stories/repost` | Repost a Telegram story. *Not generally available.* |
| `get_telegram_business_gifts` | `GET /api/uploadposts/telegram/business-gifts` | Telegram Business gifts. *Not generally available.* |
| `manage_telegram_business_gift` | `POST /api/uploadposts/telegram/business-gifts` | Convert, upgrade, transfer or delete a gift. *Not generally available.* |
| `get_telegram_business_stars` | `GET /api/uploadposts/telegram/business-stars` | Telegram Business Stars balance. *Not generally available.* |
| `transfer_telegram_business_stars` | `POST /api/uploadposts/telegram/business-stars/transfer` | Move Stars to the bot. *Not generally available.* |

### Content Upload

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `analyze_shorts` | `POST /api/uploadposts/analyze-shorts` | AI titles and captions for a short video. |
| `rewrite_captions` | `POST /api/uploadposts/rewrite-captions` | Translate or rewrite captions with AI. |
| `create_media_upload` | `POST /api/uploadposts/media-uploads` | Get a signed URL to upload a file. |
| `complete_media_upload` | `POST /api/uploadposts/media-uploads/{upload_id}/complete` | Confirm a signed upload. |
| `get_media_upload` | `GET /api/uploadposts/media-uploads/{upload_id}` | Get a signed upload. |
| `delete_media_upload` | `DELETE /api/uploadposts/media-uploads/{upload_id}` | Delete a signed upload. |

### Upload Management

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `get_scheduled_post` | `GET /api/uploadposts/schedule/{job_id}` | Get a scheduled post. |
| `get_scheduled_post_thumbnail` | `GET /api/uploadposts/schedule/{job_id}/thumbnail` | Get a scheduled post's thumbnail. |
| `get_scheduled_post_preview` | `GET /api/uploadposts/schedule/{job_id}/preview` | Preview URLs of a scheduled post. |

### Platform Integration

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `create_pinterest_board` | `POST /api/uploadposts/pinterest/boards` | Create a Pinterest board. |
| `query_youtube_analytics` | `GET /api/uploadposts/youtube/analytics/query` | Run a YouTube Analytics channel report. *Not generally available.* |
| `list_youtube_analytics_reports` | `GET /api/uploadposts/youtube/analytics/reports` | YouTube Analytics report catalog. *Not generally available.* |
| `list_youtube_analytics_groups` | `GET /api/uploadposts/youtube/analytics/groups` | List YouTube Analytics groups. *Not generally available.* |
| `list_youtube_analytics_group_items` | `GET /api/uploadposts/youtube/analytics/groups/{group_id}/items` | List the items of a YouTube Analytics group. *Not generally available.* |
| `get_youtube_analytics_usage` | `GET /api/uploadposts/youtube/analytics/usage` | Daily allowance of YouTube Analytics and bulk reports. *Not generally available.* |
| `list_youtube_report_types` | `GET /api/uploadposts/youtube/reporting/report-types` | List YouTube bulk report types. *Not generally available.* |
| `list_youtube_reporting_jobs` | `GET /api/uploadposts/youtube/reporting/jobs` | List YouTube reporting jobs. *Not generally available.* |
| `create_youtube_reporting_job` | `POST /api/uploadposts/youtube/reporting/jobs` | Create a YouTube reporting job. *Not generally available.* |
| `get_youtube_reporting_job` | `GET /api/uploadposts/youtube/reporting/jobs/{job_id}` | Get a YouTube reporting job. *Not generally available.* |
| `delete_youtube_reporting_job` | `DELETE /api/uploadposts/youtube/reporting/jobs/{job_id}` | Delete a YouTube reporting job. *Not generally available.* |
| `list_youtube_reports` | `GET /api/uploadposts/youtube/reporting/jobs/{job_id}/reports` | List the reports of a YouTube reporting job. *Not generally available.* |
| `get_youtube_report` | `GET /api/uploadposts/youtube/reporting/jobs/{job_id}/reports/{report_id}` | Get a YouTube report. *Not generally available.* |
| `download_youtube_report` | `GET /api/uploadposts/youtube/reporting/jobs/{job_id}/reports/{report_id}/download` | Download a YouTube report (CSV). *Not generally available.* |
| `get_youtube_push` | `GET /api/uploadposts/youtube/push` | YouTube new video notifications status. *Not generally available.* |
| `enable_youtube_push` | `POST /api/uploadposts/youtube/push` | Turn on YouTube new video notifications. *Not generally available.* |
| `disable_youtube_push` | `DELETE /api/uploadposts/youtube/push` | Turn off YouTube new video notifications. *Not generally available.* |
| `get_instagram_publishing_limit` | `GET /api/uploadposts/instagram/publishing_limit` | Instagram publishing quota. |
| `get_threads_publishing_limit` | `GET /api/uploadposts/threads/publishing_limit` | Threads publishing quota. |
| `list_pinterest_board_sections` | `GET /api/uploadposts/pinterest/boards/{board_id}/sections` | List the sections of a Pinterest board. |
| `create_pinterest_board_section` | `POST /api/uploadposts/pinterest/boards/{board_id}/sections` | Create a section in a Pinterest board. |
| `get_facebook_page_info` | `GET /api/uploadposts/facebook/page-info` | Read a Facebook Page's public info. |
| `update_facebook_page_info` | `PATCH /api/uploadposts/facebook/page-info` | Update a Facebook Page's public info. |
| `get_facebook_insights` | `GET /api/uploadposts/facebook/insights` | Read Facebook Page, post or video Insights on demand. |
| `list_facebook_video_captions` | `GET /api/uploadposts/facebook/videos/{video_id}/captions` | List the captions of a Facebook Page video. |
| `update_facebook_video_captions` | `POST /api/uploadposts/facebook/videos/{video_id}/captions` | Upload, set default or delete captions of a Facebook Page video. |
| `list_facebook_page_ratings` | `GET /api/uploadposts/facebook/ratings` | List a Facebook Page's reviews and recommendations. |
| `list_facebook_page_tagged_posts` | `GET /api/uploadposts/facebook/tagged` | List posts that tag a Facebook Page. |
| `list_reddit_subreddits` | `GET /api/uploadposts/reddit/subreddits` | Subreddits the Reddit account belongs to. |
| `get_reddit_post_types` | `GET /api/uploadposts/reddit/post-types` | Post types a subreddit allows. |
| `list_reddit_flairs` | `GET /api/uploadposts/reddit/flairs` | Post flairs of a subreddit. |
| `get_reddit_detailed_posts` | `GET /api/uploadposts/reddit/detailed-posts/` | Get Reddit detailed posts. |
| `list_threads_ghost_posts` | `GET /api/uploadposts/threads/ghost-posts` | List the account's Threads ghost posts. |
| `list_instagram_stories` | `GET /api/uploadposts/instagram/stories` | Instagram stories live now. |
| `list_instagram_tagged_media` | `GET /api/uploadposts/instagram/tagged` | Instagram posts where the account is tagged. |

### User Management

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `get_user_profile` | `GET /api/uploadposts/users/{username}` | Get a specific user profile. |
| `rename_user_profile` | `PATCH /api/uploadposts/users/{username}` | Rename a user profile. |
| `disconnect_social_account` | `DELETE /api/uploadposts/users/social` | Disconnect a social account from a profile. |
| `connect_discord_credentials` | `POST /api/uploadposts/users/discord/credentials` | Connect Discord with credentials. |
| `connect_telegram_credentials` | `POST /api/uploadposts/users/telegram/credentials` | Connect Telegram with credentials. |
| `connect_slack_credentials` | `POST /api/uploadposts/users/slack/credentials` | Connect Slack with credentials. |
| `connect_mastodon_credentials` | `POST /api/uploadposts/users/mastodon/credentials` | Connect Mastodon with credentials. |
| `connect_nostr_credentials` | `POST /api/uploadposts/users/nostr/credentials` | Connect Nostr with credentials. |
| `connect_lemmy_credentials` | `POST /api/uploadposts/users/lemmy/credentials` | Connect Lemmy with credentials. |
| `connect_devto_credentials` | `POST /api/uploadposts/users/devto/credentials` | Connect Dev.to with credentials. |
| `connect_hashnode_credentials` | `POST /api/uploadposts/users/hashnode/credentials` | Connect Hashnode with credentials. |
| `connect_wordpress_credentials` | `POST /api/uploadposts/users/wordpress/credentials` | Connect WordPress with credentials. |
| `connect_whop_credentials` | `POST /api/uploadposts/users/whop/credentials` | Connect Whop with credentials. |
| `connect_listmonk_credentials` | `POST /api/uploadposts/users/listmonk/credentials` | Connect Listmonk with credentials. |
| `list_facebook_page_choices` | `GET /api/uploadposts/users/facebook-page` | List the Facebook Pages a profile can publish to. |
| `set_facebook_page` | `POST /api/uploadposts/users/facebook-page` | Select the Facebook Page used when publishing. |
| `clear_facebook_page` | `DELETE /api/uploadposts/users/facebook-page` | Clear the selected Facebook Page. |
| `list_linkedin_page_choices` | `GET /api/uploadposts/users/linkedin-page` | List the LinkedIn Pages a profile can publish to. |
| `set_linkedin_page` | `POST /api/uploadposts/users/linkedin-page` | Select the LinkedIn Page used when publishing. |
| `clear_linkedin_page` | `DELETE /api/uploadposts/users/linkedin-page` | Clear the selected LinkedIn Page. |
| `connect_bluesky_credentials` | `POST /api/uploadposts/users/bluesky/credentials` | Connect Bluesky with an app password. |

### Authentication

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `get_current_user` | `GET /api/uploadposts/me` | Get current user. |
| `start_oauth_connection` | `POST /api/uploadposts/oauth/{platform}/start` | Connect API: start connecting a social account. |

### FFmpeg Editor

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `create_ffmpeg_job` | `POST /api/uploadposts/ffmpeg/jobs/upload` | Create FFmpeg job. |
| `get_ffmpeg_job_status` | `GET /api/uploadposts/ffmpeg/jobs/{job_id}` | Get FFmpeg job status. |
| `download_ffmpeg_result` | `GET /api/uploadposts/ffmpeg/jobs/{job_id}/download` | Download FFmpeg result. |
| `get_ffmpeg_consumption` | `GET /api/uploadposts/ffmpeg/consumption` | Get FFmpeg consumption. |

### Webhooks

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `list_webhook_subscriptions` | `GET /api/uploadposts/webhooks/subscriptions` | List webhook subscriptions. *Not generally available.* |
| `create_webhook_subscription` | `POST /api/uploadposts/webhooks/subscriptions` | Create a webhook subscription. *Not generally available.* |
| `get_webhook_subscription` | `GET /api/uploadposts/webhooks/subscriptions/{subscription_id}` | Get a webhook subscription. *Not generally available.* |
| `delete_webhook_subscription` | `DELETE /api/uploadposts/webhooks/subscriptions/{subscription_id}` | Delete a webhook subscription. *Not generally available.* |
| `test_webhook_subscription` | `POST /api/uploadposts/webhooks/subscriptions/{subscription_id}/test` | Send a test event to a subscription. *Not generally available.* |
| `test_notifications` | `POST /api/uploadposts/users/notifications/test` | Send a test notification. |

### Instagram Interactions

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `delete_comment_post` | `POST /api/uploadposts/comments/delete` | Delete a comment (POST alias). |
| `delete_bluesky_chat_account` | `POST /api/uploadposts/dms/bluesky/account/delete` | Delete the Bluesky chat account. *Not generally available.* |
| `list_bluesky_mutual_groups` | `GET /api/uploadposts/dms/bluesky/groups` | Bluesky groups shared with someone. *Not generally available.* |
| `create_bluesky_group` | `POST /api/uploadposts/dms/bluesky/groups` | Create a Bluesky group chat. *Not generally available.* |
| `edit_bluesky_group` | `PATCH /api/uploadposts/dms/bluesky/groups/{conversation_id}` | Rename, lock or unlock a Bluesky group. *Not generally available.* |
| `list_bluesky_group_members` | `GET /api/uploadposts/dms/bluesky/groups/{conversation_id}/members` | Bluesky group members. *Not generally available.* |
| `add_bluesky_group_members` | `POST /api/uploadposts/dms/bluesky/groups/{conversation_id}/members` | Add members to a Bluesky group. *Not generally available.* |
| `remove_bluesky_group_members` | `DELETE /api/uploadposts/dms/bluesky/groups/{conversation_id}/members` | Remove members from a Bluesky group. *Not generally available.* |
| `manage_bluesky_join_link` | `POST /api/uploadposts/dms/bluesky/groups/{conversation_id}/join-link` | Manage a Bluesky group join link. *Not generally available.* |
| `list_bluesky_join_requests` | `GET /api/uploadposts/dms/bluesky/groups/{conversation_id}/join-requests` | Pending requests to join a Bluesky group. *Not generally available.* |
| `answer_bluesky_join_request` | `POST /api/uploadposts/dms/bluesky/groups/{conversation_id}/join-requests` | Answer or withdraw a Bluesky join request. *Not generally available.* |
| `preview_bluesky_join_links` | `GET /api/uploadposts/dms/bluesky/join-links` | Preview Bluesky join links. *Not generally available.* |
| `join_bluesky_group` | `POST /api/uploadposts/dms/bluesky/join-links` | Ask to join a Bluesky group. *Not generally available.* |
| `download_dm_media` | `GET /api/uploadposts/dms/media` | Download a DM attachment. |
| `edit_whatsapp_template` | `PATCH /api/uploadposts/dms/templates` | Edit a WhatsApp template. |
| `list_whatsapp_blocked_users` | `GET /api/uploadposts/dms/whatsapp/blocked` | List blocked WhatsApp users. |
| `block_whatsapp_users` | `POST /api/uploadposts/dms/whatsapp/blocked` | Block WhatsApp users. |
| `unblock_whatsapp_users` | `DELETE /api/uploadposts/dms/whatsapp/blocked` | Unblock WhatsApp users. |
| `get_whatsapp_automation` | `GET /api/uploadposts/dms/whatsapp/automation` | WhatsApp commands and ice breakers. |
| `set_whatsapp_automation` | `POST /api/uploadposts/dms/whatsapp/automation` | Set WhatsApp commands and ice breakers. |
| `get_whatsapp_number` | `GET /api/uploadposts/dms/whatsapp/number` | WhatsApp number status. |
| `update_whatsapp_number` | `POST /api/uploadposts/dms/whatsapp/number` | Change WhatsApp display name or PIN. |
| `get_whatsapp_analytics` | `GET /api/uploadposts/dms/whatsapp/analytics` | WhatsApp analytics. |
| `enable_whatsapp_template_insights` | `POST /api/uploadposts/dms/whatsapp/analytics` | Enable WhatsApp template analytics. |
| `list_whatsapp_template_library` | `GET /api/uploadposts/dms/whatsapp/templates/library` | WhatsApp template library. |
| `get_instagram_messaging_profile` | `GET /api/uploadposts/dms/instagram/profile` | Read the Instagram ice breakers and persistent menu. |
| `set_instagram_messaging_profile` | `POST /api/uploadposts/dms/instagram/profile` | Set the Instagram ice breakers and/or persistent menu. |
| `delete_instagram_messaging_profile` | `DELETE /api/uploadposts/dms/instagram/profile` | Remove the Instagram ice breakers and/or persistent menu. |

### Bluesky

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `bluesky_graph_action` | `POST /api/uploadposts/bluesky/graph` | Follow, block or mute (one target per call). *Not generally available.* |
| `list_bluesky_lists` | `GET /api/uploadposts/bluesky/lists` | The account's lists. *Not generally available.* |
| `create_bluesky_list` | `POST /api/uploadposts/bluesky/lists` | Create a list. *Not generally available.* |
| `get_bluesky_list` | `GET /api/uploadposts/bluesky/lists/{list_id}` | A list and its members. *Not generally available.* |
| `update_bluesky_list` | `PATCH /api/uploadposts/bluesky/lists/{list_id}` | Update a list. *Not generally available.* |
| `delete_bluesky_list` | `DELETE /api/uploadposts/bluesky/lists/{list_id}` | Delete a list and its members. *Not generally available.* |
| `list_bluesky_list_members` | `GET /api/uploadposts/bluesky/lists/{list_id}/members` | List members. *Not generally available.* |
| `add_bluesky_list_member` | `POST /api/uploadposts/bluesky/lists/{list_id}/members` | Add a member. *Not generally available.* |
| `remove_bluesky_list_member` | `DELETE /api/uploadposts/bluesky/lists/{list_id}/members` | Remove a member. *Not generally available.* |
| `opt_out_bluesky_list` | `POST /api/uploadposts/bluesky/lists/opt-out` | Ask not to appear in a reference list. *Not generally available.* |
| `remove_opt_out_bluesky_list` | `DELETE /api/uploadposts/bluesky/lists/opt-out` | Withdraw the opt-out. *Not generally available.* |
| `list_bluesky_starter_packs` | `GET /api/uploadposts/bluesky/starter-packs` | The account's starter packs. *Not generally available.* |
| `create_bluesky_starter_pack` | `POST /api/uploadposts/bluesky/starter-packs` | Create a starter pack. *Not generally available.* |
| `get_bluesky_starter_pack` | `GET /api/uploadposts/bluesky/starter-packs/{pack_id}` | A starter pack. *Not generally available.* |
| `update_bluesky_starter_pack` | `PATCH /api/uploadposts/bluesky/starter-packs/{pack_id}` | Update a starter pack. *Not generally available.* |
| `delete_bluesky_starter_pack` | `DELETE /api/uploadposts/bluesky/starter-packs/{pack_id}` | Delete a starter pack. *Not generally available.* |
| `list_bluesky_feeds` | `GET /api/uploadposts/bluesky/feeds` | Feeds declared by the account. *Not generally available.* |
| `create_bluesky_feed` | `POST /api/uploadposts/bluesky/feeds` | Declare a custom feed. *Not generally available.* |
| `update_bluesky_feed` | `PATCH /api/uploadposts/bluesky/feeds/{rkey}` | Update a feed declaration. *Not generally available.* |
| `delete_bluesky_feed` | `DELETE /api/uploadposts/bluesky/feeds/{rkey}` | Delete a feed declaration. *Not generally available.* |
| `report_on_bluesky` | `POST /api/uploadposts/bluesky/report` | Report a post or account to Bluesky moderation. *Not generally available.* |

### Teams and Approvals

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `list_post_approvals` | `GET /api/uploadposts/approvals` | List posts awaiting approval. *Not generally available.* |
| `get_post_approval` | `GET /api/uploadposts/approvals/{approval_id}` | Get a post awaiting approval. *Not generally available.* |
| `edit_post_approval` | `PATCH /api/uploadposts/approvals/{approval_id}` | Edit a post awaiting approval. *Not generally available.* |
| `withdraw_post_approval` | `DELETE /api/uploadposts/approvals/{approval_id}` | Withdraw or discard a post awaiting approval. *Not generally available.* |
| `approve_post_approval` | `POST /api/uploadposts/approvals/{approval_id}/approve` | Approve a post. *Not generally available.* |
| `reject_post_approval` | `POST /api/uploadposts/approvals/{approval_id}/reject` | Reject a post. *Not generally available.* |
| `list_client_post_approvals` | `GET /api/uploadposts/approvals/client` | End client: list posts to approve. *Not generally available.* |
| `approve_client_post_approval` | `POST /api/uploadposts/approvals/client/{approval_id}/approve` | End client: approve a post. *Not generally available.* |
| `reject_client_post_approval` | `POST /api/uploadposts/approvals/client/{approval_id}/reject` | End client: reject a post. *Not generally available.* |
| `get_team_roles` | `GET /api/uploadposts/teams/roles` | Team roles and your role. |
| `list_team_audit` | `GET /api/uploadposts/teams/audit` | Team activity log. |

### Feedback

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `send_feedback` | `POST /api/uploadposts/feedback` | Send feedback to the Upload-Post team. |

### Google Business

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `update_google_business_account` | `PATCH /api/uploadposts/google-business/accounts` | Rename a Google Business account. *Not generally available.* |
| `create_google_business_admin` | `POST /api/uploadposts/google-business/admins` | Invite an admin. *Not generally available.* |
| `update_google_business_admin` | `PATCH /api/uploadposts/google-business/admins` | Change an admin's role. *Not generally available.* |
| `delete_google_business_admin` | `DELETE /api/uploadposts/google-business/admins` | Remove an admin. *Not generally available.* |
| `accept_google_business_invitation` | `POST /api/uploadposts/google-business/invitations/accept` | Accept an invitation. *Not generally available.* |
| `decline_google_business_invitation` | `POST /api/uploadposts/google-business/invitations/decline` | Decline an invitation. *Not generally available.* |
| `transfer_google_business_location` | `POST /api/uploadposts/google-business/locations/transfer` | Transfer a location to another account. *Not generally available.* |
| `create_google_business_location` | `POST /api/uploadposts/google-business/locations/create` | Create a location. *Not generally available.* |
| `delete_google_business_location` | `DELETE /api/uploadposts/google-business/locations/delete` | Delete a location. *Not generally available.* |
| `get_google_business_notification_settings` | `GET /api/uploadposts/google-business/notifications` | Get real-time notification settings. *Not generally available.* |
| `update_google_business_notification_settings` | `PUT /api/uploadposts/google-business/notifications` | Turn real-time notifications on or off. *Not generally available.* |
| `start_google_business_verification` | `POST /api/uploadposts/google-business/verification/start` | Start a verification. *Not generally available.* |
| `complete_google_business_verification` | `POST /api/uploadposts/google-business/verification/complete` | Enter the verification code. *Not generally available.* |
| `generate_google_business_verification_token` | `POST /api/uploadposts/google-business/verification/token` | Get an instant verification token. *Not generally available.* |

### ChatGPT Ads

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `connect_chatgpt_ads_account` | `POST /api/uploadposts/ads/chatgpt/connect` | Connect a ChatGPT Ads account. |
| `list_chatgpt_ads_accounts` | `GET /api/uploadposts/ads/chatgpt/accounts` | List connected ChatGPT Ads accounts. |
| `disconnect_chatgpt_ads_account` | `DELETE /api/uploadposts/ads/chatgpt/accounts/{ad_account_id}` | Disconnect a ChatGPT Ads account. |
| `get_chatgpt_ads_account` | `GET /api/uploadposts/ads/chatgpt/account` | Get live ad account metadata. |
| `list_chatgpt_ads_campaigns` | `GET /api/uploadposts/ads/chatgpt/campaigns` | List campaigns. |
| `create_chatgpt_ads_campaign` | `POST /api/uploadposts/ads/chatgpt/campaigns` | Create a campaign. |
| `get_chatgpt_ads_campaign` | `GET /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}` | Get a campaign. |
| `update_chatgpt_ads_campaign` | `POST /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}` | Update a campaign. |
| `activate_chatgpt_ads_campaign` | `POST /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}/activate` | Activate a campaign. |
| `pause_chatgpt_ads_campaign` | `POST /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}/pause` | Pause a campaign. |
| `archive_chatgpt_ads_campaign` | `POST /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}/archive` | Archive a campaign. |
| `get_chatgpt_ads_campaign_insights` | `GET /api/uploadposts/ads/chatgpt/campaigns/{campaign_id}/insights` | Get campaign insights. |
| `list_chatgpt_ads_ad_groups` | `GET /api/uploadposts/ads/chatgpt/adgroups` | List ad groups. |
| `create_chatgpt_ads_ad_group` | `POST /api/uploadposts/ads/chatgpt/adgroups` | Create an ad group. |
| `get_chatgpt_ads_ad_group` | `GET /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}` | Get an ad group. |
| `update_chatgpt_ads_ad_group` | `POST /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}` | Update an ad group. |
| `activate_chatgpt_ads_ad_group` | `POST /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/activate` | Activate an ad group. |
| `pause_chatgpt_ads_ad_group` | `POST /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/pause` | Pause an ad group. |
| `archive_chatgpt_ads_ad_group` | `POST /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/archive` | Archive an ad group. |
| `get_chatgpt_ads_ad_group_insights` | `GET /api/uploadposts/ads/chatgpt/adgroups/{ad_group_id}/insights` | Get ad group insights. |
| `list_chatgpt_ads_ads` | `GET /api/uploadposts/ads/chatgpt/ads` | List ads. |
| `create_chatgpt_ads_ad` | `POST /api/uploadposts/ads/chatgpt/ads` | Create an ad. |
| `get_chatgpt_ads_ad` | `GET /api/uploadposts/ads/chatgpt/ads/{ad_id}` | Get an ad. |
| `update_chatgpt_ads_ad` | `POST /api/uploadposts/ads/chatgpt/ads/{ad_id}` | Update an ad. |
| `activate_chatgpt_ads_ad` | `POST /api/uploadposts/ads/chatgpt/ads/{ad_id}/activate` | Activate an ad. |
| `pause_chatgpt_ads_ad` | `POST /api/uploadposts/ads/chatgpt/ads/{ad_id}/pause` | Pause an ad. |
| `archive_chatgpt_ads_ad` | `POST /api/uploadposts/ads/chatgpt/ads/{ad_id}/archive` | Archive an ad. |
| `get_chatgpt_ads_ad_insights` | `GET /api/uploadposts/ads/chatgpt/ads/{ad_id}/insights` | Get ad insights. |
| `preview_chatgpt_ads_ad` | `POST /api/uploadposts/ads/chatgpt/ads/{ad_id}/preview` | Preview an ad. |
| `upload_chatgpt_ads_creative` | `POST /api/uploadposts/ads/chatgpt/creatives` | Upload a creative image. |
| `get_chatgpt_ads_account_insights` | `GET /api/uploadposts/ads/chatgpt/insights` | Get ad account insights. |
| `promote_chatgpt_ads` | `POST /api/uploadposts/ads/chatgpt/promote` | Launch an ad in one call. |

### X

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `get_xmentions` | `GET /api/uploadposts/x/mentions` | Mentions of the whole X account. |
| `read_x` | `GET /api/uploadposts/x/read/{kind}` | Read X data (search, counts, likers, reposters, quotes, bookmarks, followers, lists, trends, analytics). |
| `manage_xlists` | `POST /api/uploadposts/x/lists` | Create, edit, delete X lists and add or remove members. |

### Pinterest

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `read_pinterest_api` | `GET /api/uploadposts/pinterest/api/{endpoint}` | Read Pinterest API v5 (boards, board sections, Pins). |
| `post_pinterest_api` | `POST /api/uploadposts/pinterest/api/{endpoint}` | Pinterest API v5 POST (create a board or a board section). |
| `patch_pinterest_api` | `PATCH /api/uploadposts/pinterest/api/{endpoint}` | Pinterest API v5 PATCH (update a board or a board section). |
| `delete_pinterest_api` | `DELETE /api/uploadposts/pinterest/api/{endpoint}` | Pinterest API v5 DELETE (delete a board or a board section). |

### Phone Numbers

| Method | Endpoint | What it does |
| :-- | :-- | :-- |
| `get_phone_numbers_config` | `GET /api/uploadposts/phone-numbers/config` | Phone numbers: availability for this account. |
| `list_phone_number_countries` | `GET /api/uploadposts/phone-numbers/countries` | Countries and prices of phone numbers. |
| `search_available_phone_numbers` | `GET /api/uploadposts/phone-numbers/available` | Search numbers to buy. |
| `purchase_phone_number` | `POST /api/uploadposts/phone-numbers/purchase` | Buy a phone number. |
| `get_phone_number_kyc_fields` | `GET /api/uploadposts/phone-numbers/kyc` | Identity fields a country needs. |
| `submit_phone_number_kyc` | `POST /api/uploadposts/phone-numbers/kyc` | Send identity documents and buy. |
| `list_phone_numbers` | `GET /api/uploadposts/phone-numbers` | List phone numbers. |
| `get_phone_number` | `GET /api/uploadposts/phone-numbers/{number_id}` | Get a phone number. |
| `release_phone_number` | `DELETE /api/uploadposts/phone-numbers/{number_id}` | Release a phone number. |
| `update_phone_number_voice` | `PATCH /api/uploadposts/phone-numbers/{number_id}/voice` | Call settings of a number. |
| `send_phone_number_sms` | `POST /api/uploadposts/phone-numbers/{number_id}/sms` | Send an SMS. |
| `list_phone_number_messages` | `GET /api/uploadposts/phone-numbers/{number_id}/messages` | SMS of a number. |
| `list_phone_number_calls` | `GET /api/uploadposts/phone-numbers/{number_id}/calls` | Calls and voicemails of a number. |
| `list_phone_number_codes` | `GET /api/uploadposts/phone-numbers/{number_id}/codes` | Verification codes received. |
| `prepare_phone_number_whatsapp` | `POST /api/uploadposts/phone-numbers/{number_id}/whatsapp/prepare` | Get ready to receive the WhatsApp code. |
| `get_phone_number_port_out_info` | `GET /api/uploadposts/phone-numbers/{number_id}/port-out` | Move a number to another carrier. |
| `get_phone_numbers_usage` | `GET /api/uploadposts/phone-numbers/usage` | Phone usage and charges. |
<!-- /openapi:methods -->

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
| `draft` | `tiktok_upload_to_draft` or `post_mode="MEDIA_UPLOAD"` (same draft) |
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
    tiktok_upload_to_draft=False,  # same draft as post_mode="MEDIA_UPLOAD"
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
| `tiktok_is_ai_generated` | bool | — | Video + photos. AI-generated content disclosure (aliases: `is_ai_generated`) |
| `tiktok_upload_to_draft` | bool | `draft` | Video + photos. Same draft as `post_mode="MEDIA_UPLOAD"` (aliases: `upload_to_draft`, `is_draft`). TikTok ignores the rest of the post settings |
| `tiktok_is_ads_only` | bool | — | Video. Only show in ads (alias: `is_ads_only`) |
| `tiktok_tto_invite_link` | str | — | Video. TikTok One invite link; needs branded content (alias: `tto_invite_link`) |
| `photo_cover_index` | int | — | Cover photo index for photo posts (0-based) |
| `privacy_level` | str | `photo_privacy` / `video_privacy` | Accepted on video and photo posts alike; which values the account may use is decided by TikTok, see the note below |
| `post_mode` | str | `draft` | `DIRECT_POST` or `MEDIA_UPLOAD`. `MEDIA_UPLOAD` is the same draft as `tiktok_upload_to_draft=True` |

## Platform-Specific Options

### TikTok (Video)
- `disable_duet` - Disable duet
- `disable_comment` - Disable comments
- `disable_stitch` - Disable stitch
- `cover_timestamp` - Timestamp in ms for cover
- `is_aigc` - AI-generated content flag
- `post_mode` - DIRECT_POST or MEDIA_UPLOAD. `MEDIA_UPLOAD` is the same draft as `tiktok_upload_to_draft=True`
- `brand_content_toggle` - Branded content toggle
- `brand_organic_toggle` - Brand organic toggle
- `tiktok_is_ads_only` - Only show the video in ads (alias: `is_ads_only`)
- `tiktok_tto_invite_link` - TikTok One invite link; needs branded content (alias: `tto_invite_link`)

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
- `post_mode` - DIRECT_POST or MEDIA_UPLOAD. `MEDIA_UPLOAD` is the same draft as `tiktok_upload_to_draft=True`
- `auto_add_music` - Auto add music
- `photo_cover_index` - Index of photo for cover (0-based)
- `disable_comment` - Disable comments
- `tiktok_music_id` - Commercial Music Library track id
- `tiktok_location_id` / `tiktok_location_name` - Location tag, both required together
- `tiktok_is_ai_generated` - AI-generated content disclosure
- `tiktok_upload_to_draft` - Same draft as `post_mode="MEDIA_UPLOAD"` (aliases: `upload_to_draft`, `is_draft`)

> TikTok's photo contract takes the music track id alone: `tiktok_music_volume`,
> `tiktok_music_start`, `tiktok_music_end`, `tiktok_original_sound_volume` and
> `tiktok_cover_image_url` are video-only. `post_mode="MEDIA_UPLOAD"` and
> `tiktok_upload_to_draft=True` are aliases of the same draft.

### Instagram
- `media_type` - REELS, STORIES, IMAGE
- `share_to_feed` - Share to feed (for Reels/Stories)
- `collaborators` - Comma-separated collaborator usernames
- `cover_url` - Custom cover URL
- `audio_name` - Audio track name
- `user_tags` - Comma-separated user tags
- `location_id` - Location ID
- `thumb_offset` - Thumbnail offset
- `instagram_alt_text` - Alt text (string, or JSON list / one per carousel item)

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
- `youtube_notify_subscribers` - Notify subscribers (default `true`; send `false` to skip)
- `youtube_publish_at` - RFC3339 time; uploads as private and schedules on YouTube
- `youtube_localizations` - Translated title/description per language: `{"es": {"title": ..., "description": ...}}`
- `youtube_brand_partner` - Brand partner channel id (`UC…`) for creator-initiated brand partner access

### LinkedIn
- `visibility` / `linkedin_visibility` - PUBLIC, CONNECTIONS, LOGGED_IN, CONTAINER
- `target_linkedin_page_id` - Page ID for organization posts
- `linkedin_alt_text` - Alt text per image (string, JSON list, or repeated)
- `linkedin_disable_reshare` - Disable reshare by others
- `linkedin_link_title` / `linkedin_link_description` / `linkedin_thumbnail_alt_text` - Article/link-share overrides
- `linkedin_target_geo_locations` / `linkedin_target_industries` / `linkedin_target_seniorities` / `linkedin_target_job_functions` / `linkedin_target_staff_count_ranges` / `linkedin_target_interface_locales` / `linkedin_target_degrees` / `linkedin_target_fields_of_study` / `linkedin_target_organizations` - Page targeting (needs `target_linkedin_page_id`)
- `linkedin_target_entities` - Raw targeting JSON instead of the fields above
- `linkedin_target_check_audience` - Reject if LinkedIn reports fewer than 300 followers in the segment
- `linkedin_subtitles` / `linkedin_subtitles_url` / `linkedin_subtitles_text` - English SRT captions on video

### Facebook
- `facebook_page_id` - Facebook Page ID (required)
- `video_state` - PUBLISHED, DRAFT
- `facebook_media_type` - REELS, STORIES, or VIDEO (normal page video)
- `thumbnail_url` - Thumbnail URL for normal page videos (only when `facebook_media_type` is VIDEO)
- `facebook_link_url` - URL for text posts
- `facebook_alt_text` - Alt text per photo (string, `facebook_alt_text[]`, or JSON array)
- `facebook_place_id` - Place id on feed/photos/videos/reels
- `facebook_targeting` / `facebook_feed_targeting` - JSON audience objects
- `facebook_call_to_action` / `facebook_child_attachments` / `facebook_multi_share_end_card` - Link post CTA and carousel
- `facebook_is_ai_generated` - AI-generated flag on Reels
- `facebook_collaborators` - Page ids to invite on Reels
- `facebook_unpublished_content_type` - DRAFT / INLINE_CREATED / ADS_POST on page video (`SCHEDULED` is rejected; use `scheduled_date`)
- `facebook_no_story` / `facebook_secret` - Page video flags

### Pinterest
- `pinterest_board_id` - Board ID
- `pinterest_link` - Destination link
- `pinterest_alt_text` - Alt text for photos
- `pinterest_cover_image_url` - Cover image URL (video)
- `pinterest_cover_image_key_frame_time` - Key frame time in seconds (values larger than the video duration are treated as milliseconds)
- `pinterest_board_section_id` - Board section id
- `pinterest_ai_disclosures` - `AI_MODIFIED` and/or `SYNTHETIC_PERFORMER`
- `pinterest_carousel_titles` / `pinterest_carousel_descriptions` / `pinterest_carousel_links` - Per-slide carousel fields (2–5 photos)
- `pinterest_carousel_index` - 0-based cover slide

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
- `x_alt_text` - Alt text (string, `x_alt_text[]`, or JSON array; ≤1000 chars)
- `x_subtitles` / `x_subtitles_url` / `x_subtitles_language` / `x_subtitles_name` - Video SRT captions
- `x_paid_partnership` - Paid partnership flag on the first post
- `x_article_title` / `x_article_body` / `x_article_content_state` / `x_article_draft` / `x_article_cover_media` - X Articles (text; Premium). Articles have two heading levels: a `### Heading` in the body, or a `header-three` block in `x_article_content_state`, is published as `header-two`

### Threads
- `threads_long_text_as_post` - Post long text as single post (vs thread). Over 500 UTF-8 bytes this sends an official long post instead of truncating.
- `threads_thread_media_layout` - Comma-separated list of how many media items to include in each Threads post (e.g. "5,5" or "3,4,3"). Each value 0-20, total must equal media count. Auto-chunks into groups of 20 when >20 items.
- `threads_topic_tag` - Topic tag for the Threads post (1-50 characters, no periods or ampersands). One tag per post. Helps increase reach.
- `threads_reply_control` - Who can reply: `everyone`, `accounts_you_follow`, `mentioned_only`, `parent_post_author_only`, `followers_only`
- `threads_alt_text` - Alt text per image/video (`threads_alt_text[]`)
- `threads_reply_to_id` / `threads_quote_post_id` - Reply or quote
- `threads_link_attachment` - Force link preview (text)
- `threads_poll_options` - 2–4 poll options (text)
- `threads_auto_publish_text` - Skip the second publish call on text posts

### Reddit
Reddit uploads currently return `error_code=reddit_unavailable` until the Reddit app is restored.

- `subreddit` - Subreddit name (without r/)
- `flair_id` - Flair template ID
- `reddit_nsfw` / `reddit_spoiler` / `reddit_resubmit` / `reddit_send_replies` - Booleans
- `reddit_flair_text` - Custom text for editable flairs
- `reddit_gallery_captions` / `reddit_gallery_urls` - Per-image gallery caption and outbound URL

### Google Business
- `gbp_location_id` - Location, e.g. `"accounts/123/locations/456"` (list them with `get_google_business_locations`). Required when the account has more than one location; the API only auto-selects when exactly one exists.
- `gbp_post_type` - `MEDIA`, `PHOTO` or `GALLERY` to publish into the location's photo gallery instead of creating a Local Post. Any other value, or omitting it, keeps the Local Post behaviour.
- `gbp_media_category` - Gallery category, default `ADDITIONAL`. One of `COVER`, `PROFILE`, `LOGO`, `EXTERIOR`, `INTERIOR`, `PRODUCT`, `AT_WORK`, `FOOD_AND_DRINK`, `MENU`, `COMMON_AREA`, `ROOMS`, `TEAMS`, `ADDITIONAL`.
- `gbp_topic_type` - STANDARD, EVENT or OFFER
- `gbp_media_url` / `gbp_media_format` - Media attached to the post
- `gbp_cta_type` / `gbp_cta_url` - Call-to-action button
- `gbp_event_title` / `gbp_event_start_date` / `gbp_event_start_time` / `gbp_event_end_date` / `gbp_event_end_time` - Used with `gbp_topic_type="EVENT"`
- `gbp_offer_coupon` / `gbp_offer_redeem_url` / `gbp_offer_terms` - Used with `gbp_topic_type="OFFER"`
- `gbp_coupon_code` / `gbp_redeem_url` / `gbp_terms` - Aliases of the offer fields above (legacy names still win if both are sent)
- `gbp_language_code` - BCP-47 language (default `en`)
- `gbp_recurrence` (`DAILY`, `WEEKLY`, `MONTHLY`) with `gbp_recurrence_days` / `gbp_recurrence_day_of_month` / `gbp_recurrence_week_occurrence` / `gbp_recurrence_end` - Recurring EVENT and OFFER posts
- `gbp_scheduled_time` - Google's own scheduling (RFC 3339 with time zone)
- `gbp_multi_media` - With a list in `gbp_media_url` (sent as `gbp_media_url[]`): several photos, max 10
- `gbp_alert_type` - For ALERT posts (`COVID_19`)
- `gbp_upload_to_gallery` - Same as `gbp_post_type="MEDIA"`

List, read, edit and delete the posts afterwards with `list_google_business_posts`,
`get_google_business_post`, `edit_post` and `unpublish_post`, or pin the location a
profile publishes to with `pin_google_business_location`.

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

### Bluesky
- `bluesky_link_url` - External embed link preview (text)
- `bluesky_alt_text` - Alt text per image/video (JSON array, `||`-separated, or string)
- `bluesky_langs` - Comma list, max 3 BCP-47 codes
- `bluesky_labels` - `porn`, `sexual`, `nudity`, `graphic-media`
- `bluesky_gallery` - Publish up to 10 images as a gallery (`false` keeps the first 4). With more than 10, the first 10 are published and the response carries a `warnings` entry
- `bluesky_threadgate` / `bluesky_reply_settings` - Who can reply
- `bluesky_postgate` / `bluesky_quote_settings` - `disable_quotes` to block quotes
- `bluesky_quote_uri` / `bluesky_quote_id` / `bluesky_quote_url` - Quote another post
- `bluesky_tags` - Up to 8 extra hashtags stored on the post, not shown in the text
- `bluesky_created_at` - Date Bluesky shows the post with (ISO 8601 with timezone, not in the future)
- `bluesky_thread_overflow` - Text over 300 characters goes on as replies instead of being cut
- `bluesky_gif_as_video` - A single animated GIF published as a looping video
- `bluesky_captions` - Video subtitles: `[{"lang": "es", "url": "https://.../es.vtt"}]` (WebVTT)
- `bluesky_video_presentation` - `default` or `gif`

### Discord
- `discord_thread_id` / `discord_thread_name` / `discord_applied_tags` - Thread or forum post
- `discord_embeds` / `discord_poll` / `discord_allowed_mentions` - JSON
- `discord_username` / `discord_avatar_url` - Per-post webhook identity
- `discord_alt_text` / `discord_flags` / `discord_tts` / `discord_max_file_mb`

### Telegram
- `telegram_parse_mode` - `MarkdownV2` or `HTML`
- `telegram_message_thread_id` - Forum topic
- `telegram_disable_notification` / `telegram_protect_content` / `telegram_has_spoiler` / `telegram_pin`
- `telegram_link_preview` / `telegram_reply_markup` / `telegram_as_document`
- `telegram_caption_overflow` - `truncate` (default) or `split`
- `telegram_media_urls` - Comma-separated public URLs for a mixed album
- `telegram_title` / `telegram_first_comment` - Telegram text and first comment
- `telegram_poll` / `telegram_location` / `telegram_venue` / `telegram_contact` / `telegram_dice` / `telegram_game_short_name` - Send a poll, a (live) location, a venue, a contact or a dice instead of a plain message (Telegram's JSON shapes)
- `telegram_pin_notify` - Notify the members when pinning
- `telegram_reply_to_message_id` / `telegram_reply_quote` / `telegram_reply_parameters` - Reply to a message
- `telegram_link_preview_options` / `telegram_entities` / `telegram_caption_entities` / `telegram_show_caption_above_media` - Formatting
- `telegram_first_comment_as_reply` - The first comment as a reply to the post (default `True`)
- `telegram_direct_messages_topic_id` / `telegram_suggested_post_parameters` / `telegram_ephemeral_message_parameters` / `telegram_message_effect_id`
- `telegram_send_as` (`animation`, `video_note`, `live_photo`, `document`, `audio`, `voice`...) with `telegram_performer` / `telegram_title_audio` / `telegram_duration` / `telegram_length` / `telegram_emoji` / `telegram_live_photo_photo`
- `telegram_paid_star_count` / `telegram_paid_payload` - Paid media unlocked with Telegram Stars
- `telegram_cover` / `telegram_thumbnail` (local file or URL) / `telegram_start_timestamp` / `telegram_send_by_url` / `telegram_disable_content_type_detection`

### Mastodon
- `mastodon_visibility` / `mastodon_sensitive` / `mastodon_spoiler_text` / `mastodon_language`
- `mastodon_alt_text` - `|`-separated for albums
- `mastodon_poll_options` / `mastodon_poll_expires_in` / `mastodon_poll_multiple`
- `mastodon_scheduled_at` - ISO 8601, at least 5 minutes ahead

### WordPress
- `wordpress_status` / `wordpress_date` - `publish`, `draft`, `pending`, `future` (`date` required for `future`)
- `wordpress_categories` / `wordpress_tags` / `wordpress_excerpt` / `wordpress_slug`
- `wordpress_alt_text` / `wordpress_media_caption` / `wordpress_block_format`

### Lemmy
- `lemmy_url` / `lemmy_community` / `lemmy_nsfw` / `lemmy_language_id` / `lemmy_alt_text`

### Slack
- `slack_markdown` / `slack_mrkdwn` / `slack_blocks` / `slack_alt_text`
- `slack_first_comment_mode` - `separate` (default) or `inline`

### Nostr
- `nostr_kind` - `1` default, `20` picture, `22` short video, `34235` video, `30023` long-form
- `nostr_long_form` - Shorthand for kind 30023

### Dev.to
- `devto_tags` / `devto_canonical_url` / `devto_description` / `devto_main_image` / `devto_series` / `devto_published`

### Hashnode
- `hashnode_body` / `content` - Article body
- `hashnode_tags` / `hashnode_original_article_url` / `hashnode_subtitle` / `hashnode_cover_image_url` / `hashnode_draft`

### Whop
- `whop_body` / `whop_pinned` / `whop_is_mention` / `whop_paywall_amount` / `whop_paywall_currency` / `whop_attachment_ids`

### Listmonk
- `listmonk_content_type` - `richtext` (default), `markdown`, `html`, `plain`
- `listmonk_send_at` / `listmonk_lists` / `listmonk_template_id` / `listmonk_media_ids`

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
| `paid_partnership` | Sponsored post. Mapped to each network's native label (TikTok `brand_content_toggle`, YouTube `hasPaidProductPlacement`, X `paid_partnership`); Facebook and Pinterest also need `facebook_sponsor_id` / `pinterest_sponsor_id`. Networks without a label publish without it, with a warning. A network-specific field wins. TikTok's own switch: `disclose_commercial` with `your_brand` / `branded_content` |

## Error Handling

```python
from upload_post import UploadPostClient, UploadPostError

client = UploadPostClient("YOUR_API_KEY")

try:
    response = client.upload_video("video.mp4", **options)
    print("Upload successful:", response)
except UploadPostError as e:
    print("Upload failed:", str(e))
    print(e.status_code)   # HTTP status, or None if no answer arrived
    print(e.error_code)    # stable code, e.g. "bluesky_dm_scope_missing", "TEAM_SEAT_SUSPENDED"
    print(e.response)      # decoded JSON body of the error
    print(e.retry_after)   # Retry-After seconds, when the API sent it
    print(e.error_type)    # `error_type` of the body, where the API sends one
```

Error bodies differ by area of the API (`error_code`, `reason`, `code` or
`error_type`); `error_code` reads the first of `error_code`, `code` and
`reason`. Methods marked *not generally available* answer HTTP 503 (for example
`webhook_subscriptions_disabled` or `post_approvals_disabled`) until the feature
is switched on for your account.

## Development: methods generated from the OpenAPI spec

`codegen/openapi.json` is a copy of the API's OpenAPI spec. Every operation in it
either has a hand-written method (listed in `codegen/sdk-map.json` under
`existing`), is left out on purpose (`excluded`, with the reason), or gets a
generated method from `codegen/generate.py` (standard library only; the same
file lives in the npm SDK). The client offers only what is switched on in
production: operations that are off there go in `excluded`, the ones production
switched on although the spec still marks them go in `available`, and
`hidden_fields` / `descriptions` keep fields and texts of features that are off
out of the generated methods (`tests/test_production_switches.py` checks it):

```bash
cp <spec> codegen/openapi.json        # the API's openapi/openapi.json
python3 codegen/generate.py           # rewrites the generated part of api_client.py and this README
python3 codegen/generate.py --check   # fails if they are out of date
python -m pytest tests
```

`tests/test_openapi_coverage.py` fails when an operation of the spec has no
method, and calls every method to check it sends the HTTP method and path of its
operation. `tests/test_upload_fields.py` fails when an upload drops a form field
the spec gives that endpoint. Generated code sits between `<openapi:...>`
markers: do not edit it by hand.

## Links

- [Upload-Post Website](https://www.upload-post.com)
- [API Documentation](https://docs.upload-post.com)
- [Dashboard](https://app.upload-post.com)

## License

MIT

<!-- deployed 2026-03-16 17:49 UTC -->
