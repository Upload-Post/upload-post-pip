import argparse
import logging
from pathlib import Path
from typing import List
from . import UploadPostClient, UploadPostError

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Upload videos to multiple social platforms via Upload-Post.com API"
    )
    parser.add_argument("--api-key", required=True, help="API authentication key")
    parser.add_argument("--video", required=True, type=Path, help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--user", required=True, help="User identifier")
    parser.add_argument(
        "--platforms", 
        nargs="+",
        required=True,
        choices=["tiktok", "instagram", "linkedin", "youtube", "facebook", "x", "threads", "pinterest"],
        help="Platforms to upload to. For platform-specific parameters, please use the Python API."
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    client = UploadPostClient(api_key=args.api_key)

    try:
        response = client.upload_video(
            video_path=args.video,
            title=args.title,
            user=args.user,
            platforms=args.platforms
        )
        logger.info(f"Upload successful! Response: {response}")
    except UploadPostError as e:
        logger.error(f"Upload failed: {str(e)}")
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()
