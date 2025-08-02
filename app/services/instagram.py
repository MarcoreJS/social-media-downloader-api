import re
import requests
import instaloader
from typing import Optional
from urllib.parse import urlparse
from app.models.schemas import DownloadResponse
from app.services.downloader import MediaDownloader
from app.services.storage import S3StorageService
# from app.utils.exceptions import DownloadException


class InstagramDownloader(MediaDownloader):
    def __init__(self, storage_service: S3StorageService):
        self.storage_service = storage_service
        self.session = requests.Session()
        self.instagram_pattern = re.compile(
            r'(https?://)?(www\.)?instagram\.com/(p|reel|tv)/[a-zA-Z0-9_-]+/?'
        )

    def supports(self, url: str) -> bool:
        """Check if the URL is an Instagram post"""
        return bool(self.instagram_pattern.match(url))

    def download(self, url: str) -> DownloadResponse:
        """Download Instagram media and upload to S3"""
        if not self.supports(url):
            raise Exception("Unsupported Instagram URL")

        try:
            # In a real implementation, you would use a proper Instagram API or library
            # This is a simplified example
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            shortcode = path.split('/')[-1]
            print(shortcode)
            L = instaloader.Instaloader(
                dirname_pattern='temp',
                filename_pattern='{shortcode}',
                save_metadata=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                compress_json=False
            )

            L.login("ml.marcoo", "968774654132As!")

            post = instaloader.Post.from_shortcode(L.context, shortcode)
            print(post)

            # Determine media type and download
            if post.is_video:
                L.download_post(post, target='temp')
                media_path = f"temp/{shortcode}.mp4"
                media_type = "video"
            else:
                L.download_post(post, target='temp')
                # Get the first image (for carousel posts)
                media_path = f"temp/{shortcode}.jpg"
                media_type = "image"
            
            # Generate S3 object name
            object_name = f"instagram/{path.split('/')[-1]}.{'mp4' if 'video' in media_type else 'jpg'}"
            
            # Upload to S3
            download_url = self.storage_service.upload_file(
                media_path, object_name
            )

            
            return DownloadResponse(
                status="success",
                download_url=download_url,
                media_type="video" if 'video' in media_type else "image"
            )
        except Exception as e:
            raise Exception(f"Failed to download Instagram media: {str(e)}")

    # def _fetch_media(self, url: str) -> tuple[bytes, str]:
    #     """Fetch media from Instagram (simplified example)"""
    #     # NOTE: In a real implementation, you would:
    #     # 1. Use Instagram API or a reliable library
    #     # 2. Handle authentication if needed
    #     # 3. Properly extract media URLs from the post
    #     # 4. Download the highest quality version
        
    #     # This is a placeholder implementation
    #     response = self.session.get(url)
    #     response.raise_for_status()
        
    #     # Determine if it's a video or image (simplified)
    #     is_video = '/reel/' in url or '/tv/' in url
    #     content_type = 'video/mp4' if is_video else 'image/jpeg'
        
    #     # Return dummy data - replace with actual media download
    #     dummy_data = b'dummy_data'  # Replace with actual media bytes
    #     return dummy_data, content_type