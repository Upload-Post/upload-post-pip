# Upload-Post SDK for Python

Official Python client for the [Upload-Post API](https://www.upload-post.com) - Cross-platform social media upload.

Upload videos, photos, text posts, and documents to **TikTok, Instagram, YouTube, LinkedIn, Facebook, Pinterest, Threads, Reddit, Bluesky, and X (Twitter)** with a single API.

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

- ✅ **Video Upload** - TikTok, Instagram, YouTube, LinkedIn, Facebook, Pinterest, Threads, Bluesky, X
- ✅ **Photo Upload** - TikTok, Instagram, LinkedIn, Facebook, Pinterest, Threads, Reddit, Bluesky, X
- ✅ **Text Posts** - X, LinkedIn, Facebook, Threads, Reddit, Bluesky
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
    privacy_level="PUBLIC_TO_EVERYONE",  # TikTok
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
)
```

### Get Analytics

```python
analytics = client.get_analytics(
    "my-profile",
    platforms=["instagram", "tiktok"],
)
print(analytics)
```

### Helper Methods

```python
# Get Facebook pages for a profile
fb_pages = client.get_facebook_pages("my-profile")

# Get LinkedIn pages for a profile
li_pages = client.get_linkedin_pages("my-profile")

# Get Pinterest boards for a profile
boards = client.get_pinterest_boards("my-profile")
```

## Platform-Specific Options

### TikTok (Video)
- `privacy_level` - PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR, SELF_ONLY
- `disable_duet` - Disable duet
- `disable_comment` - Disable comments
- `disable_stitch` - Disable stitch
- `cover_timestamp` - Timestamp in ms for cover
- `is_aigc` - AI-generated content flag
- `post_mode` - DIRECT_POST or MEDIA_UPLOAD
- `brand_content_toggle` - Branded content toggle
- `brand_organic_toggle` - Brand organic toggle

### TikTok (Photos)
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

### LinkedIn
- `visibility` - PUBLIC, CONNECTIONS, LOGGED_IN, CONTAINER
- `target_linkedin_page_id` - Page ID for organization posts

### Facebook
- `facebook_page_id` - Facebook Page ID (required)
- `video_state` - PUBLISHED, DRAFT
- `facebook_media_type` - REELS, STORIES
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

### Threads
- `threads_long_text_as_post` - Post long text as single post (vs thread)

### Reddit
- `subreddit` - Subreddit name (without r/)
- `flair_id` - Flair template ID

## Common Options

These options work across all upload methods:

| Option | Description |
|--------|-------------|
| `title` | Post title/caption (required for most platforms; optional for TikTok-only uploads) |
| `user` | Profile name (required) |
| `platforms` | Target platforms list (required) |
| `first_comment` | First comment to post |
| `alt_text` | Alt text for accessibility |
| `scheduled_date` | ISO date for scheduling |
| `timezone` | Timezone for scheduled date |
| `add_to_queue` | Add to posting queue |
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
