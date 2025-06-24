# upload-post Python Client

A Python client for the [Upload-Post.com](https://www.upload-post.com/) API, designed to facilitate interaction with the service. Upload-Post.com allows you to upload videos to multiple social media platforms simultaneously.

[![PyPI version](https://img.shields.io/pypi/v/upload-post.svg)](https://pypi.org/project/upload-post/)
[![Python Versions](https://img.shields.io/pypi/pyversions/upload-post.svg)](https://pypi.org/project/upload-post/)

## Features

- 🚀 Upload videos to TikTok, Instagram, LinkedIn, YouTube, Facebook, X (Twitter), Threads, and Pinterest (platform support based on API availability)
- 🖼️ Upload photos to TikTok, Instagram, LinkedIn, Facebook, X (Twitter), Threads, and Pinterest
- ✍️ Upload text posts to LinkedIn, X (Twitter), Facebook, and Threads
- 🔒 Secure API key authentication
- 📁 File validation and error handling
- 📊 Detailed logging
- 🤖 Both CLI and Python API interfaces

## Installation

```bash
pip install upload-post
```

## Usage

### Command Line Interface

```bash
upload-post \
  --api-key "your_api_key_here" \
  --video "/path/to/video.mp4" \
  --title "My Awesome Video" \
  --user "testuser" \
  --platforms tiktok instagram
```

### Python API

```python
from upload_post import UploadPostClient, UploadPostError
from pathlib import Path

# Initialize client
client = UploadPostClient(api_key="your_api_key_here")

# Example: Upload a video
try:
    response_video = client.upload_video(
        video_path="/path/to/video.mp4", # Can also be a URL: "https://example.com/video.mp4"
        title="My Awesome Video",
        user="testuser",
        platforms=["tiktok", "youtube", "linkedin"],
        # TikTok specific
        privacy_level="PUBLIC_TO_EVERYONE",
        disable_comment=False,
        # YouTube specific
        description="Detailed description for YouTube",
        tags=["tutorial", "python", "api"],
        categoryId="22", # "People & Blogs"
        privacyStatus="public",
        # LinkedIn specific
        visibility="PUBLIC", # Required for LinkedIn if not using default
        description="Post commentary for LinkedIn" # Optional, uses title if not set
    )
    print(f"Video upload successful: {response_video}")
except UploadPostError as e:
    print(f"Video upload failed: {e}")

# Example: Upload photos
try:
    response_photos = client.upload_photos(
        photos=["/path/to/image1.jpg", Path("/path/to/image2.png"), "https://example.com/photo3.jpg"],
        user="testuser",
        platforms=["instagram", "facebook"],
        title="My Photo Album",
        caption="Check out these cool photos!",
        # Platform-specific parameters
        facebook_page_id="your_facebook_page_id", # Required for Facebook
        media_type="IMAGE" # For Instagram, "IMAGE" or "STORIES"
    )
    print(f"Photo upload successful: {response_photos}")
except UploadPostError as e:
    print(f"Photo upload failed: {e}")

# Example: Upload a text post
try:
    response_text = client.upload_text(
        user="testuser",
        platforms=["x", "linkedin"],
        title="This is my awesome text post! #Python #API",
        # Platform-specific parameters
        # For LinkedIn, if posting to an organization page:
        # target_linkedin_page_id="your_linkedin_page_id",
        # For Facebook, facebook_page_id is required:
        # facebook_page_id="your_facebook_page_id" 
        # (add 'facebook' to platforms list too)
    )
    print(f"Text post successful: {response_text}")
except UploadPostError as e:
    print(f"Text post failed: {e}")
```

## Error Handling

The client raises `UploadPostError` exceptions for API errors. Common error scenarios:

- Invalid API key
- Missing required parameters
- File not found
- Platform not supported
- API rate limits exceeded

## Documentation

For full API documentation and platform availability, see the official [Upload-Post.com documentation](https://www.upload-post.com/).

## License

MIT License - See [LICENSE](LICENSE) for details.
