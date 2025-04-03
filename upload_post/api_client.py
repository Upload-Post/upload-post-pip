from pathlib import Path
from typing import Dict, List, Union

import requests


class UploadPostError(Exception):
    """Base exception for Upload-Post API errors"""
    pass

class UploadPostClient:
    BASE_URL = "https://api.upload-post.com/api"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Apikey {self.api_key}",
            "User-Agent": f"upload-post-python-client/0.1.0"
        })

    def upload_video(
        self,
        video_path: Union[str, Path],
        title: str,
        user: str,
        platforms: List[str]
    ) -> Dict:
        """
        Upload a video to specified social media platforms
        
        Args:
            video_path: Path to video file
            title: Video title
            user: User identifier
            platforms: List of platforms (e.g. ["tiktok", "instagram"])
            
        Returns:
            API response JSON
            
        Raises:
            UploadPostError: If upload fails
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise UploadPostError(f"Video file not found: {video_path}")

        try:
            with video_path.open("rb") as video_file:
                files = {"video": video_file}
                data = {
                    "title": title,
                    "user": user,
                    "platform[]": platforms
                }
                
                response = self.session.post(
                    f"{self.BASE_URL}/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            raise UploadPostError(
                f"API request failed: {str(e)}"
            ) from e
        except (ValueError, TypeError) as e:
            raise UploadPostError(
                f"Invalid response format: {str(e)}"
            ) from e
