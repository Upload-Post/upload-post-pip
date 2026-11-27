# Changelog

## 2.23.0

Phone numbers: buy a number inside Upload-Post and use it for WhatsApp, SMS and
calls (paid plans only; no emergency calls). Only additions: no existing method
changes its name, arguments or result. Until phone numbers are available for
your account, the API answers `403 phone_numbers_not_available`.

### Added

- `get_phone_numbers_config`, `list_phone_number_countries`,
  `search_available_phone_numbers`, `purchase_phone_number` (idempotent on
  `purchase_intent_id`; `end_user`, `accept_terms`, `terms_version`),
  `get_phone_number_kyc_fields` and `submit_phone_number_kyc` (identity documents
  base64-encoded in `documents`), `list_phone_numbers`, `get_phone_number`,
  `release_phone_number` (final; `confirm=True` is a required argument),
  `get_phone_number_port_out_info`.
- `update_phone_number_voice` (forwarding, voicemail, recording, transcription),
  `send_phone_number_sms`, `list_phone_number_messages`, `list_phone_number_calls`,
  `list_phone_number_codes` and `prepare_phone_number_whatsapp` (receive the WhatsApp
  code by phone call), `get_phone_numbers_usage`.
- Webhook events (opt-in): `sms_received`, `call_received`, `voicemail_received`,
  `phone_number_activated`, `phone_number_declined`, `phone_number_released`,
  `phone_number_port_out` (`update_notification_config` docs and the webhook
  subscription events).
- README section "Phone numbers".

## 2.22.0

Covers the API features switched on in production on 2026-11-25, and only
those. Only additions: no existing method changes its name, arguments or result.

### Added

- Facebook Pages: `get_facebook_insights` (Page, post and video),
  `list_facebook_page_ratings`, `list_facebook_page_tagged_posts`,
  `list_facebook_video_captions` / `update_facebook_video_captions` (upload, set default or
  delete); `upload_text` `facebook_backdated_time` and `facebook_backdated_time_granularity`.
- Pinterest: `read_pinterest_api`, `post_pinterest_api`, `patch_pinterest_api`,
  `delete_pinterest_api` (Pinterest API v5 boards, board sections and Pins).
- TikTok: `create_comment` `image_url`; `get_suggestions` `type="trending"` and `personalized`.
- Threads: `threads_gif_id`, `threads_spoiler_media`, `threads_text_spoilers`,
  `threads_ghost_post` and `list_threads_ghost_posts`.
- Instagram: `list_instagram_stories`, `list_instagram_tagged_media`; `upload_photos` with a
  single video takes `cover_url`, `thumb_offset`, `share_to_feed` and `audio_name`;
  `user_tags` also on a video Story; `create_comment` posts a top-level comment on your own
  post (`post_id`/`post_url` without `comment_id`); comments carry `like_count` and `hidden`;
  `get_analytics` returns `breakdowns_detail` and post analytics `profile_activity`,
  `profile_activity_breakdown` and `reels_skip_rate` (documented);
  `get_instagram_messaging_profile`, `set_instagram_messaging_profile` and
  `delete_instagram_messaging_profile` (ice breakers and persistent menu).
- WhatsApp: `send_dm` `flow`, `carousel`, `location_request`, `call_button` (documented;
  sent as given); blocked users, commands and ice breakers, number (display name, PIN,
  quality, limit), analytics and templates (`edit_whatsapp_template`,
  `list_whatsapp_template_library`).
- X: `get_x_mentions`, `read_x` (search and counts, likers, reposters, quotes, bookmarks,
  followers and following, lists, trends, analytics), `manage_x_lists`; `post_action`
  `unrepost` / `bookmark` / `unbookmark`, `comment_action` `hide` / `unhide` of a reply;
  upload fields `x_video_title`, `x_video_description`, `x_video_cta*` (videos) and
  `x_clip_post_id`, `x_clip_start_seconds`, `x_clip_end_seconds` (text posts). Bookmarks,
  lists, followers/following, likers, `reposts_of_me` and hiding replies need an X account
  connected or reconnected on or after 2026-11-25 (otherwise `403 x_reconnect_required`).

### Changed

- `set_youtube_oauth_client` is deprecated: the API no longer documents it, but it still
  answers.

## 2.21.1

### Changed

- DM docs list the networks that work today: Instagram, WhatsApp, Bluesky and
  Telegram.

## 2.21.0

WhatsApp DMs, fully covered. WhatsApp is open to every account; it is a
messaging channel only (it never publishes posts). Only additions.

### Added

- `upload_dm_media(user, file, platform=None, type=None, page_id=None,
  filename=None, content_type=None, **fields)`: multipart upload to
  `POST /dms/media` (the MIME type is guessed from the file name); send the
  answer's `type` and `media_id` in `send_dm` attachments.
- Templates: `list_dm_templates`, `create_dm_template`, `delete_dm_template`
  (`/dms/templates`).
- WhatsApp Business profile: `get_whatsapp_business_profile`,
  `update_whatsapp_business_profile` (optional photo `file`, sent as multipart).
- WhatsApp QR codes / short links: `list_whatsapp_qr_codes`,
  `create_whatsapp_qr_code`, `delete_whatsapp_qr_code`.

### Changed

- `send_dm` docstring documents every WhatsApp field and the 24-hour window
  rule; Messenger is documented as a limited rollout (403
  `messenger_not_enabled`).
- `DELETE` requests can carry a query string (used by the template and QR
  deletes).

## 2.18.0

The client now covers every operation of the Upload-Post OpenAPI spec (467).
Only additions, plus one fix: no other method changes its name, arguments or
result.

### Added

- 180 methods generated from the OpenAPI spec (`codegen/openapi.json`) by
  `codegen/generate.py` (required fields are arguments, the rest `**params`):
  - Webhook subscriptions: `create_webhook_subscription`, `list_webhook_subscriptions`,
    `get_webhook_subscription`, `delete_webhook_subscription`, `test_webhook_subscription`.
  - Post approvals: `list_post_approvals`, `get_post_approval`, `edit_post_approval`,
    `withdraw_post_approval`, `approve_post_approval`, `reject_post_approval`, and for
    the end client (profile JWT as `token`) `list_client_post_approvals`,
    `approve_client_post_approval`, `reject_client_post_approval`.
  - Teams: `get_team_roles`, `list_team_audit`.
  - ChatGPT Ads (32 methods), FFmpeg jobs (`create_ffmpeg_job`,
    `get_ffmpeg_job_status`, `download_ffmpeg_result`, `get_ffmpeg_consumption`),
    Bluesky lists, starter packs, feeds and group chats, DM media download,
    Telegram gifts, payments, business account and stories, Google Business
    admins, invitations, locations, notifications and verification, YouTube
    Analytics, Reporting and push notifications, Pinterest boards and sections,
    Reddit subreddits, flairs, post types and detailed posts, Facebook page info,
    connection of credential-based platforms (`connect_*_credentials`), Facebook /
    LinkedIn page pinning, `disconnect_social_account`, `start_oauth_connection`,
    `get_current_user`, `get_user_profile`, `rename_user_profile`, scheduled post
    detail, thumbnail and preview, resumable media uploads, `analyze_shorts`,
    `rewrite_captions`, `send_feedback`, `test_notifications`, Instagram / Threads
    publishing limits.
  - Methods whose operation the spec marks `x-availability: not_generally_available`
    say so in their docstring and in the README (generated methods and, in their
    own table, the hand-written ones): they answer an error (usually HTTP 503)
    until the feature is switched on for the account.
  - The six deprecated aliases of the spec (POST/PATCH copies of Google Business
    routes the client already calls with the right verb) are left out on purpose.
- Upload fields the API accepts and the client dropped: `reddit_title`,
  `exclude_reply_user_ids`, `telegram_allow_paid_broadcast`, `telegram_send_title`,
  `share_mode` (Instagram Trial Reels), `thumbnail` (YouTube, a local file),
  `cover_image` (Instagram, a local file), `first_comment_media` on `upload_video`,
  and on `upload_document` `platforms=["telegram"]` (default still LinkedIn only)
  with the Telegram fields.
- `UploadPostError.error_type` (the `error_type` of the answer, where the API sends one).
- `generate_jwt(..., client_approval=True|False)`: lets the end client approve
  posts from the connect page (post approvals, not generally available yet).
- Docs for the new answers: uploads by an Editor or Contributor team member
  (HTTP 202 `pending_approval`, `approval_id`, `approval_status`), `role` /
  `profiles` in `list_team_members` and `list_shared_accounts`, `configured` in
  `get_queue_settings`, `client_approval` in `validate_jwt`. README: roles and
  post approvals, and reading Telegram DMs (`get_dm_conversations`).

### Fixed

- `first_comment_media` URLs: the API reads `first_comment_media[]` from uploaded
  files only. A URL used to fail with "First comment media file not found"; now
  `upload_video`, `upload_photos` and `upload_text` download it (a plain request,
  without the API key) and send it as a file. A URL that cannot be downloaded
  raises `UploadPostError` naming it, before the upload is sent. Local paths
  work as before; bytes are accepted too.

- `validate_jwt` always failed with HTTP 405: it sent a POST with the token in
  the body. It now sends the GET with `Authorization: Bearer <jwt>` the API
  expects (same arguments and result).

### Tests

- `tests/test_openapi_coverage.py`: every operation of the spec has a method and
  each method sends the HTTP method and path of its operation; the generated code
  is up to date with the spec.
- `tests/test_upload_fields.py`: the uploads send every form field the spec gives them.
- `tests/test_resource_endpoints.py`: `generate_jwt` sends every body field of the spec.
- `.github/workflows/test.yml` runs the tests and the checks on every push and
  pull request.
