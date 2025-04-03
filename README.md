# upload-post Python Client

A Python client for the [Upload-Post.com](https://www.upload-post.com/) API, designed to facilitate interaction with the service. Upload-Post.com allows you to upload videos to multiple social media platforms simultaneously.

[![PyPI version](https://img.shields.io/pypi/v/upload-post.svg)](https://pypi.org/project/upload-post/)
[![Python Versions](https://img.shields.io/pypi/pyversions/upload-post.svg)](https://pypi.org/project/upload-post/)

## Features

- 🚀 Upload videos to TikTok, Instagram, Facebook, and YouTube (platform support based on API availability)
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
from upload_post import UploadPostClient

client = UploadPostClient(api_key="your_api_key_here")

response = client.upload_video(
    video_path="/path/to/video.mp4",
    title="My Awesome Video",
    user="testuser",
    platforms=["tiktok", "instagram"]
)
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
