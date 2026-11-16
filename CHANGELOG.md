# Changelog

## 2.18.0

The client now covers every operation of the Upload-Post OpenAPI spec (467).
Only additions, plus one fix: no other method changes its name, arguments or
result.

### Added

- 182 methods generated from the OpenAPI spec (`codegen/openapi.json`) by
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
  - Methods marked *not generally available* in their docstring answer HTTP 503
    until the feature is switched on for the account.
- Upload fields the API accepts and the client dropped: `reddit_title`,
  `exclude_reply_user_ids`, `telegram_allow_paid_broadcast`, `telegram_send_title`,
  `share_mode` (Instagram Trial Reels), `thumbnail` (YouTube, a local file),
  `cover_image` (Instagram, a local file), `first_comment_media` on `upload_video`,
  and on `upload_document` `platforms=["telegram"]` (default still LinkedIn only)
  with the Telegram fields.
- `UploadPostError.error_type` (the `error_type` of the answer, where the API sends one).

### Fixed

- `validate_jwt` always failed with HTTP 405: it sent a POST with the token in
  the body. It now sends the GET with `Authorization: Bearer <jwt>` the API
  expects (same arguments and result).

### Tests

- `tests/test_openapi_coverage.py`: every operation of the spec has a method and
  each method sends the HTTP method and path of its operation; the generated code
  is up to date with the spec.
- `tests/test_upload_fields.py`: the uploads send every form field the spec gives them.
- `.github/workflows/test.yml` runs the tests and the checks on every push and
  pull request.
