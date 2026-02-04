"""
Upload-Post - Cross-platform social media upload

Upload videos, photos, text posts, and documents to TikTok, Instagram, YouTube,
LinkedIn, Facebook, Pinterest, Threads, Reddit, Bluesky, and X (Twitter).

Example:
    >>> from upload_post import UploadPostClient
    >>> client = UploadPostClient("YOUR_API_KEY")
    >>> response = client.upload_video(
    ...     "video.mp4",
    ...     title="My awesome video",
    ...     user="my-profile",
    ...     platforms=["tiktok", "instagram"]
    ... )
"""

__version__ = "2.0.0"

from .api_client import UploadPostClient, UploadPostError

__all__ = ['UploadPostClient', 'UploadPostError', '__version__']
