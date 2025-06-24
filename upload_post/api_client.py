from pathlib import Path
from typing import Dict, List, Union, Optional

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
        platforms: List[str],
        **kwargs
    ) -> Dict:
        """
        Upload a video to specified social media platforms.

        Args:
            video_path: Path to video file (str or Path) or video URL (str).
            title: Video title.
            user: User identifier.
            platforms: List of platforms (e.g., ["tiktok", "instagram", "linkedin"]).
            **kwargs: Platform-specific parameters.
                tiktok: privacy_level (str), disable_duet (bool), disable_comment (bool),
                        disable_stitch (bool), cover_timestamp (int), brand_content_toggle (bool),
                        brand_organic (bool), branded_content (bool), brand_organic_toggle (bool),
                        is_aigc (bool)
                instagram: media_type (str), share_to_feed (bool), collaborators (str),
                           cover_url (str), audio_name (str), user_tags (str),
                           location_id (str), thumb_offset (str)
                linkedin: description (str), visibility (str), target_linkedin_page_id (str)
                youtube: description (str), tags (List[str]), categoryId (str),
                         privacyStatus (str), embeddable (bool), license (str),
                         publicStatsViewable (bool), madeForKids (bool)
                facebook: facebook_page_id (str), description (str), video_state (str)
                threads: description (str)
                x: tagged_user_ids (List[str]), reply_settings (str), nullcast (bool),
                   place_id (str), poll_duration (int), poll_options (List[str]),
                   poll_reply_settings (str)
                pinterest: pinterest_board_id (str), pinterest_link (str),
                           pinterest_cover_image_url (str),
                           pinterest_cover_image_content_type (str),
                           pinterest_cover_image_data (str),
                           pinterest_cover_image_key_frame_time (int)

        Returns:
            API response JSON.

        Raises:
            UploadPostError: If upload fails or video file not found.
        """
        data_payload: List[tuple] = []
        files_payload: List[tuple] = []
        video_file_obj = None # To keep track of the opened file

        try:
            # Prepare video
            if isinstance(video_path, str) and \
               (video_path.startswith('http://') or video_path.startswith('https://')):
                # It's a URL
                data_payload.append(('video', video_path))
            else:
                # It's a file path
                video_p = Path(video_path)
                if not video_p.exists():
                    raise UploadPostError(f"Video file not found: {video_p}")
                
                video_file_obj = video_p.open("rb")
                files_payload.append(('video', (video_p.name, video_file_obj)))

            # Prepare common parameters
            data_payload.append(('title', title))
            data_payload.append(('user', user))
            for p in platforms:
                data_payload.append(('platform[]', p))

            # Add platform-specific parameters from kwargs
            for key, value in kwargs.items():
                if isinstance(value, bool):
                    data_payload.append((key, str(value).lower())) # 'true' or 'false'
                elif isinstance(value, list):
                    for v_item in value: # Handles array parameters like 'tags' or 'tagged_user_ids'
                        data_payload.append((f'{key}[]' if key.endswith('s') else key, str(v_item))) # API expects tags[] for YouTube, etc.
                else:
                    data_payload.append((key, str(value)))
            
            response = self.session.post(
                f"{self.BASE_URL}/upload", # Endpoint for video is /upload
                files=files_payload if files_payload else None,
                data=data_payload
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
        finally:
            if video_file_obj:
                video_file_obj.close()

    def upload_photos(
        self,
        photos: List[Union[str, Path]],
        user: str,
        platforms: List[str],
        title: str,
        caption: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Upload photos to specified social media platforms.

        Args:
            photos: List of photo file paths (str or Path) or photo URLs (str).
            user: User identifier.
            platforms: List of platforms (e.g., ["tiktok", "instagram"]).
            title: Title of the post.
            caption: Optional caption/description for the photos.
            **kwargs: Platform-specific parameters.
                linkedin: visibility (str), target_linkedin_page_id (str)
                facebook: facebook_page_id (str)
                tiktok: auto_add_music (bool), disable_comment (bool), 
                        branded_content (bool), disclose_commercial (bool),
                        photo_cover_index (int), description (str)
                instagram: media_type (str)
                pinterest: pinterest_board_id (str), pinterest_alt_text (str), 
                           pinterest_link (str)

        Returns:
            API response JSON.

        Raises:
            UploadPostError: If upload fails or any photo file not found.
        """
        data_payload: List[tuple] = []
        files_payload: List[tuple] = []
        opened_files: List[object] = []  # To keep track of files to close them later

        try:
            # Prepare photos
            for photo_item in photos:
                if isinstance(photo_item, str) and \
                   (photo_item.startswith('http://') or photo_item.startswith('https://')):
                    # It's a URL
                    data_payload.append(('photos[]', photo_item))
                else:
                    # It's a file path
                    photo_path = Path(photo_item)
                    if not photo_path.exists():
                        raise UploadPostError(f"Photo file not found: {photo_path}")
                    
                    photo_file_obj = photo_path.open("rb")
                    opened_files.append(photo_file_obj)
                    files_payload.append(('photos[]', (photo_path.name, photo_file_obj)))
            
            # Prepare common parameters
            data_payload.append(('user', user))
            data_payload.append(('title', title))
            if caption is not None:
                data_payload.append(('caption', caption))

            for p in platforms:
                data_payload.append(('platform[]', p))

            # Add platform-specific parameters from kwargs
            for key, value in kwargs.items():
                if isinstance(value, bool):
                    data_payload.append((key, str(value).lower())) # 'true' or 'false'
                elif isinstance(value, list):
                    for v_item in value: # Handles cases where a kwarg value is a list
                        data_payload.append((key, str(v_item)))
                else:
                    data_payload.append((key, str(value)))

            response = self.session.post(
                f"{self.BASE_URL}/upload_photos",
                files=files_payload if files_payload else None,
                data=data_payload
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise UploadPostError(f"API request failed: {str(e)}") from e
        except (ValueError, TypeError) as e: # ValueError for json parsing, TypeError for bad args
            raise UploadPostError(f"Data or response format error: {str(e)}") from e
        finally:
            for f_obj in opened_files:
                f_obj.close()

    def upload_text(
        self,
        user: str,
        platforms: List[str],
        title: str, # As per API docs, 'title' is used for the text content
        **kwargs
    ) -> Dict:
        """
        Upload text posts to specified social media platforms.

        Args:
            user: User identifier.
            platforms: List of platforms (e.g., ["x", "linkedin"]). 
                       Supported: "linkedin", "x", "facebook", "threads".
            title: The text content for the post.
            **kwargs: Platform-specific parameters.
                linkedin: target_linkedin_page_id (str)
                facebook: facebook_page_id (str)

        Returns:
            API response JSON.

        Raises:
            UploadPostError: If upload fails.
        """
        data_payload: List[tuple] = []

        try:
            # Prepare common parameters
            data_payload.append(('user', user))
            data_payload.append(('title', title)) # 'title' carries the text content

            for p in platforms:
                data_payload.append(('platform[]', p))

            # Add platform-specific parameters from kwargs
            # (e.g., target_linkedin_page_id, facebook_page_id)
            for key, value in kwargs.items():
                if isinstance(value, bool): # Should not happen based on current docs for text
                    data_payload.append((key, str(value).lower()))
                elif isinstance(value, list): # Should not happen based on current docs for text
                    for v_item in value:
                        data_payload.append((key, str(v_item)))
                else:
                    data_payload.append((key, str(value)))
            
            response = self.session.post(
                f"{self.BASE_URL}/upload_text",
                data=data_payload
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise UploadPostError(f"API request failed: {str(e)}") from e
        except (ValueError, TypeError) as e: 
            raise UploadPostError(f"Data or response format error: {str(e)}") from e
